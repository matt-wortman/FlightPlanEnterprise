from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import hmac
import hashlib
import os
from pathlib import Path
from typing import Any, Callable, Iterable
from uuid import UUID, uuid4, uuid5


LEGACY_NAMESPACE_UUID = UUID("9f8e4f24-6d1a-4c1a-b6b3-7b9e1c7b6a12")


@dataclass
class LegacyEvent:
    occurred_at: datetime
    stream_id: UUID
    stream_type: str
    event_type: str
    data: dict[str, Any]
    created_by: UUID
    metadata: dict[str, Any]


class LegacyIdMapper:
    def __init__(self, token_key: bytes, mapping_file: Path | None = None) -> None:
        self._token_key = token_key
        self._mapping_file = mapping_file
        self._dirty = False
        self._mapping: dict[str, dict[str, str]] = {
            "patients": {},
            "admissions": {},
            "users": {},
            "attachments": {},
        }
        if mapping_file and mapping_file.exists():
            self._mapping = _load_mapping(mapping_file)

    @classmethod
    def from_env(cls, mapping_file: str | None = None) -> "LegacyIdMapper":
        key = os.getenv("LEGACY_TOKEN_KEY")
        if not key:
            raise ValueError("LEGACY_TOKEN_KEY is required to tokenize legacy identifiers.")
        path = Path(mapping_file) if mapping_file else None
        return cls(token_key=key.encode("utf-8"), mapping_file=path)

    def save(self) -> None:
        if not self._mapping_file or not self._dirty:
            return
        _save_mapping(self._mapping_file, self._mapping)
        self._dirty = False

    def mrn_token(self, mrn: str) -> str:
        return self._tokenize("MRN", mrn)

    def patient_id_for_mrn(self, mrn: str) -> UUID:
        token = self._tokenize("MRN", mrn)
        return self._get_or_create_uuid("patients", token)

    def admission_id_for(self, mrn: str, adm: str) -> UUID:
        token = self._tokenize("ADM", f"{mrn}|{adm}")
        return self._get_or_create_uuid("admissions", token)

    def user_id_for_username(self, username: str, default_created_by: UUID) -> UUID:
        if not username:
            return default_created_by
        token = self._tokenize("USER", username)
        return self._get_or_create_uuid("users", token)

    def attachment_id_for(self, attachment_id: str) -> UUID:
        token = self._tokenize("ATTACHMENT", attachment_id)
        return self._get_or_create_uuid("attachments", token)

    def _get_or_create_uuid(self, bucket: str, token: str) -> UUID:
        if bucket in self._mapping and token in self._mapping[bucket]:
            return UUID(self._mapping[bucket][token])
        new_uuid = uuid5(LEGACY_NAMESPACE_UUID, f"{bucket}:{token}")
        if bucket in self._mapping:
            self._mapping[bucket][token] = str(new_uuid)
            self._dirty = True
        return new_uuid

    def _tokenize(self, namespace: str, value: str) -> str:
        payload = f"{namespace}:{value}".encode("utf-8")
        digest = hmac.new(self._token_key, payload, hashlib.sha256).hexdigest()
        return digest


def normalize_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def get_value(row: dict[str, Any], key: str) -> Any:
    if key in row:
        return row[key]
    lower = key.lower()
    upper = key.upper()
    if lower in row:
        return row[lower]
    if upper in row:
        return row[upper]
    return None


def build_patient_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    mrn = get_value(row, "MRN")
    if not mrn:
        return None
    patient_id = mapper.patient_id_for_mrn(str(mrn))
    created_by = mapper.user_id_for_username(str(get_value(row, "Username") or ""), default_created_by)
    dob = get_value(row, "DOB")
    dob_value = normalize_datetime(dob).date().isoformat() if dob else None
    first = (get_value(row, "FirstName") or "").strip()
    last = (get_value(row, "LastName") or "").strip()
    name = " ".join(part for part in [first, last] if part).strip() or "Unknown"

    data = {
        "patient_id": str(patient_id),
        "name": name,
        "mrn": mapper.mrn_token(str(mrn)),
        "date_of_birth": dob_value,
        "gender": get_value(row, "sex"),
        "legacy_fields": {
            "key_diagnosis": get_value(row, "KeyDiagnosis"),
            "deceased": get_value(row, "Deceased"),
            "activity_date": _iso_or_none(get_value(row, "ActivityDate")),
            "legacy_username": get_value(row, "Username"),
        },
    }

    occurred_at = normalize_datetime(get_value(row, "ActivityDate"))
    return LegacyEvent(
        occurred_at=occurred_at,
        stream_id=patient_id,
        stream_type="Patient",
        event_type="patient.created",
        data=data,
        created_by=created_by,
        metadata={"source": "legacy_v2", "table": "patients"},
    )


def build_admission_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
    specialty: str,
) -> LegacyEvent | None:
    mrn = get_value(row, "MRN")
    adm = get_value(row, "ADM")
    if not mrn or not adm:
        return None
    patient_id = mapper.patient_id_for_mrn(str(mrn))
    admission_id = mapper.admission_id_for(str(mrn), str(adm))
    created_by = mapper.user_id_for_username(str(get_value(row, "Username") or ""), default_created_by)
    admit_date = normalize_datetime(get_value(row, "ADMDATE"))

    data = {
        "admission_id": str(admission_id),
        "patient_id": str(patient_id),
        "specialty": specialty,
        "attending_id": str(created_by),
        "admit_date": admit_date.isoformat(),
        "chief_complaint": get_value(row, "Diagnosis"),
        "admission_type": get_value(row, "Status"),
        "legacy_fields": {
            "interventions": get_value(row, "Interventions"),
            "review_date": _iso_or_none(get_value(row, "ReviewDate")),
            "cross_check": get_value(row, "CrossCheck"),
            "thumbnail": get_value(row, "Thumbnail"),
            "activity_date": _iso_or_none(get_value(row, "ActivityDate")),
            "legacy_username": get_value(row, "Username"),
            "legacy_admission_number": str(adm),
        },
    }

    return LegacyEvent(
        occurred_at=admit_date,
        stream_id=admission_id,
        stream_type="Admission",
        event_type="admission.created",
        data=data,
        created_by=created_by,
        metadata={"source": "legacy_v2", "table": "admissions"},
    )


def build_location_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    mrn = get_value(row, "MRN")
    adm = get_value(row, "ADM")
    if not mrn or not adm:
        return None
    admission_id = mapper.admission_id_for(str(mrn), str(adm))
    created_by = mapper.user_id_for_username(str(get_value(row, "Username") or ""), default_created_by)
    effective_at = normalize_datetime(get_value(row, "EntryDatetime"))

    data = {
        "admission_id": str(admission_id),
        "from_location": None,
        "to_location": get_value(row, "Location"),
        "from_bed": None,
        "to_bed": None,
        "effective_at": effective_at.isoformat(),
        "reason": get_value(row, "Notes"),
        "legacy_fields": {
            "legacy_location_step_id": get_value(row, "LocationStepID"),
            "teams": get_value(row, "Teams"),
            "weight": get_value(row, "Weight"),
            "extra": get_value(row, "Extra"),
            "activity_date": _iso_or_none(get_value(row, "ActivityDate")),
            "legacy_username": get_value(row, "Username"),
        },
    }

    return LegacyEvent(
        occurred_at=effective_at,
        stream_id=admission_id,
        stream_type="Admission",
        event_type="admission.location_changed",
        data=data,
        created_by=created_by,
        metadata={"source": "legacy_v2", "table": "location_steps"},
    )


def build_risk_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="risk_status",
        timestamp_key="StartDatetime",
        table="location_risks",
        extra_fields={
            "risk": get_value(row, "Risk"),
            "notes": get_value(row, "Notes"),
            "extra": get_value(row, "Extra"),
            "legacy_location_step_id": get_value(row, "LocationStepID"),
            "legacy_location_risk_id": get_value(row, "LocationRiskID"),
        },
    )


def build_annotation_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="annotation",
        timestamp_key="EntryDatetime",
        table="annotations",
        extra_fields={
            "annotation": get_value(row, "annotation"),
            "annotation_type": get_value(row, "type"),
            "href": get_value(row, "href"),
            "special_node": get_value(row, "SpecialNode"),
            "format": get_value(row, "format"),
            "legacy_annotation_id": get_value(row, "AnnotaionID"),
        },
    )


def build_feedback_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="feedback",
        timestamp_key="EntryDatetime",
        table="feedbacks",
        extra_fields={
            "exit_datetime": _iso_or_none(get_value(row, "ExitDatetime")),
            "score": get_value(row, "Score"),
            "performance": get_value(row, "Performance"),
            "outcome": get_value(row, "Outcome"),
            "attachment_keys": get_value(row, "AttachmentKeys"),
            "notes": get_value(row, "Notes"),
            "graph_visible": get_value(row, "GraphVisible"),
            "suggested_edit": get_value(row, "SuggestedEdit"),
            "legacy_feedback_id": get_value(row, "FeedbackID"),
        },
    )


def build_conference_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="conference",
        timestamp_key="EntryDatetime",
        table="conferences",
        extra_fields={
            "conference_type": get_value(row, "Type"),
            "attachment_keys": get_value(row, "AttachmentKeys"),
            "action_items": get_value(row, "ActionItems"),
            "notes": get_value(row, "Notes"),
            "legacy_conference_id": get_value(row, "ConferenceID"),
        },
    )


def build_bedside_procedure_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="bedside_procedure",
        timestamp_key="StartDatetime",
        table="bedside_procedures",
        extra_fields={
            "end_datetime": _iso_or_none(get_value(row, "EndDatetime")),
            "procedure_type": get_value(row, "ProcedureType"),
            "teams": get_value(row, "Teams"),
            "notes": get_value(row, "Notes"),
            "legacy_bedside_procedure_id": get_value(row, "BedsideProcedureID"),
            "legacy_location_step_id": get_value(row, "LocationStepID"),
        },
    )


def build_continuous_therapy_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="continuous_therapy",
        timestamp_key="EntryDatetime",
        table="continuous_therapy",
        extra_fields={
            "therapy_type": get_value(row, "Type"),
            "status": get_value(row, "Status"),
            "attachment_keys": get_value(row, "AttachmentKeys"),
            "notes": get_value(row, "Notes"),
            "legacy_continuous_therapy_id": get_value(row, "CtId"),
        },
    )


def build_course_correction_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    return _build_clinical_event(
        row=row,
        mapper=mapper,
        default_created_by=default_created_by,
        event_kind="course_correction",
        timestamp_key="EntryDatetime",
        table="course_corrections",
        extra_fields={
            "correction_type": get_value(row, "type"),
            "detail": get_value(row, "detail"),
            "legacy_course_correction_id": get_value(row, "course_correct_id"),
        },
    )


def build_attachment_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> LegacyEvent | None:
    mrn = get_value(row, "MRN")
    adm = get_value(row, "ADM")
    if not mrn or not adm:
        return None
    admission_id = mapper.admission_id_for(str(mrn), str(adm))
    created_by = mapper.user_id_for_username(str(get_value(row, "Username") or ""), default_created_by)
    occurred_at = normalize_datetime(get_value(row, "EntryDatetime"))
    attachment_id = mapper.attachment_id_for(str(get_value(row, "AttachmentID") or uuid4()))

    data = {
        "attachment_id": str(attachment_id),
        "admission_id": str(admission_id),
        "occurred_at": occurred_at.isoformat(),
        "storage_key": get_value(row, "storage_key"),
        "filename": get_value(row, "Filename"),
        "description": get_value(row, "Description"),
        "attachment_type": get_value(row, "AttachmentType"),
        "content_type": get_value(row, "ContentType"),
        "thumbnail_key": get_value(row, "Thumbnail"),
        "linked_event_id": None,
        "legacy_fields": {
            "legacy_location_step_id": get_value(row, "LocationStepID"),
            "legacy_location_risk_id": get_value(row, "LocationRiskID"),
            "activity_date": _iso_or_none(get_value(row, "ActivityDate")),
            "legacy_username": get_value(row, "Username"),
        },
    }

    return LegacyEvent(
        occurred_at=occurred_at,
        stream_id=admission_id,
        stream_type="Admission",
        event_type="attachment.added",
        data=data,
        created_by=created_by,
        metadata={"source": "legacy_v2", "table": "attachments"},
    )


def _build_clinical_event(
    row: dict[str, Any],
    mapper: LegacyIdMapper,
    default_created_by: UUID,
    event_kind: str,
    timestamp_key: str,
    table: str,
    extra_fields: dict[str, Any],
) -> LegacyEvent | None:
    mrn = get_value(row, "MRN")
    adm = get_value(row, "ADM")
    if not mrn or not adm:
        return None
    admission_id = mapper.admission_id_for(str(mrn), str(adm))
    created_by = mapper.user_id_for_username(str(get_value(row, "Username") or ""), default_created_by)
    occurred_at = normalize_datetime(get_value(row, timestamp_key))

    data = {
        "event_id": str(uuid4()),
        "admission_id": str(admission_id),
        "event_type": event_kind,
        "occurred_at": occurred_at.isoformat(),
        **extra_fields,
        "legacy_fields": {
            "activity_date": _iso_or_none(get_value(row, "ActivityDate")),
            "legacy_username": get_value(row, "Username"),
        },
    }

    return LegacyEvent(
        occurred_at=occurred_at,
        stream_id=admission_id,
        stream_type="Admission",
        event_type="clinical_event.recorded",
        data=data,
        created_by=created_by,
        metadata={"source": "legacy_v2", "table": table},
    )


def _iso_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return normalize_datetime(value).isoformat()


def _load_mapping(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {"patients": {}, "admissions": {}, "users": {}, "attachments": {}}
    return _safe_json_load(path)


def _save_mapping(path: Path, mapping: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe_json_dump(path, mapping)


def _safe_json_load(path: Path) -> dict[str, dict[str, str]]:
    import json

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_json_dump(path: Path, payload: dict[str, dict[str, str]]) -> None:
    import json

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


TableBuilder = Callable[[dict[str, Any], LegacyIdMapper, UUID], LegacyEvent | None]


def iter_table_events(
    rows: Iterable[dict[str, Any]],
    builder: TableBuilder,
    mapper: LegacyIdMapper,
    default_created_by: UUID,
) -> Iterable[LegacyEvent]:
    for row in rows:
        event = builder(row, mapper, default_created_by)
        if event:
            yield event
