import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models.base import Base


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_append_events_endpoint():
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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "stream_id": str(uuid.uuid4()),
            "stream_type": "Admission",
            "events": [
                {
                    "event_type": "admission.created",
                    "data": {"foo": "bar"},
                    "metadata": {},
                    "created_by": str(uuid.uuid4()),
                }
            ],
        }
        resp = await client.post("/api/v1/events", json=payload)

    app.dependency_overrides.clear()
    await engine.dispose()

    assert resp.status_code == 200
    assert resp.json()["new_version"] == 1
