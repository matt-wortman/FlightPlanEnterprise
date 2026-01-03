# Current Database Schema

**Last Updated:** January 3, 2026
**Source:** Alembic migrations 001-002
**Database:** PostgreSQL 16 / SQLite (dev)

This document describes the **actively implemented** database schema from Alembic migrations, not the legacy schema.

## Overview

The FlightPlan Enterprise database uses **Event Sourcing** with **CQRS** (Command Query Responsibility Segregation):

- **Event Store Tables**: Immutable event log (source of truth)
- **Read Model Tables**: Denormalized views optimized for queries
- **Tenant Tables**: Multi-tenant isolation

## Schema Diagram

```
┌─────────────┐
│   tenants   │
└──────┬──────┘
       │
       │ tenant_id (FK to all tables)
       │
       ├─────────────────────────────────────────┐
       │                                         │
┌──────▼──────┐                          ┌──────▼──────┐
│   events    │◄────┬─────────────────── │ snapshots   │
└─────────────┘     │                    └─────────────┘
                    │
                    │ stream_id
                    │
            ┌───────┴────────┐
            │ subscriptions  │
            └────────────────┘

Read Models (denormalized from events):
┌──────────────────────┐
│ patient_read_models  │
└──────┬───────────────┘
       │
       │ patient_id (FK)
       │
┌──────▼────────────────┐      ┌─────────────────────┐
│ admission_read_models │─────►│ flightplan_read_... │
└──────┬────────────────┘      └─────────────────────┘
       │
       │ admission_id (FK)
       │
       ├───────────────┬─────────────────┐
       │               │                 │
┌──────▼──────┐ ┌──────▼──────┐  ┌──────▼──────┐
│ timeline_   │ │ trajectory_ │  │   (more     │
│ events      │ │ points      │  │  read       │
└─────────────┘ └─────────────┘  │  models)    │
                                 └─────────────┘
```

---

## Event Store Tables

### `events`

**Purpose**: Immutable append-only log of all system events (source of truth)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `event_id` | UUID | PRIMARY KEY | Unique event identifier |
| `stream_id` | UUID | NOT NULL | Aggregate/entity ID (e.g., admission ID) |
| `stream_type` | VARCHAR(100) | NOT NULL | Aggregate type (e.g., "Admission", "Patient") |
| `event_type` | VARCHAR(200) | NOT NULL | Event type (e.g., "admission.created") |
| `event_version` | INTEGER | NOT NULL | Version within stream (optimistic locking) |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `data` | JSONB | NOT NULL | Event payload |
| `metadata` | JSONB | NOT NULL | Event metadata (correlation ID, causation ID) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Event timestamp |
| `created_by` | UUID | NOT NULL | User who created the event |
| `global_position` | BIGINT | UNIQUE, NOT NULL | Global ordering (auto-incrementing) |

**Unique Constraints:**
- `(stream_id, event_version)` - Prevents duplicate versions in stream

**Indexes:**
- `idx_events_stream` on `(stream_id, event_version)` - Read stream events
- `idx_events_type` on `(event_type, created_at)` - Query by event type
- `idx_events_tenant` on `(tenant_id, created_at)` - Tenant isolation
- `idx_events_global_position` on `(global_position)` - Ordered read of all events
- `idx_events_created_at` on `(created_at)` - Time-based queries

**Notes:**
- Events are **never updated or deleted** (append-only)
- `global_position` provides total ordering for projections
- `event_version` enables optimistic concurrency control

---

### `snapshots`

**Purpose**: Periodic state snapshots to optimize event replay

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `snapshot_id` | UUID | PRIMARY KEY | Unique snapshot identifier |
| `stream_id` | UUID | NOT NULL | Aggregate ID |
| `stream_type` | VARCHAR(100) | NOT NULL | Aggregate type |
| `version` | INTEGER | NOT NULL | Event version at snapshot |
| `state` | JSONB | NOT NULL | Aggregate state |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Snapshot timestamp |

**Unique Constraints:**
- `(stream_id, version)` - One snapshot per stream version

**Indexes:**
- `idx_snapshots_stream` on `(stream_id, version DESC)` - Find latest snapshot

**Notes:**
- Snapshots are **optional** - events are the source of truth
- Used to avoid replaying thousands of events for long-lived aggregates
- Typically created every N events (e.g., every 100 events)

---

### `subscriptions`

**Purpose**: Track projection progress through event stream

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `subscription_id` | VARCHAR(200) | PRIMARY KEY | Subscription name (e.g., "patient_projection") |
| `last_position` | BIGINT | NOT NULL, DEFAULT 0 | Last processed global_position |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes:**
- `idx_subscriptions_updated` on `(updated_at)` - Monitor subscription health

**Notes:**
- Each projection maintains its own subscription
- Enables **at-least-once** event processing
- Allows projections to catch up independently

---

## Tenant Tables

### `tenants`

**Purpose**: Multi-tenant configuration and isolation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Tenant identifier |
| `name` | VARCHAR(255) | NOT NULL | Tenant display name |
| `subdomain` | VARCHAR(100) | UNIQUE | Subdomain for tenant (e.g., "hospital1") |
| `plan` | VARCHAR(50) | NULL | Subscription plan (e.g., "enterprise", "standard") |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Tenant active status |
| `features` | JSONB | NOT NULL, DEFAULT '{}' | Feature flags (e.g., {"analytics": true}) |
| `enabled_specialties` | JSONB | NOT NULL, DEFAULT '[]' | Enabled specialty plugins (e.g., ["cardiac", "ortho"]) |
| `branding` | JSONB | NOT NULL, DEFAULT '{}' | Custom branding (logo, colors) |
| `integrations` | JSONB | NOT NULL, DEFAULT '{}' | External system integrations |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Tenant creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes:**
- `idx_tenants_active` on `(is_active)` - Query active tenants

**Notes:**
- All other tables have `tenant_id` foreign key for isolation
- `subdomain` enables tenant resolution from URL (e.g., `hospital1.flightplan.app`)
- `enabled_specialties` controls which plugins are active

---

## Read Model Tables

Read models are **denormalized views** built from events for query performance.

### `patient_read_models`

**Purpose**: Queryable patient data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Patient UUID (NOT MRN - PHI compliance) |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `data` | JSONB | NOT NULL | Patient data (name, DOB, MRN encrypted, etc.) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes:**
- `idx_patient_tenant` on `(tenant_id)` - Tenant isolation

**Data Structure (JSON):**
```json
{
  "patient_id": "uuid",
  "name": "string",
  "mrn_encrypted": "encrypted_string",
  "date_of_birth": "YYYY-MM-DD",
  "gender": "string",
  "contact": {
    "phone": "string",
    "email": "string"
  }
}
```

**Notes:**
- MRN is **encrypted** in the JSON data
- Patient ID in URLs, never MRN (PHI compliance)

---

### `admission_read_models`

**Purpose**: Queryable admission data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Admission UUID |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `patient_id` | UUID | NOT NULL | Foreign key to patient |
| `data` | JSONB | NOT NULL | Admission data |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes:**
- `idx_admission_tenant` on `(tenant_id)` - Tenant isolation
- `idx_admission_patient` on `(patient_id)` - Query admissions by patient

**Data Structure (JSON):**
```json
{
  "admission_id": "uuid",
  "patient_id": "uuid",
  "specialty": "cardiac",
  "attending_id": "uuid",
  "admit_date": "ISO-8601 datetime",
  "discharge_date": "ISO-8601 datetime or null",
  "chief_complaint": "string",
  "admission_type": "emergency|elective|transfer",
  "status": "active|discharged|transferred",
  "current_location": "ICU|Floor|Discharge",
  "current_bed": "string or null"
}
```

---

### `flightplan_read_models`

**Purpose**: Queryable care plan data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | FlightPlan UUID |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `admission_id` | UUID | NOT NULL | Foreign key to admission |
| `data` | JSONB | NOT NULL | Care plan data |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Indexes:**
- `idx_flightplan_tenant` on `(tenant_id)` - Tenant isolation
- `idx_flightplan_admission` on `(admission_id)` - One-to-one with admission

**Data Structure (JSON):**
```json
{
  "flightplan_id": "uuid",
  "admission_id": "uuid",
  "status": "draft|active|completed",
  "milestones": [
    {
      "name": "Surgery",
      "scheduled_date": "ISO-8601",
      "completed": true
    }
  ],
  "risk_score": 0.75,
  "alerts": []
}
```

---

### `timeline_events`

**Purpose**: Denormalized timeline for UI display

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Timeline event ID |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `admission_id` | UUID | NOT NULL | Foreign key to admission |
| `event_type` | VARCHAR(200) | NOT NULL | Event type (procedure, annotation, etc.) |
| `occurred_at` | TIMESTAMP | NOT NULL | When the event occurred |
| `data` | JSONB | NOT NULL | Event-specific data |

**Indexes:**
- `idx_timeline_tenant` on `(tenant_id)` - Tenant isolation
- `idx_timeline_admission` on `(admission_id)` - Query by admission
- `idx_timeline_occurred` on `(occurred_at)` - Time-based ordering

**Data Structure (JSON):**
```json
{
  "event_id": "uuid",
  "event_type": "surgery|procedure|annotation|location_change",
  "occurred_at": "ISO-8601",
  "title": "string",
  "description": "string",
  "details": { /* event-specific */ }
}
```

**Notes:**
- Built from multiple event types for unified timeline view
- Optimized for chronological queries

---

### `trajectory_points`

**Purpose**: Patient location history for trajectory visualization

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Trajectory point ID |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `admission_id` | UUID | NOT NULL | Foreign key to admission |
| `location` | VARCHAR(200) | NOT NULL | Location code (ICU, Floor, etc.) |
| `effective_at` | TIMESTAMP | NOT NULL | When patient entered location |
| `data` | JSONB | NOT NULL | Additional location data |

**Indexes:**
- `idx_trajectory_tenant` on `(tenant_id)` - Tenant isolation
- `idx_trajectory_admission` on `(admission_id)` - Query by admission
- `idx_trajectory_effective` on `(effective_at)` - Time-based ordering

**Data Structure (JSON):**
```json
{
  "location": "ICU",
  "bed": "ICU-12",
  "effective_at": "ISO-8601",
  "ended_at": "ISO-8601 or null",
  "reason": "Post-surgical monitoring",
  "risk_level": "high|medium|low"
}
```

**Notes:**
- Enables "where was patient at time T" queries
- Built from `admission.location_changed` events

---

### `attachment_read_models`

**Purpose**: Metadata for file attachments linked to an admission

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Attachment UUID |
| `tenant_id` | UUID | NOT NULL | Tenant isolation |
| `admission_id` | UUID | NOT NULL | Foreign key to admission |
| `occurred_at` | TIMESTAMP | NOT NULL | When attachment was added |
| `data` | JSONB | NOT NULL | Attachment metadata |

**Indexes:**
- `idx_attachment_tenant` on `(tenant_id)` - Tenant isolation
- `idx_attachment_admission` on `(admission_id)` - Query by admission
- `idx_attachment_occurred` on `(occurred_at)` - Time-based ordering

**Data Structure (JSON):**
```json
{
  "attachment_id": "uuid",
  "admission_id": "uuid",
  "occurred_at": "ISO-8601",
  "storage_key": "string",
  "filename": "string",
  "description": "string",
  "attachment_type": "string",
  "content_type": "string"
}
```

**Notes:**
- Stores metadata only (file contents live in object storage)
- Built from `attachment.added` events

---

## Migration History

### 001_event_store (2026-01-02 12:10:00)

**Created:**
- `events` - Event store
- `snapshots` - State snapshots
- `subscriptions` - Projection tracking

**Purpose:** Core event sourcing infrastructure

---

### 002_read_models_and_tenants (2026-01-02 13:00:00)

**Created:**
- `tenants` - Multi-tenant management
- `patient_read_models` - Patient queries
- `admission_read_models` - Admission queries
- `flightplan_read_models` - Care plan queries
- `timeline_events` - Timeline views
- `trajectory_points` - Location history

**Purpose:** CQRS read models and tenant isolation

---

### 003_attachment_read_models (2026-01-03 09:00:00)

**Created:**
- `attachment_read_models` - Attachment metadata

**Purpose:** Attachment metadata read model

---

## Data Types

### GUID (UUID)

Custom SQLAlchemy type that:
- Stores as `CHAR(36)` in SQLite
- Stores as `UUID` native type in PostgreSQL
- Automatically converts Python `uuid.UUID` ↔ database

### JSONB

- PostgreSQL: Native `JSONB` (binary JSON with indexing)
- SQLite: `TEXT` with JSON validation

---

## Querying Patterns

### Event Stream Read (Replay)

```sql
-- Read all events for an admission
SELECT * FROM events
WHERE stream_id = :admission_id
ORDER BY event_version ASC;

-- Read events since position (for projections)
SELECT * FROM events
WHERE global_position > :last_position
ORDER BY global_position ASC
LIMIT 1000;
```

### Read Model Queries

```sql
-- Get patient with admissions
SELECT p.data, array_agg(a.data) as admissions
FROM patient_read_models p
LEFT JOIN admission_read_models a ON a.patient_id = p.id
WHERE p.tenant_id = :tenant_id
  AND p.id = :patient_id
GROUP BY p.id;

-- Get admission timeline
SELECT * FROM timeline_events
WHERE tenant_id = :tenant_id
  AND admission_id = :admission_id
ORDER BY occurred_at ASC;
```

---

## Future Schema Extensions

Planned additions (not yet implemented):

- **Annotations**: Clinical notes and markers
- **Conferences**: Multi-disciplinary meetings
- **Procedures**: Surgical/clinical procedure details
- **Risk Assessments**: Location-specific risk scores
- **Attachments**: File references
- **Audit Log**: User action tracking (separate from events)

---

## Schema Maintenance

### Adding New Fields

1. Modify SQLAlchemy models in `backend/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit migration file
4. Test migration: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
5. Commit migration file to git

### Adding New Tables

Follow same process as adding fields. Consider:
- Is this a read model? Add projection in `backend/app/projections/`
- Does it need tenant isolation? Add `tenant_id` column and index
- Does it reference other entities? Add foreign key indexes

### Backward Compatibility

- **Never drop columns** - Mark as deprecated instead
- **Never change column types** - Add new column, migrate data, deprecate old
- **Events are immutable** - New event types, never modify existing

---

## Related Documentation

- **Event Contracts**: [/backend/docs/event_contracts_v1.md](/backend/docs/event_contracts_v1.md)
- **Database Setup**: [/docs/DATABASE_SETUP.md](/docs/DATABASE_SETUP.md)
- **Architecture**: [/docs/architecture/DATABASE_ARCHITECTURE.md](/docs/architecture/DATABASE_ARCHITECTURE.md)
- **Legacy Schema**: [/docs/data-model/DATABASE_SCHEMA_DUMP.sql](/docs/data-model/DATABASE_SCHEMA_DUMP.sql) (reference only)
