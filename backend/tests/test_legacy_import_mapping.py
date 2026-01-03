from datetime import datetime, timezone
from uuid import UUID

from app.legacy_import.mapping import (
    LegacyIdMapper,
    build_admission_event,
    build_attachment_event,
    build_patient_event,
    build_risk_event,
)


def test_legacy_id_mapper_is_deterministic() -> None:
    mapper = LegacyIdMapper(token_key=b"test-key")
    first = mapper.patient_id_for_mrn("MRN123")
    second = mapper.patient_id_for_mrn("MRN123")
    other = mapper.patient_id_for_mrn("MRN999")

    assert first == second
    assert first != other


def test_patient_event_tokenizes_mrn() -> None:
    mapper = LegacyIdMapper(token_key=b"test-key")
    default_created_by = UUID("00000000-0000-0000-0000-000000000001")
    row = {
        "MRN": "MRN123",
        "FirstName": "Ada",
        "LastName": "Lovelace",
        "DOB": datetime(1990, 1, 1),
        "sex": "female",
        "Username": "legacy_user",
        "ActivityDate": datetime(2020, 1, 1, tzinfo=timezone.utc),
    }
    event = build_patient_event(row, mapper, default_created_by)

    assert event is not None
    assert event.event_type == "patient.created"
    assert event.data["mrn"] != "MRN123"


def test_admission_event_shapes() -> None:
    mapper = LegacyIdMapper(token_key=b"test-key")
    default_created_by = UUID("00000000-0000-0000-0000-000000000001")
    row = {
        "MRN": "MRN123",
        "ADM": "ADM1",
        "ADMDATE": datetime(2021, 1, 1, tzinfo=timezone.utc),
        "Username": "",
        "Diagnosis": "Test",
    }
    event = build_admission_event(row, mapper, default_created_by, specialty="cardiac")

    assert event is not None
    assert event.event_type == "admission.created"
    assert event.stream_type == "Admission"
    assert event.data["specialty"] == "cardiac"


def test_risk_event_maps_to_clinical_event() -> None:
    mapper = LegacyIdMapper(token_key=b"test-key")
    default_created_by = UUID("00000000-0000-0000-0000-000000000001")
    row = {
        "MRN": "MRN123",
        "ADM": "ADM1",
        "StartDatetime": datetime(2022, 1, 1, tzinfo=timezone.utc),
        "Risk": "high",
    }
    event = build_risk_event(row, mapper, default_created_by)

    assert event is not None
    assert event.event_type == "clinical_event.recorded"
    assert event.data["event_type"] == "risk_status"


def test_attachment_event_contract() -> None:
    mapper = LegacyIdMapper(token_key=b"test-key")
    default_created_by = UUID("00000000-0000-0000-0000-000000000001")
    row = {
        "MRN": "MRN123",
        "ADM": "ADM1",
        "AttachmentID": "ATT1",
        "EntryDatetime": datetime(2023, 1, 1, tzinfo=timezone.utc),
        "storage_key": "files/att1.pdf",
        "Filename": "att1.pdf",
    }
    event = build_attachment_event(row, mapper, default_created_by)

    assert event is not None
    assert event.event_type == "attachment.added"
    assert event.data["storage_key"] == "files/att1.pdf"
