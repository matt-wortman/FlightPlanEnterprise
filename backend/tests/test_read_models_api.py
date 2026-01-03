from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.base import Base
from app.models.read_models import PatientReadModel, AdmissionReadModel, AttachmentReadModel


@pytest.mark.asyncio
async def test_read_model_endpoints():
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
    admission_id = uuid.uuid4()

    async with async_session() as session:
        session.add(
            PatientReadModel(
                id=patient_id,
                tenant_id=tenant_id,
                data={"patient_id": str(patient_id), "name": "Test"},
            )
        )
        session.add(
            AdmissionReadModel(
                id=admission_id,
                tenant_id=tenant_id,
                patient_id=patient_id,
                data={"admission_id": str(admission_id), "patient_id": str(patient_id)},
            )
        )
        session.add(
            AttachmentReadModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                admission_id=admission_id,
                occurred_at=datetime.now(timezone.utc),
                data={"admission_id": str(admission_id), "filename": "note.pdf"},
            )
        )
        await session.commit()

    async def _override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/patients", headers={"X-Tenant-ID": str(tenant_id)})
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

        resp = await client.get(
            "/api/v1/patients",
            headers={"X-Tenant-ID": str(tenant_id)},
            params={"limit": 1, "offset": 10},
        )
        assert resp.status_code == 200
        assert resp.json()["items"] == []

        resp = await client.get(f"/api/v1/patients/{patient_id}", headers={"X-Tenant-ID": str(tenant_id)})
        assert resp.status_code == 200

        resp = await client.get(
            f"/api/v1/patients/{uuid.uuid4()}",
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 200
        assert resp.json()["detail"] == "not found"

        resp = await client.get(
            "/api/v1/admissions",
            headers={"X-Tenant-ID": str(tenant_id)},
            params={"patient_id": str(patient_id)},
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

        # Missing tenant header should fall back to default and return no rows
        resp = await client.get("/api/v1/admissions", params={"patient_id": str(patient_id)})
        assert resp.status_code == 200

        resp = await client.get(
            f"/api/v1/admissions/{admission_id}/timeline",
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 200

        resp = await client.get(
            f"/api/v1/admissions/{admission_id}/trajectory",
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 200

        resp = await client.get(
            f"/api/v1/admissions/{admission_id}/attachments",
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    app.dependency_overrides.clear()
    await engine.dispose()
