# Legacy v2 to Enterprise Mapping (Draft)

**Last Updated:** January 2, 2026  
**Source:** `docs/legacy_schema_snapshot.json` (SQL Server)

This document maps the **legacy v2 database tables** to the **enterprise event contracts and read models**. The goal is to preserve every clinically meaningful data point while moving to an event-sourced, multi-tenant architecture.

---

## Goals

- Preserve all legacy data points in the enterprise model.
- Keep the **core** data model stable across specialties.
- Isolate **cardiac-specific** details in the cardiac plugin.
- Enable ML and federated learning by standardizing events and timestamps.

---

## Identifier Strategy (Critical)

Legacy identifiers must be mapped without exposing PHI:

- **MRN (legacy)** → `patient_id` (UUID) + **encrypted MRN** stored in event payload
- **ADM (legacy)** → `admission_id` (UUID)
- **Legacy row IDs** (e.g., `LocationStepID`) should be preserved as `legacy_*_id` inside event `data` for traceability.
- **Username** (legacy) → `created_by` (UUID). If identity mapping is not ready, store `legacy_username` in event data and backfill later.

---

## High-Level Table Mapping

| Legacy Table | Purpose | Target Event(s) | Target Read Model(s) | Core vs Plugin |
|---|---|---|---|---|
| `patients` | Patient demographics | `patient.created` | `patient_read_models` | Core |
| `admissions` | Admission header | `admission.created` | `admission_read_models` | Core |
| `location_steps` | Location timeline | `admission.location_changed` | `trajectory_points` | Core |
| `location_risks` | Risk status over time | `clinical_event.recorded` (`risk_status`) | `timeline_events` | Plugin (cardiac first) |
| `annotations` | Free-text notes | `clinical_event.recorded` (`annotation`) | `timeline_events` | Plugin |
| `feedbacks` | Performance/outcome notes | `clinical_event.recorded` (`feedback`) | `timeline_events` | Plugin |
| `conferences` | Conference notes | `clinical_event.recorded` (`conference`) | `timeline_events` | Plugin |
| `bedside_procedures` | Procedures | `clinical_event.recorded` (`bedside_procedure`) | `timeline_events` | Plugin |
| `continuous_therapy` | Therapy episodes | `clinical_event.recorded` (`continuous_therapy`) | `timeline_events` | Plugin |
| `course_corrections` | Plan changes | `clinical_event.recorded` (`course_correction`) | `timeline_events` | Plugin |
| `attachments` | Files/images | **New event needed**: `attachment.added` | `timeline_events` (metadata) | Core (shared) |
| `users` | Clinician directory | Identity mapping only | None (external IdP) | Core (external) |

---

## Detailed Mapping

### 1) `patients`

Legacy columns:
`MRN`, `LastName`, `FirstName`, `DOB`, `sex`, `KeyDiagnosis`, `Deceased`, `Username`, `ActivityDate`

Target event: `patient.created`

Suggested mapping:
- `patient_id`: new UUID
- `name`: `FirstName + LastName`
- `mrn`: **encrypted MRN**
- `date_of_birth`: `DOB`
- `gender`: `sex`
- `legacy_fields` (optional): `KeyDiagnosis`, `Deceased`, `ActivityDate`, `Username`

Notes:
- The enterprise model should keep **MRN encrypted** and never expose it in URLs.
- Consider a separate `patient.updated` event if legacy has multiple changes over time.

---

### 2) `admissions`

Legacy columns:
`MRN`, `ADM`, `ADMDATE`, `Status`, `Interventions`, `Diagnosis`, `ReviewDate`, `CrossCheck`, `Thumbnail`, `Username`, `ActivityDate`

Target event: `admission.created`

Suggested mapping:
- `admission_id`: new UUID
- `patient_id`: from MRN mapping
- `specialty`: `"cardiac"` for current legacy scope
- `attending_id`: from user mapping (if available)
- `admit_date`: `ADMDATE`
- `chief_complaint`: `Diagnosis` (until a better field exists)
- `admission_type`: derived from legacy if available
- `legacy_fields`: `Status`, `Interventions`, `ReviewDate`, `CrossCheck`, `Thumbnail`, `ActivityDate`, `Username`, `ADM`

---

### 3) `location_steps`

Legacy columns:
`MRN`, `ADM`, `LocationStepID`, `EntryDatetime`, `Location`, `Teams`, `Weight`, `Notes`, `Extra`, `Username`, `ActivityDate`

Target event: `admission.location_changed`

Suggested mapping:
- `admission_id`: from ADM mapping
- `to_location`: `Location`
- `effective_at`: `EntryDatetime`
- `reason`: `Notes` (if meaningful)
- `legacy_fields`: `LocationStepID`, `Teams`, `Weight`, `Extra`, `ActivityDate`, `Username`

Resulting read model:
- `trajectory_points` (location over time)

---

### 4) `location_risks`

Legacy columns:
`MRN`, `ADM`, `LocationStepID`, `LocationRiskID`, `StartDatetime`, `Risk`, `Notes`, `Extra`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "risk_status"`

Suggested mapping:
- `admission_id`: from ADM mapping
- `occurred_at`: `StartDatetime`
- `event_type`: `"risk_status"`
- `details`: `Risk`, `Notes`, `Extra`, `LocationStepID`, `LocationRiskID`
- `legacy_fields`: `ActivityDate`, `Username`

Notes:
- Risk categories are **specialty-specific**. Keep the event type generic, but define allowed values in the cardiac plugin first.

---

### 5) `annotations`

Legacy columns:
`MRN`, `ADM`, `AnnotaionID`, `EntryDatetime`, `annotation`, `type`, `href`, `SpecialNode`, `format`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "annotation"`

Suggested mapping:
- `occurred_at`: `EntryDatetime`
- `details`: `annotation`, `type`, `href`, `SpecialNode`, `format`, `AnnotaionID`
- `legacy_fields`: `ActivityDate`, `Username`

---

### 6) `feedbacks`

Legacy columns:
`MRN`, `ADM`, `FeedbackID`, `EntryDatetime`, `ExitDatetime`, `Score`, `Performance`, `Outcome`, `AttachmentKeys`, `Notes`, `GraphVisible`, `SuggestedEdit`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "feedback"`

Suggested mapping:
- `occurred_at`: `EntryDatetime`
- `details`: `Score`, `Performance`, `Outcome`, `ExitDatetime`, `Notes`, `GraphVisible`, `SuggestedEdit`, `AttachmentKeys`
- `legacy_fields`: `FeedbackID`, `ActivityDate`, `Username`

---

### 7) `conferences`

Legacy columns:
`MRN`, `ADM`, `ConferenceID`, `EntryDatetime`, `Type`, `AttachmentKeys`, `ActionItems`, `Notes`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "conference"`

Suggested mapping:
- `occurred_at`: `EntryDatetime`
- `details`: `Type`, `ActionItems`, `Notes`, `AttachmentKeys`, `ConferenceID`
- `legacy_fields`: `ActivityDate`, `Username`

---

### 8) `bedside_procedures`

Legacy columns:
`MRN`, `ADM`, `LocationStepID`, `BedsideProcedureID`, `StartDatetime`, `EndDatetime`, `ProcedureType`, `Teams`, `Notes`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "bedside_procedure"`

Suggested mapping:
- `occurred_at`: `StartDatetime`
- `details`: `EndDatetime`, `ProcedureType`, `Teams`, `Notes`, `LocationStepID`, `BedsideProcedureID`
- `legacy_fields`: `ActivityDate`, `Username`

---

### 9) `continuous_therapy`

Legacy columns:
`MRN`, `ADM`, `CtId`, `EntryDatetime`, `Type`, `Status`, `AttachmentKeys`, `Notes`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "continuous_therapy"`

Suggested mapping:
- `occurred_at`: `EntryDatetime`
- `details`: `Type`, `Status`, `AttachmentKeys`, `Notes`, `CtId`
- `legacy_fields`: `ActivityDate`, `Username`

---

### 10) `course_corrections`

Legacy columns:
`MRN`, `ADM`, `course_correct_id`, `EntryDatetime`, `type`, `detail`, `Username`, `ActivityDate`

Target event: `clinical_event.recorded` with `event_type = "course_correction"`

Suggested mapping:
- `occurred_at`: `EntryDatetime`
- `details`: `type`, `detail`, `course_correct_id`
- `legacy_fields`: `ActivityDate`, `Username`

---

### 11) `attachments`

Legacy columns:
`MRN`, `ADM`, `AttachmentID`, `LocationStepID`, `LocationRiskID`, `EntryDatetime`, `storage_key`, `Filename`, `Description`, `AttachmentType`, `ContentType`, `Thumbnail`, `Username`, `ActivityDate`

**New event required**: `attachment.added`

Suggested mapping:
- `admission_id`: from ADM mapping
- `occurred_at`: `EntryDatetime`
- `details`: `storage_key`, `Filename`, `Description`, `AttachmentType`, `ContentType`, `Thumbnail`
- `linkage`: `LocationStepID` or `LocationRiskID` (if attachment is tied to a specific event)
- `legacy_fields`: `AttachmentID`, `ActivityDate`, `Username`

Notes:
- Actual file storage should be outside the database (object storage) with the `storage_key` as reference.

---

### 12) `users`

Legacy columns:
`username`, `occupation`, `credentials`, `last_access`

Suggested handling:
- Use external identity provider in enterprise system.
- Preserve legacy `username` in event metadata for audit until real user mapping exists.
- Create a one-time mapping table: `legacy_username` → `user_id` (UUID).

---

## Core vs Plugin Guidance

**Core (shared across specialties):**
- Patient identity
- Admissions
- Location/trajectory
- Attachments metadata

**Cardiac plugin (specialty-specific):**
- Risk status categories
- Bedside procedures
- Continuous therapy
- Course corrections
- Feedbacks, conferences, annotations

This keeps the enterprise core stable while allowing each specialty to define its own event types and business rules.

---

## Open Decisions / Next Steps

1. **Event contract expansion:** Define `attachment.added` and confirm `risk_status` event type.
2. **Value standardization:** Map legacy codes to canonical enums (see `legacy-reference/core/FpCodes.py`).
3. **Identity mapping:** Decide how to map `username` → `created_by` UUIDs.
4. **Backfill plan:** Design ETL to replay legacy rows into the event store in chronological order.
5. **Validation:** Clinician review of mappings for clinical meaning and safety.

