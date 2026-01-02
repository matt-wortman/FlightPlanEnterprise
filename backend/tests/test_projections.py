import uuid
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.read_models import PatientReadModel, AdmissionReadModel, TimelineEventModel
from app.projections.read_model_projections import PatientProjection, AdmissionProjection, TimelineProjection


@pytest.mark.asyncio
async def test_patient_projection_creates_read_model():
    engine = _create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    async with async_session() as session:
        projection = PatientProjection(session=session, tenant_id=tenant_id)
        event = {
            "event_type": "patient.created",
            "event_id": str(uuid.uuid4()),
            "data": {"patient_id": str(patient_id), "name": "Test"},
        }
        await projection.handle(event)
        await session.commit()

        row = await session.get(PatientReadModel, patient_id)
        assert row is not None
        assert row.data["name"] == "Test"

    await engine.dispose()


@pytest.mark.asyncio
async def test_admission_projection_location_creates_trajectory_point():
    engine = _create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()
    admission_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    async with async_session() as session:
        projection = AdmissionProjection(session=session, tenant_id=tenant_id)

        create_event = {
            "event_type": "admission.created",
            "event_id": str(uuid.uuid4()),
            "data": {
                "admission_id": str(admission_id),
                "patient_id": str(patient_id),
            },
        }
        await projection.handle(create_event)

        location_event = {
            "event_type": "admission.location_changed",
            "event_id": str(uuid.uuid4()),
            "data": {
                "admission_id": str(admission_id),
                "to_location": "ICU",
                "effective_at": "2026-01-02T00:00:00",
            },
        }
        await projection.handle(location_event)
        await session.commit()

        admission = await session.get(AdmissionReadModel, admission_id)
        assert admission is not None

    await engine.dispose()


@pytest.mark.asyncio
async def test_timeline_projection_inserts_event():
    engine = _create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
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
                "occurred_at": "2026-01-02T00:00:00",
            },
        }
        await projection.handle(event)
        await session.commit()

        rows = (await session.execute(TimelineEventModel.__table__.select())).fetchall()
        assert len(rows) == 1

    await engine.dispose()


def _create_engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
