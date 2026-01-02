import os
import uuid
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.infrastructure.event_store import EventStore, EventToAppend, ConcurrencyError


@pytest.mark.asyncio
async def test_append_and_load_stream():
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()
    stream_id = uuid.uuid4()

    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        new_version = await store.append(
            stream_id=stream_id,
            stream_type="Admission",
            events=[
                EventToAppend(
                    event_type="admission.created",
                    data={"foo": "bar"},
                    metadata={},
                    created_by=uuid.uuid4(),
                ),
                EventToAppend(
                    event_type="admission.updated",
                    data={"baz": "qux"},
                    metadata={},
                    created_by=uuid.uuid4(),
                ),
            ],
        )
        await session.commit()
        assert new_version == 2

        events = await store.load_stream(stream_id)
        assert [e["event_version"] for e in events] == [1, 2]
        assert events[0]["event_type"] == "admission.created"

    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrency_check():
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
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
                )
            ],
        )
        await session.commit()

        with pytest.raises(ConcurrencyError):
            await store.append(
                stream_id=stream_id,
                stream_type="Admission",
                events=[
                    EventToAppend(
                        event_type="admission.updated",
                        data={},
                        metadata={},
                        created_by=uuid.uuid4(),
                    )
                ],
                expected_version=0,
            )

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_all_events_since():
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()

    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        stream_id = uuid.uuid4()
        await store.append(
            stream_id=stream_id,
            stream_type="Admission",
            events=[
                EventToAppend(
                    event_type="admission.created",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                )
            ],
        )
        await session.commit()

        events = await store.get_all_events_since(position=0)
        assert len(events) == 1
        assert events[0]["stream_id"] == str(stream_id)

    await engine.dispose()


def _test_database_url() -> str:
    return os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


def _create_test_engine():
    url = _test_database_url()
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_async_engine(url, future=True)
