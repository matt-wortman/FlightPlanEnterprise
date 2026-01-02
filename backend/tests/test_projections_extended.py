import uuid
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.read_models import PatientReadModel, FlightPlanReadModel
from app.projections.read_model_projections import (
    PatientProjection,
    FlightPlanProjection,
    TimelineProjection,
)


@pytest.mark.asyncio
async def test_patient_projection_updates_existing():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    async with async_session() as session:
        session.add(
            PatientReadModel(
                id=patient_id,
                tenant_id=tenant_id,
                data={"patient_id": str(patient_id), "name": "Old"},
            )
        )
        await session.commit()

        projection = PatientProjection(session=session, tenant_id=tenant_id)
        event = {
            "event_type": "patient.created",
            "event_id": str(uuid.uuid4()),
            "data": {"patient_id": str(patient_id), "name": "New"},
        }
        await projection.handle(event)
        await session.commit()

        row = await session.get(PatientReadModel, patient_id)
        assert row.data["name"] == "New"

    await engine.dispose()


@pytest.mark.asyncio
async def test_flightplan_projection_inserts_and_updates():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tenant_id = uuid.uuid4()
    flightplan_id = uuid.uuid4()
    admission_id = uuid.uuid4()

    async with async_session() as session:
        projection = FlightPlanProjection(session=session, tenant_id=tenant_id)
        event = {
            "event_type": "flightplan.created",
            "event_id": str(uuid.uuid4()),
            "data": {"flightplan_id": str(flightplan_id), "admission_id": str(admission_id)},
        }
        await projection.handle(event)
        await session.commit()

        existing = await session.get(FlightPlanReadModel, flightplan_id)
        assert existing is not None

        event2 = {
            "event_type": "flightplan.created",
            "event_id": str(uuid.uuid4()),
            "data": {"flightplan_id": str(flightplan_id), "admission_id": str(admission_id), "status": "updated"},
        }
        await projection.handle(event2)
        await session.commit()

        updated = await session.get(FlightPlanReadModel, flightplan_id)
        assert updated.data.get("status") == "updated"

    await engine.dispose()


@pytest.mark.asyncio
async def test_timeline_projection_invalid_datetime_fallback():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tenant_id = uuid.uuid4()
    admission_id = uuid.uuid4()

    async with async_session() as session:
        projection = TimelineProjection(session=session, tenant_id=tenant_id)
        event = {
            "event_type": "clinical_event.recorded",
            "event_id": str(uuid.uuid4()),
            "data": {
                "event_id": str(uuid.uuid4()),
                "admission_id": str(admission_id),
                "event_type": "procedure",
                "occurred_at": "not-a-date",
            },
        }
        await projection.handle(event)
        await session.commit()

    await engine.dispose()
