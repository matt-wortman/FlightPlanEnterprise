# API Documentation

**Last Updated:** 2026-01-02
**API Version:** v1
**Base URL:** `http://localhost:8000` (development)

Complete API reference for FlightPlan Enterprise backend.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Tenant Context](#tenant-context)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Commands API](#commands-api)
  - [Events API](#events-api)
  - [Read Models API](#read-models-api)
  - [Plugins API](#plugins-api)
- [Data Models](#data-models)
- [Event Contracts](#event-contracts)
- [Examples](#examples)

---

## Overview

### Architecture Style

FlightPlan uses **CQRS** (Command Query Responsibility Segregation) with **Event Sourcing**:

- **Commands**: Write operations that generate events (POST /api/v1/admissions)
- **Events**: Append-only log of what happened (POST /api/v1/events)
- **Queries**: Read operations from optimized read models (GET /api/v1/admissions)

### API Characteristics

- **RESTful** design with resource-oriented URLs
- **JSON** request/response bodies
- **UUID** identifiers (never expose PHI like MRN in URLs)
- **Multi-tenant** with tenant isolation
- **Async** processing with eventual consistency
- **Idempotent** writes where possible

### Base URL

| Environment | Base URL |
|-------------|----------|
| Development | `http://localhost:8000` |
| Staging | `https://staging-api.flightplan.example.com` |
| Production | `https://api.flightplan.example.com` |

### Content Type

All requests and responses use `application/json`:

```http
Content-Type: application/json
Accept: application/json
```

---

## Authentication

### Development Mode

Currently, authentication is **mocked** for development:

```http
# No authentication required in development
GET /api/v1/admissions
```

### Production Mode (Future)

Will use **Azure AD** (Microsoft Entra ID) with OAuth 2.0:

```http
# Future production authentication
GET /api/v1/admissions
Authorization: Bearer <azure_ad_token>
```

**Token Acquisition (Future):**
```bash
# Get token from Azure AD
curl -X POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token \
  -d "client_id={client_id}" \
  -d "client_secret={client_secret}" \
  -d "scope=api://flightplan/.default" \
  -d "grant_type=client_credentials"
```

---

## Tenant Context

### Multi-Tenancy Model

Every API request operates within a **tenant context**. Tenants represent:
- Different hospitals
- Different departments
- Different organizational units

### Tenant ID Header

In development, tenant ID is provided via header:

```http
GET /api/v1/admissions
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

In production, tenant ID is extracted from Azure AD token claims.

### Tenant Isolation

**All queries are automatically filtered by tenant:**

```python
# Backend automatically adds tenant_id filter
SELECT * FROM admissions
WHERE tenant_id = :current_tenant_id  -- Automatic
  AND id = :admission_id              -- User-specified
```

**🔒 Security Guarantee:** Tenant A can NEVER access Tenant B's data.

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/POST |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request body/params |
| 401 | Unauthorized | Missing/invalid auth token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Concurrency error, version mismatch |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary outage |

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "field_errors": {
    "field_name": ["Error message 1", "Error message 2"]
  }
}
```

### Example Error Responses

**Validation Error (422):**
```json
{
  "detail": "Validation error",
  "field_errors": {
    "specialty": ["Value 'invalid_specialty' is not a valid specialty code"],
    "admit_date": ["Date cannot be in the future"]
  }
}
```

**Concurrency Error (409):**
```json
{
  "detail": "Version mismatch: expected version 5 but stream is at version 7",
  "error_code": "CONCURRENCY_ERROR",
  "expected_version": 5,
  "actual_version": 7
}
```

**Not Found (404):**
```json
{
  "detail": "Admission not found",
  "error_code": "RESOURCE_NOT_FOUND",
  "resource_type": "admission",
  "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## Rate Limiting

**Current Status:** Not implemented (development)

**Future Implementation:**
- 1000 requests per minute per tenant
- 100 write operations per minute per tenant
- `X-RateLimit-*` headers in responses

---

## Endpoints

### Health Check

#### GET /health

Check API server health status.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok"
}
```

**Use Case:** Load balancer health checks, monitoring

---

### Commands API

Commands are **write operations** that create events.

#### POST /api/v1/admissions

Create a new admission and associated FlightPlan.

**Request:**
```http
POST /api/v1/admissions HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Tenant-ID: 00000000-0000-0000-0000-000000000001

{
  "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "specialty": "cardiac_surgery",
  "attending_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "admit_date": "2025-01-15T08:30:00Z",
  "chief_complaint": "Chest pain, shortness of breath",
  "admission_type": "emergency",
  "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| admission_id | UUID | Yes | Unique admission identifier (client-generated) |
| patient_id | UUID | Yes | Patient identifier (opaque, NOT MRN) |
| specialty | string | Yes | Medical specialty code (see [FpCodes](../legacy-reference/core/FpCodes.py)) |
| attending_id | UUID | Yes | Attending physician identifier |
| admit_date | datetime | Yes | Admission date/time (ISO 8601 format) |
| chief_complaint | string | No | Primary reason for admission |
| admission_type | string | No | Type: "elective", "emergency", "urgent" |
| created_by | UUID | Yes | User who created the admission |

**Valid Specialty Codes:**
- `cardiac_surgery` - Cardiac Surgery
- `neurosurgery` - Neurosurgery
- `orthopedics` - Orthopedic Surgery
- `general_surgery` - General Surgery
- `transplant` - Transplant Surgery

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "new_version": 1
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| new_version | integer | Version of the admission stream after event appended |

**Generated Event:**
```json
{
  "event_type": "admission.created",
  "data": {
    "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "specialty": "cardiac_surgery",
    "attending_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "admit_date": "2025-01-15T08:30:00Z",
    "chief_complaint": "Chest pain, shortness of breath",
    "admission_type": "emergency"
  }
}
```

**Errors:**
- `400`: Invalid specialty code
- `422`: Validation error (missing required fields, invalid date format)

---

#### POST /api/v1/admissions/{admission_id}/location

Change patient location within the hospital.

**Request:**
```http
POST /api/v1/admissions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/location HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Tenant-ID: 00000000-0000-0000-0000-000000000001

{
  "from_location": "ICU",
  "to_location": "Floor_3A",
  "from_bed": "ICU-12",
  "to_bed": "3A-205",
  "effective_at": "2025-01-16T14:30:00Z",
  "reason": "Patient stable, ready for step-down",
  "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| admission_id | UUID | Admission identifier |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| from_location | string | No | Previous location (null if first location) |
| to_location | string | Yes | New location code |
| from_bed | string | No | Previous bed identifier |
| to_bed | string | No | New bed identifier |
| effective_at | datetime | Yes | When location change occurred (ISO 8601) |
| reason | string | No | Reason for transfer |
| created_by | UUID | Yes | User who recorded the change |

**Valid Location Codes:**
- `ER` - Emergency Room
- `ICU` - Intensive Care Unit
- `CVICU` - Cardiovascular ICU
- `Floor_3A`, `Floor_4B`, etc. - Hospital floors
- `OR` - Operating Room
- `PACU` - Post-Anesthesia Care Unit
- `Discharged` - Patient discharged

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "new_version": 2
}
```

**Generated Event:**
```json
{
  "event_type": "admission.location_changed",
  "data": {
    "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "from_location": "ICU",
    "to_location": "Floor_3A",
    "from_bed": "ICU-12",
    "to_bed": "3A-205",
    "effective_at": "2025-01-16T14:30:00Z",
    "reason": "Patient stable, ready for step-down"
  }
}
```

**Errors:**
- `404`: Admission not found
- `400`: Invalid location code
- `422`: Validation error

---

#### POST /api/v1/clinical-events

Record a clinical event for a patient admission.

**Request:**
```http
POST /api/v1/clinical-events HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Tenant-ID: 00000000-0000-0000-0000-000000000001

{
  "event_id": "e1f2a3b4-c5d6-7890-ef12-3456789abcde",
  "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event_type": "lab_result",
  "occurred_at": "2025-01-16T09:15:00Z",
  "data": {
    "test_name": "Troponin I",
    "result": "0.04",
    "unit": "ng/mL",
    "reference_range": "< 0.03",
    "critical": true
  },
  "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | UUID | Yes | Unique event identifier (client-generated) |
| admission_id | UUID | Yes | Associated admission |
| event_type | string | Yes | Type of clinical event |
| occurred_at | datetime | Yes | When event occurred (ISO 8601) |
| data | object | No | Event-specific data (flexible schema) |
| created_by | UUID | Yes | User who recorded the event |

**Event Types:**
- `lab_result` - Laboratory test result
- `vital_signs` - Vital signs measurement
- `medication_admin` - Medication administration
- `procedure` - Procedure performed
- `consultation` - Specialist consultation
- `imaging` - Imaging study
- `surgery` - Surgical procedure

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "new_version": 3
}
```

**Generated Event:**
```json
{
  "event_type": "clinical_event.recorded",
  "data": {
    "event_id": "e1f2a3b4-c5d6-7890-ef12-3456789abcde",
    "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "event_type": "lab_result",
    "occurred_at": "2025-01-16T09:15:00Z",
    "test_name": "Troponin I",
    "result": "0.04",
    "unit": "ng/mL",
    "reference_range": "< 0.03",
    "critical": true
  }
}
```

---

### Events API

Low-level event store operations.

#### POST /api/v1/events

Append events directly to the event store.

**⚠️ Note:** Most applications should use the Commands API instead. This endpoint is for advanced scenarios and event replay.

**Request:**
```http
POST /api/v1/events HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-Tenant-ID: 00000000-0000-0000-0000-000000000001

{
  "stream_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "stream_type": "Admission",
  "events": [
    {
      "event_type": "admission.created",
      "data": {
        "patient_id": "550e8400-e29b-41d4-a716-446655440000",
        "specialty": "cardiac_surgery"
      },
      "metadata": {
        "source": "migration",
        "original_timestamp": "2024-12-01T10:00:00Z"
      },
      "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }
  ],
  "expected_version": null
}
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| stream_id | UUID | Yes | Stream identifier (aggregate ID) |
| stream_type | string | Yes | Type of stream ("Admission", "Patient", etc.) |
| events | array | Yes | Events to append (at least 1) |
| expected_version | integer\|null | No | Expected current version (for concurrency control) |

**Event Object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_type | string | Yes | Event type (e.g., "admission.created") |
| data | object | Yes | Event data (any JSON) |
| metadata | object | No | Event metadata (any JSON) |
| created_by | UUID | Yes | User who created the event |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "new_version": 3
}
```

**Concurrency Control:**

Use `expected_version` to prevent concurrent writes:

```json
{
  "stream_id": "a1b2c3d4-...",
  "stream_type": "Admission",
  "events": [...],
  "expected_version": 5  // Expect stream to be at version 5
}
```

If stream is at version 7, returns **409 Conflict**:
```json
{
  "detail": "Version mismatch: expected 5 but stream is at 7",
  "expected_version": 5,
  "actual_version": 7
}
```

**Errors:**
- `400`: Invalid stream_type or empty events array
- `409`: Concurrency error (version mismatch)
- `422`: Validation error (invalid event format)

---

### Read Models API

Query optimized read models (projections from events).

#### GET /api/v1/patients

List patients for current tenant.

**Request:**
```http
GET /api/v1/patients?limit=50&offset=0 HTTP/1.1
Host: localhost:8000
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Max results to return (1-200) |
| offset | integer | 0 | Number of results to skip |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "mrn": "MRN001234",
      "name": "John Doe",
      "date_of_birth": "1965-03-15",
      "admission_count": 3
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| items | array | Array of patient objects |
| limit | integer | Limit used for query |
| offset | integer | Offset used for query |

**Patient Object:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Patient identifier (opaque) |
| mrn | string | Medical record number (PHI) |
| name | string | Patient full name (PHI) |
| date_of_birth | date | Date of birth (PHI) |
| admission_count | integer | Total number of admissions |

**Pagination Example:**
```bash
# Get first page
GET /api/v1/patients?limit=50&offset=0

# Get second page
GET /api/v1/patients?limit=50&offset=50

# Get third page
GET /api/v1/patients?limit=50&offset=100
```

---

#### GET /api/v1/patients/{patient_id}

Get a single patient by ID.

**Request:**
```http
GET /api/v1/patients/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| patient_id | UUID | Patient identifier |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "mrn": "MRN001234",
  "name": "John Doe",
  "date_of_birth": "1965-03-15",
  "admission_count": 3
}
```

**Errors:**
- `404`: Patient not found (or not in current tenant)

---

#### GET /api/v1/admissions

List admissions for current tenant.

**Request:**
```http
GET /api/v1/admissions?patient_id=550e8400-e29b-41d4-a716-446655440000&limit=50&offset=0 HTTP/1.1
Host: localhost:8000
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| patient_id | UUID | null | Filter by patient (optional) |
| limit | integer | 50 | Max results to return (1-200) |
| offset | integer | 0 | Number of results to skip |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "specialty": "cardiac_surgery",
      "attending_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "admit_date": "2025-01-15T08:30:00Z",
      "discharge_date": null,
      "status": "active",
      "current_location": "ICU"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**Admission Object:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Admission identifier |
| patient_id | UUID | Associated patient |
| specialty | string | Medical specialty |
| attending_id | UUID | Attending physician |
| admit_date | datetime | Admission date/time |
| discharge_date | datetime\|null | Discharge date/time (null if active) |
| status | string | "active", "discharged", "transferred" |
| current_location | string | Current patient location |

---

#### GET /api/v1/flightplans/{flightplan_id}

Get a FlightPlan (care plan) for an admission.

**Request:**
```http
GET /api/v1/flightplans/f1e2d3c4-b5a6-7890-cdef-1234567890ab HTTP/1.1
Host: localhost:8000
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| flightplan_id | UUID | FlightPlan identifier |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "f1e2d3c4-b5a6-7890-cdef-1234567890ab",
  "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "target_discharge_date": "2025-01-25T12:00:00Z",
  "milestones": [
    {
      "name": "Surgery",
      "target_date": "2025-01-16T10:00:00Z",
      "status": "completed"
    },
    {
      "name": "ICU Recovery",
      "target_date": "2025-01-18T12:00:00Z",
      "status": "in_progress"
    }
  ]
}
```

**FlightPlan Object:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | FlightPlan identifier |
| admission_id | UUID | Associated admission |
| target_discharge_date | datetime | Planned discharge date |
| milestones | array | Care milestones |

**Errors:**
- `404`: FlightPlan not found

---

#### GET /api/v1/admissions/{admission_id}/timeline

Get timeline of events for an admission.

**Request:**
```http
GET /api/v1/admissions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/timeline HTTP/1.1
Host: localhost:8000
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| admission_id | UUID | Admission identifier |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "t1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "occurred_at": "2025-01-15T08:30:00Z",
      "event_type": "admission",
      "description": "Patient admitted to Cardiac Surgery",
      "data": {
        "specialty": "cardiac_surgery",
        "chief_complaint": "Chest pain"
      }
    },
    {
      "id": "t2b3c4d5-e6f7-8901-bcde-f12345678901",
      "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "occurred_at": "2025-01-16T10:00:00Z",
      "event_type": "surgery",
      "description": "Cardiac bypass surgery performed",
      "data": {
        "procedure": "CABG x4",
        "duration_minutes": 240
      }
    }
  ]
}
```

**Timeline Event Object:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Timeline event identifier |
| admission_id | UUID | Associated admission |
| occurred_at | datetime | When event occurred |
| event_type | string | Type of event |
| description | string | Human-readable description |
| data | object | Event-specific data |

---

#### GET /api/v1/admissions/{admission_id}/trajectory

Get patient location trajectory (movement history).

**Request:**
```http
GET /api/v1/admissions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/trajectory HTTP/1.1
Host: localhost:8000
X-Tenant-ID: 00000000-0000-0000-0000-000000000001
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| admission_id | UUID | Admission identifier |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "tr1a2b3c-d4e5-6789-0abc-def123456789",
      "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "effective_at": "2025-01-15T08:30:00Z",
      "location": "ER",
      "bed": "ER-5",
      "duration_hours": 2.5
    },
    {
      "id": "tr2b3c4d-e5f6-7890-1bcd-ef1234567890",
      "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "effective_at": "2025-01-15T11:00:00Z",
      "location": "ICU",
      "bed": "ICU-12",
      "duration_hours": 72.0
    }
  ]
}
```

**Trajectory Point Object:**

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Trajectory point identifier |
| admission_id | UUID | Associated admission |
| effective_at | datetime | When patient moved to this location |
| location | string | Location code |
| bed | string | Bed identifier |
| duration_hours | float | Hours spent at this location |

---

### Plugins API

Specialty-specific plugin management.

#### GET /api/v1/specialties

List available specialty plugins.

**Request:**
```http
GET /api/v1/specialties HTTP/1.1
Host: localhost:8000
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "name": "cardiac_surgery",
    "version": "1.0.0",
    "displayName": "Cardiac Surgery"
  },
  {
    "name": "neurosurgery",
    "version": "1.0.0",
    "displayName": "Neurosurgery"
  }
]
```

**Plugin Object:**

| Field | Type | Description |
|-------|------|-------------|
| name | string | Plugin identifier (specialty code) |
| version | string | Plugin version (semver) |
| displayName | string | Human-readable name |

---

#### GET /api/v1/specialties/{name}/config

Get UI configuration for a specialty plugin.

**Request:**
```http
GET /api/v1/specialties/cardiac_surgery/config HTTP/1.1
Host: localhost:8000
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| name | string | Specialty code |

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "timeline_events": [
    {
      "type": "cabg_surgery",
      "display": "CABG Surgery",
      "icon": "heart",
      "color": "#e74c3c"
    },
    {
      "type": "extubation",
      "display": "Extubation",
      "icon": "wind",
      "color": "#3498db"
    }
  ],
  "risk_factors": [
    {
      "key": "ejection_fraction",
      "label": "Ejection Fraction",
      "type": "number",
      "unit": "%",
      "normal_range": [55, 70]
    }
  ]
}
```

**Errors:**
- `404`: Plugin not found

---

## Data Models

### UUID Format

All identifiers are **UUIDs** (version 4):

```
550e8400-e29b-41d4-a716-446655440000
```

### DateTime Format

All timestamps use **ISO 8601** format with UTC timezone:

```
2025-01-15T08:30:00Z
```

### Enumerations

See [FpCodes.py](../legacy-reference/core/FpCodes.py) for complete enumeration of:
- Specialties
- Locations
- Access roles
- Teams
- Event types

---

## Event Contracts

See [backend/docs/event_contracts_v1.md](../backend/docs/event_contracts_v1.md) for complete event schema documentation.

### Core Events

**admission.created**
```json
{
  "event_type": "admission.created",
  "data": {
    "admission_id": "UUID",
    "patient_id": "UUID",
    "specialty": "string",
    "attending_id": "UUID",
    "admit_date": "ISO8601",
    "chief_complaint": "string|null",
    "admission_type": "string|null"
  }
}
```

**admission.location_changed**
```json
{
  "event_type": "admission.location_changed",
  "data": {
    "admission_id": "UUID",
    "from_location": "string|null",
    "to_location": "string",
    "effective_at": "ISO8601"
  }
}
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Create admission
curl -X POST http://localhost:8000/api/v1/admissions \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -d '{
    "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "specialty": "cardiac_surgery",
    "attending_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "admit_date": "2025-01-15T08:30:00Z",
    "chief_complaint": "Chest pain",
    "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }'

# 2. Change location
curl -X POST http://localhost:8000/api/v1/admissions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/location \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -d '{
    "from_location": "ER",
    "to_location": "ICU",
    "effective_at": "2025-01-15T11:00:00Z",
    "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }'

# 3. Record clinical event
curl -X POST http://localhost:8000/api/v1/clinical-events \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -d '{
    "event_id": "e1f2a3b4-c5d6-7890-ef12-3456789abcde",
    "admission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "event_type": "surgery",
    "occurred_at": "2025-01-16T10:00:00Z",
    "data": {
      "procedure": "CABG x4",
      "surgeon_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    },
    "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }'

# 4. Query admission timeline
curl http://localhost:8000/api/v1/admissions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/timeline \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"

# 5. Query trajectory
curl http://localhost:8000/api/v1/admissions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/trajectory \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

### Python Client Example

```python
import httpx
from uuid import uuid4

BASE_URL = "http://localhost:8000"
TENANT_ID = "00000000-0000-0000-0000-000000000001"

async def create_admission_workflow():
    async with httpx.AsyncClient() as client:
        # Create admission
        admission_id = uuid4()
        response = await client.post(
            f"{BASE_URL}/api/v1/admissions",
            headers={"X-Tenant-ID": TENANT_ID},
            json={
                "admission_id": str(admission_id),
                "patient_id": str(uuid4()),
                "specialty": "cardiac_surgery",
                "attending_id": str(uuid4()),
                "admit_date": "2025-01-15T08:30:00Z",
                "created_by": str(uuid4()),
            },
        )
        print(f"Created admission: {response.json()}")

        # Get admission timeline
        response = await client.get(
            f"{BASE_URL}/api/v1/admissions/{admission_id}/timeline",
            headers={"X-Tenant-ID": TENANT_ID},
        )
        print(f"Timeline: {response.json()}")
```

---

## Versioning

### API Version Strategy

- Current version: **v1**
- Version specified in URL path: `/api/v1/`
- Breaking changes require new version: `/api/v2/`
- Non-breaking changes can be added to existing version

### Backward Compatibility Promise

Within a major version (v1), we guarantee:
- ✅ New fields can be added to responses
- ✅ New optional parameters can be added to requests
- ✅ New endpoints can be added
- ❌ Existing fields will NOT be removed
- ❌ Field types will NOT change
- ❌ Required parameters will NOT be added

---

**Related Documentation:**
- [Event Contracts](../backend/docs/event_contracts_v1.md) - Complete event schema
- [TESTING.md](TESTING.md) - API testing guide
- [backend/README.md](../backend/README.md) - Backend setup
- [FpCodes.py](../legacy-reference/core/FpCodes.py) - Domain enumerations
