import uuid
import pytest

from app.projections import run as run_module


class DummySession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_run_main_invokes_runner(monkeypatch):
    called = {"run": False}

    class DummyEventStore:
        def __init__(self, session, tenant_id):
            self.session = session
            self.tenant_id = tenant_id

    class DummyRunner:
        def __init__(self, event_store, projections, subscription_id, session, poll_interval_seconds=1.0):
            self.event_store = event_store
            self.projections = projections
            self.subscription_id = subscription_id
            self.session = session

        async def run(self):
            called["run"] = True

    async def dummy_session_factory():
        return DummySession()

    class DummySessionFactory:
        def __call__(self):
            return DummySession()

    class DummySettings:
        default_tenant_id = str(uuid.uuid4())

    monkeypatch.setattr(run_module, "EventStore", DummyEventStore)
    monkeypatch.setattr(run_module, "ProjectionRunner", DummyRunner)
    monkeypatch.setattr(run_module, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(run_module, "async_session_factory", DummySessionFactory())

    await run_module.main()
    assert called["run"] is True
