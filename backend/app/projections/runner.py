import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.event_store import EventStore
from app.models.event_store import SubscriptionModel


class ProjectionRunner:
    """Runs projections by subscribing to the event store."""

    def __init__(
        self,
        event_store: EventStore,
        projections: list[Any],
        subscription_id: str,
        session: AsyncSession,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self.event_store = event_store
        self.projections = projections
        self.subscription_id = subscription_id
        self.session = session
        self.poll_interval_seconds = poll_interval_seconds

    async def run(self) -> None:
        position = await self._get_checkpoint()

        while True:
            events = await self.event_store.get_all_events_since(
                position=position,
                limit=100,
            )

            if not events:
                await asyncio.sleep(self.poll_interval_seconds)
                continue

            for event in events:
                for projection in self.projections:
                    await projection.handle(event)
                position = event["global_position"]

            await self._save_checkpoint(position)

    async def _get_checkpoint(self) -> int:
        result = await self.session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.subscription_id == self.subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        if subscription is None:
            subscription = SubscriptionModel(subscription_id=self.subscription_id, last_position=0)
            self.session.add(subscription)
            await self.session.flush()
            return 0
        return int(subscription.last_position)

    async def _save_checkpoint(self, position: int) -> None:
        result = await self.session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.subscription_id == self.subscription_id
            )
        )
        subscription = result.scalar_one()
        subscription.last_position = position
        await self.session.flush()
