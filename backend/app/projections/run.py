import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.infrastructure.event_store import EventStore
from app.projections.read_model_projections import (
    PatientProjection,
    AdmissionProjection,
    FlightPlanProjection,
    TimelineProjection,
    AttachmentProjection,
)
from app.projections.runner import ProjectionRunner


async def main() -> None:
    settings = get_settings()
    tenant_id = UUID(settings.default_tenant_id)

    async with async_session_factory() as session:
        event_store = EventStore(session=session, tenant_id=tenant_id)
        projections = [
            PatientProjection(session, tenant_id),
            AdmissionProjection(session, tenant_id),
            FlightPlanProjection(session, tenant_id),
            TimelineProjection(session, tenant_id),
            AttachmentProjection(session, tenant_id),
        ]
        runner = ProjectionRunner(
            event_store=event_store,
            projections=projections,
            subscription_id="read-models",
            session=session,
        )
        await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
