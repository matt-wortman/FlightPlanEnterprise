from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_store import EventModel, SnapshotModel


@dataclass
class EventToAppend:
    event_type: str
    data: dict[str, Any]
    metadata: dict[str, Any]
    created_by: UUID


class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails."""


class EventStore:
    """Append-only event store with optimistic concurrency control."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def append(
        self,
        stream_id: UUID,
        stream_type: str,
        events: list[EventToAppend],
        expected_version: Optional[int] = None,
    ) -> int:
        current_version = await self._get_current_version(stream_id)

        if expected_version is not None and current_version != expected_version:
            raise ConcurrencyError(
                f"Expected version {expected_version}, but found {current_version}"
            )

        new_version = current_version
        next_global_position = await self._get_next_global_position()
        for event in events:
            new_version += 1
            event_model = EventModel(
                stream_id=stream_id,
                stream_type=stream_type,
                event_type=event.event_type,
                event_version=new_version,
                tenant_id=self.tenant_id,
                data=event.data,
                metadata_=event.metadata or {},
                created_by=event.created_by,
                global_position=next_global_position,
            )
            self.session.add(event_model)
            next_global_position += 1

        await self.session.flush()
        return new_version

    async def load_stream(
        self,
        stream_id: UUID,
        from_version: int = 0,
        to_version: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        query = select(EventModel).where(
            and_(
                EventModel.stream_id == stream_id,
                EventModel.tenant_id == self.tenant_id,
                EventModel.event_version > from_version,
            )
        ).order_by(EventModel.event_version)

        if to_version is not None:
            query = query.where(EventModel.event_version <= to_version)

        result = await self.session.execute(query)
        event_models = result.scalars().all()
        return [self._to_dict(em) for em in event_models]

    async def load_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        query = select(EventModel).where(
            and_(
                EventModel.event_type == event_type,
                EventModel.tenant_id == self.tenant_id,
            )
        ).order_by(EventModel.global_position).limit(limit)

        if since:
            query = query.where(EventModel.created_at > since)

        result = await self.session.execute(query)
        return [self._to_dict(em) for em in result.scalars().all()]

    async def get_all_events_since(
        self,
        position: int,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        query = select(EventModel).where(
            and_(
                EventModel.global_position > position,
                EventModel.tenant_id == self.tenant_id,
            )
        ).order_by(EventModel.global_position).limit(limit)

        result = await self.session.execute(query)
        return [self._to_dict(em) for em in result.scalars().all()]

    async def save_snapshot(
        self,
        stream_id: UUID,
        stream_type: str,
        version: int,
        state: dict[str, Any],
    ) -> None:
        snapshot = SnapshotModel(
            stream_id=stream_id,
            stream_type=stream_type,
            version=version,
            state=state,
        )
        self.session.add(snapshot)
        await self.session.flush()

    async def load_snapshot(self, stream_id: UUID) -> Optional[tuple[int, dict[str, Any]]]:
        query = (
            select(SnapshotModel)
            .where(SnapshotModel.stream_id == stream_id)
            .order_by(SnapshotModel.version.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        snapshot = result.scalar_one_or_none()
        if snapshot:
            return (snapshot.version, snapshot.state)
        return None

    async def _get_current_version(self, stream_id: UUID) -> int:
        query = select(func.max(EventModel.event_version)).where(
            and_(
                EventModel.stream_id == stream_id,
                EventModel.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(query)
        version = result.scalar_one_or_none()
        return int(version or 0)

    async def _get_next_global_position(self) -> int:
        query = select(func.max(EventModel.global_position))
        result = await self.session.execute(query)
        current = result.scalar_one_or_none()
        return int(current or 0) + 1

    def _to_dict(self, model: EventModel) -> dict[str, Any]:
        return {
            "event_id": str(model.event_id),
            "stream_id": str(model.stream_id),
            "stream_type": model.stream_type,
            "event_type": model.event_type,
            "event_version": model.event_version,
            "tenant_id": str(model.tenant_id),
            "data": model.data,
            "metadata": model.metadata_,
            "created_at": model.created_at.isoformat(),
            "created_by": str(model.created_by),
            "global_position": model.global_position,
        }
