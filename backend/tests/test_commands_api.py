import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.base import Base


@pytest.mark.asyncio
async def test_command_endpoints_append_events():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    admission_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admissions",
            headers={"X-Tenant-ID": str(tenant_id)},
            json={
                "admission_id": str(admission_id),
                "patient_id": str(patient_id),
                "specialty": "cardiac",
                "attending_id": str(uuid.uuid4()),
                "admit_date": "2026-01-02T00:00:00",
                "chief_complaint": "test",
                "admission_type": "Elective",
                "created_by": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["new_version"] == 1

        resp = await client.post(
            f"/api/v1/admissions/{admission_id}/location",
            headers={"X-Tenant-ID": str(tenant_id)},
            json={
                "from_location": None,
                "to_location": "ICU",
                "from_bed": None,
                "to_bed": "12A",
                "effective_at": "2026-01-02T01:00:00",
                "reason": "post-op",
                "created_by": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["new_version"] == 2

        resp = await client.post(
            "/api/v1/clinical-events",
            headers={"X-Tenant-ID": str(tenant_id)},
            json={
                "event_id": str(uuid.uuid4()),
                "admission_id": str(admission_id),
                "event_type": "procedure",
                "occurred_at": "2026-01-02T02:00:00",
                "data": {"procedure": "CABG"},
                "created_by": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["new_version"] == 3

    app.dependency_overrides.clear()
    await engine.dispose()
