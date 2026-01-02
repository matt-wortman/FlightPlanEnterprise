from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.tenant import get_tenant_id
from app.infrastructure.event_store import EventStore, EventToAppend

router = APIRouter(prefix="/api/v1", tags=["events"])


class EventInput(BaseModel):
    event_type: str
    data: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: UUID


class EventAppendRequest(BaseModel):
    stream_id: UUID
    stream_type: str
    events: list[EventInput]
    expected_version: Optional[int] = None


class EventAppendResponse(BaseModel):
    new_version: int


@router.post("/events", response_model=EventAppendResponse)
async def append_events(
    payload: EventAppendRequest,
    session: AsyncSession = Depends(get_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EventAppendResponse:
    event_store = EventStore(session=session, tenant_id=tenant_id)
    events = [
        EventToAppend(
            event_type=e.event_type,
            data=e.data,
            metadata=e.metadata,
            created_by=e.created_by,
        )
        for e in payload.events
    ]

    new_version = await event_store.append(
        stream_id=payload.stream_id,
        stream_type=payload.stream_type,
        events=events,
        expected_version=payload.expected_version,
    )

    await session.commit()
    return EventAppendResponse(new_version=new_version)
