# Event Contracts v1

**Last Updated:** January 2, 2026
**Status:** Active - In Production Use
**Version:** 1.0

This document defines the event contracts (schemas) used by the event store and projections.

## Conventions

- **event_type**: Dot-delimited string following pattern `{aggregate}.{action}` (e.g., `admission.created`)
- **stream_type**: Aggregate name in PascalCase (e.g., `Admission`, `Patient`)
- **stream_id**: UUID identifier for the aggregate instance
- **data**: Event payload (JSON object with strongly-typed fields)
- **metadata**: Event metadata (correlation ID, causation ID, user context)

## Validation Rules

All events must:
1. Have a valid UUID for `event_id`, `stream_id`, and `created_by`
2. Have `event_version` as a positive integer
3. Have `data` as a valid JSON object (not null, not array)
4. Have `created_at` as ISO-8601 datetime with timezone
5. Include `tenant_id` for multi-tenant isolation

## Field Types

- **UUID**: RFC 4122 UUID (e.g., `123e4567-e89b-12d3-a456-426614174000`)
- **DateTime**: ISO-8601 format with timezone (e.g., `2026-01-02T10:00:00Z`)
- **String**: UTF-8 text, max length specified per field
- **Integer**: 32-bit signed integer
- **Decimal**: Numeric with fixed precision (for monetary values, scores)

## Core Events

### patient.created

**Stream:** Patient
**Purpose:** Records creation of a new patient record

**Fields:**

| Field | Type | Required | Max Length | Validation |
|-------|------|----------|------------|------------|
| `patient_id` | UUID | Yes | - | Valid UUID |
| `name` | String | Yes | 255 | Non-empty |
| `mrn` | String | Yes | 255 | Encrypted/tokenized, non-empty |
| `date_of_birth` | String | Yes | - | ISO-8601 date (YYYY-MM-DD) |
| `gender` | String | No | 50 | One of: "male", "female", "other", "unknown" |

**Example:**

```json
{
  "patient_id": "223e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "mrn": "ENC_abc123xyz789",
  "date_of_birth": "1965-03-15",
  "gender": "male"
}
```

**Business Rules:**
- MRN must be encrypted before storing (never plain text)
- `patient_id` must be globally unique
- PHI fields (name, MRN, DOB) must never appear in logs or URLs

---

### admission.created

**Stream:** Admission
**Purpose:** Records patient admission to hospital

**Fields:**

| Field | Type | Required | Max Length | Validation |
|-------|------|----------|------------|------------|
| `admission_id` | UUID | Yes | - | Valid UUID, globally unique |
| `patient_id` | UUID | Yes | - | Valid UUID, must reference existing patient |
| `specialty` | String | Yes | 100 | Non-empty, matches plugin specialty |
| `attending_id` | UUID | Yes | - | Valid UUID (physician/provider) |
| `admit_date` | String | Yes | - | ISO-8601 datetime with timezone |
| `chief_complaint` | String | No | 500 | Clinical description |
| `admission_type` | String | No | 50 | One of: "emergency", "elective", "transfer" |

**Example:**

```json
{
  "admission_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "223e4567-e89b-12d3-a456-426614174000",
  "specialty": "cardiac",
  "attending_id": "323e4567-e89b-12d3-a456-426614174000",
  "admit_date": "2026-01-02T10:00:00Z",
  "chief_complaint": "Chest pain, shortness of breath",
  "admission_type": "emergency"
}
```

**Business Rules:**
- `admission_id` must be globally unique
- `patient_id` must exist (eventual consistency check in projection)
- `specialty` must match an enabled plugin for the tenant
- `admit_date` cannot be in the future

---

### admission.location_changed

**Stream:** Admission
**Purpose:** Records patient movement between hospital locations

**Fields:**

| Field | Type | Required | Max Length | Validation |
|-------|------|----------|------------|------------|
| `admission_id` | UUID | Yes | - | Valid UUID |
| `from_location` | String | No | 100 | Location code (null if first location) |
| `to_location` | String | Yes | 100 | Non-empty location code |
| `from_bed` | String | No | 50 | Bed identifier |
| `to_bed` | String | No | 50 | Bed identifier |
| `effective_at` | String | Yes | - | ISO-8601 datetime with timezone |
| `reason` | String | No | 500 | Clinical reason for transfer |

**Example:**

```json
{
  "admission_id": "123e4567-e89b-12d3-a456-426614174000",
  "from_location": "ER",
  "to_location": "ICU",
  "from_bed": "ER-3",
  "to_bed": "ICU-12",
  "effective_at": "2026-01-02T14:30:00Z",
  "reason": "Post-surgical monitoring required"
}
```

**Business Rules:**
- `from_location` is null only for the first location assignment
- `effective_at` must be >= admission admit_date
- `to_location` must be different from `from_location` (if from_location exists)
- Location codes should match tenant's configured locations

---

### flightplan.created

**Stream:** FlightPlan
**Purpose:** Initializes care plan for an admission

**Fields:**

| Field | Type | Required | Max Length | Validation |
|-------|------|----------|------------|------------|
| `flightplan_id` | UUID | Yes | - | Valid UUID, globally unique |
| `admission_id` | UUID | Yes | - | Valid UUID, must reference existing admission |
| `status` | String | Yes | 50 | One of: "draft", "active", "completed", "cancelled" |

**Example:**

```json
{
  "flightplan_id": "423e4567-e89b-12d3-a456-426614174000",
  "admission_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "draft"
}
```

**Business Rules:**
- Each admission can have only one FlightPlan (1:1 relationship)
- `flightplan_id` typically matches `admission_id` for simplicity
- Initial status is typically "draft"

---

### clinical_event.recorded

**Stream:** Admission
**Purpose:** Records clinical events (procedures, surgeries, consultations, etc.)

**Fields:**

| Field | Type | Required | Max Length | Validation |
|-------|------|----------|------------|------------|
| `event_id` | UUID | Yes | - | Valid UUID, globally unique |
| `admission_id` | UUID | Yes | - | Valid UUID |
| `event_type` | String | Yes | 200 | Event classification (e.g., "surgery", "procedure", "consultation") |
| `occurred_at` | String | Yes | - | ISO-8601 datetime with timezone |
| `details` | Object | No | - | Event-specific additional data (varies by event_type) |

**Example:**

```json
{
  "event_id": "523e4567-e89b-12d3-a456-426614174000",
  "admission_id": "123e4567-e89b-12d3-a456-426614174000",
  "event_type": "surgery",
  "occurred_at": "2026-01-03T09:00:00Z",
  "details": {
    "procedure_name": "CABG",
    "surgeon_id": "623e4567-e89b-12d3-a456-426614174000",
    "duration_minutes": 240,
    "outcome": "successful"
  }
}
```

**Business Rules:**
- `event_id` must be globally unique
- `occurred_at` should be >= admission admit_date and <= discharge_date (if discharged)
- `details` structure varies by `event_type` and specialty plugin
- Clinical events appear on the timeline in chronological order

---

## PHI Security Requirements

**CRITICAL:** These events contain Protected Health Information (PHI) and must be handled securely:

- **Never log event data** containing patient names, MRN, or identifying information
- **Never expose MRN in URLs** - use patient_id (UUID) instead
- **Encrypt MRN at rest** - always store encrypted/tokenized
- **Use HTTPS/TLS** for all event transmission
- **Audit all access** - event store provides complete audit trail

---

## Event Versioning

As the system evolves, event contracts will change. Follow these rules:

1. **Additive changes only** - Add new optional fields, never remove or rename existing fields
2. **New event types** - For significant changes, create a new event type (e.g., `admission.created.v2`)
3. **Version in metadata** - Include `schema_version` in event metadata
4. **Backward compatibility** - Projections must handle all versions of an event type

**Example of additive change:**

```json
// v1
{
  "admission_id": "uuid",
  "patient_id": "uuid"
}

// v2 (added optional field - backward compatible)
{
  "admission_id": "uuid",
  "patient_id": "uuid",
  "referral_source": "string"  // NEW - optional
}
```

---

## Related Documentation

- **Current Schema**: [/docs/data-model/CURRENT_SCHEMA.md](/docs/data-model/CURRENT_SCHEMA.md)
- **API Documentation**: [/docs/API.md](/docs/API.md)
- **Database Setup**: [/docs/DATABASE_SETUP.md](/docs/DATABASE_SETUP.md)
- **Plugin Development**: [/docs/PLUGIN_DEVELOPMENT.md](/docs/PLUGIN_DEVELOPMENT.md)
