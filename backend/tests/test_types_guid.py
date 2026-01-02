import uuid

from app.models.types import GUID


def test_guid_bind_and_result_roundtrip_sqlite():
    guid = GUID()
    value = uuid.uuid4()

    bound = guid.process_bind_param(value, type("D", (), {"name": "sqlite"})())
    assert isinstance(bound, str)

    result = guid.process_result_value(bound, type("D", (), {"name": "sqlite"})())
    assert isinstance(result, uuid.UUID)
    assert result == value


def test_guid_bind_param_none():
    guid = GUID()
    assert guid.process_bind_param(None, type("D", (), {"name": "sqlite"})()) is None
