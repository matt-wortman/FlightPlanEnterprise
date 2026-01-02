import uuid
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.infrastructure.event_store import EventStore, EventToAppend


@pytest.mark.asyncio
async def test_load_stream_with_version_range_and_snapshot():
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
    stream_id = uuid.uuid4()

    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        await store.append(
            stream_id=stream_id,
            stream_type="Admission",
            events=[
                EventToAppend(
                    event_type="admission.created",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                ),
                EventToAppend(
                    event_type="admission.updated",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                ),
            ],
        )
        await session.commit()

        subset = await store.load_stream(stream_id, from_version=0, to_version=1)
        assert len(subset) == 1

        await store.save_snapshot(stream_id, "Admission", version=2, state={"ok": True})
        await session.commit()
        snapshot = await store.load_snapshot(stream_id)
        assert snapshot is not None
        assert snapshot[0] == 2

    await engine.dispose()


@pytest.mark.asyncio
async def test_load_by_type_filters():
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
    stream_id = uuid.uuid4()

    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        await store.append(
            stream_id=stream_id,
            stream_type="Admission",
            events=[
                EventToAppend(
                    event_type="admission.created",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                ),
                EventToAppend(
                    event_type="admission.location_changed",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                ),
            ],
        )
        await session.commit()

        created_events = await store.load_by_type("admission.created")
        assert len(created_events) == 1

    await engine.dispose()
