import asyncio
import uuid
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.event_store import EventStore, EventToAppend
from app.projections.runner import ProjectionRunner
from app.models.base import Base


class RecordingProjection:
    def __init__(self):
        self.handled = []

    async def handle(self, event):
        self.handled.append(event["event_type"])


@pytest.mark.asyncio
async def test_projection_runner_updates_checkpoint():
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
    projection = RecordingProjection()

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

        runner = ProjectionRunner(
            event_store=store,
            projections=[projection],
            subscription_id="test-sub",
            session=session,
            poll_interval_seconds=0.01,
        )

        async def run_once():
            task = asyncio.create_task(runner.run())
            await asyncio.sleep(0.05)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        await run_once()

        assert "admission.created" in projection.handled
        assert "admission.location_changed" in projection.handled

    await engine.dispose()
