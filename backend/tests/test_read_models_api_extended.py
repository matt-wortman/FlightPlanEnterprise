import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.base import Base
from app.models.read_models import FlightPlanReadModel


@pytest.mark.asyncio
async def test_flightplan_not_found_and_ok():
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
        session.add(
            FlightPlanReadModel(
                id=flightplan_id,
                tenant_id=tenant_id,
                admission_id=admission_id,
                data={"flightplan_id": str(flightplan_id)},
            )
        )
        await session.commit()

    async def _override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/flightplans/{uuid.uuid4()}",
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 200
        assert resp.json()["detail"] == "not found"

        resp = await client.get(
            f"/api/v1/flightplans/{flightplan_id}",
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 200
        assert resp.json()["flightplan_id"] == str(flightplan_id)

    app.dependency_overrides.clear()
    await engine.dispose()
