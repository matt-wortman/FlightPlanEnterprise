# FlightPlan Enterprise

**Status:** Active Development - Enterprise Rebuild
**Last Updated:** January 2, 2026

A medical patient management and clinical care planning platform for complex cardiac surgery care, multi-specialty coordination, and hospital workflow management.

## 🚀 Quick Start

New to the project? Start here:
1. Read [QUICKSTART.md](QUICKSTART.md) - Get running in 5 minutes
2. Review [docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md](docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md) - Understand the vision
3. Check [CONTRIBUTING.md](CONTRIBUTING.md) - Development workflow and standards

## Project Overview

**FlightPlan Enterprise** is a modern rebuild of the FlightPlan v2 legacy application, transitioning from a Python/Dash monolith to an event-sourced, multi-tenant SaaS platform.

### What Does It Do?

- **Patient & Admission Management**: Track patients across hospital stays with PHI-compliant data handling
- **Clinical Timeline Visualization**: Real-time patient trajectory through hospital locations
- **Multi-Team Coordination**: Enable cardiac surgery teams, ICU, floor care, and specialty consultations
- **Specialty Plugin Architecture**: Extensible platform supporting cardiac, orthopedic, and custom specialties
- **Event-Driven Architecture**: Full audit trail with event sourcing and CQRS patterns

### Domain

**Healthcare** - Specifically cardiac surgery care planning, with extensibility to any medical specialty requiring complex care coordination.

---

## Current Implementation Status

### ✅ Completed
- Event Store infrastructure with PostgreSQL
- Read model projections (CQRS pattern)
- Multi-tenant foundation with tenant isolation
- FastAPI backend with async SQLAlchemy
- Alembic migrations for schema management
- Plugin system foundation (cardiac specialty reference)
- Core API endpoints (admissions, patients, timelines, trajectories)
- PHI-compliant URL design (no MRN exposure)
- Test suite with SQLite/PostgreSQL support

### 🚧 In Progress
- Frontend (Next.js/TypeScript - planned)
- Authentication (Azure AD integration - planned)
- Event bus integration (Kafka - planned)
- Additional specialty plugins

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 | API and business logic |
| **Database** | PostgreSQL 16 (prod), SQLite (dev/test) | Event store and read models |
| **Frontend** | Next.js 14+, TypeScript, Tailwind | React framework with SSR (planned) |
| **Auth** | Azure AD (prod), Mock (dev) | Identity management (planned) |
| **Messaging** | Kafka | Event streaming (planned) |
| **ORM** | SQLAlchemy 2.0 (async) | Database abstraction |
| **Migrations** | Alembic | Schema versioning |

---

## Project Structure

```
FlightPlanEnterprise/
├── README.md                    # This file - project overview
├── QUICKSTART.md                # 5-minute getting started guide
├── CONTRIBUTING.md              # Development workflow and standards
├── CLAUDE.md                    # AI coding assistant guidelines
│
├── backend/                     # FastAPI application (ACTIVE)
│   ├── app/
│   │   ├── api/                 # REST API endpoints
│   │   ├── core/                # Database, config, tenant resolution
│   │   ├── infrastructure/      # Event store, projections
│   │   ├── models/              # SQLAlchemy models
│   │   └── projections/         # Read model builders
│   ├── alembic/                 # Database migrations
│   ├── plugins/                 # Specialty plugins (cardiac)
│   ├── tests/                   # Test suite
│   └── README.md                # Backend setup guide
│
├── docs/
│   ├── architecture/            # System design and planning
│   │   ├── ENTERPRISE_ARCHITECTURE_PLAN.md  # Full enterprise vision
│   │   ├── TECHNICAL_ARCHITECTURE.md        # Current architecture
│   │   └── DATABASE_ARCHITECTURE.md         # Database design rationale
│   ├── domain/                  # Clinical/medical domain knowledge
│   ├── data-model/              # Schema documentation
│   │   ├── CURRENT_SCHEMA.md    # Implemented schema from migrations
│   │   └── DATABASE_SCHEMA_DUMP.sql  # Legacy reference
│   ├── sample-data/             # CSV files for testing
│   ├── API.md                   # API endpoint documentation
│   ├── DATABASE_SETUP.md        # Database setup guide
│   ├── TESTING.md               # Test strategy and execution
│   └── PLUGIN_DEVELOPMENT.md    # How to create specialty plugins
│
└── legacy-reference/            # Legacy v2 codebase (REFERENCE ONLY)
    ├── core/                    # Key Python modules
    │   └── FpCodes.py           # CRITICAL - all domain enums
    ├── models/                  # Domain model classes
    │   └── Admission.py         # Core business logic (41KB)
    └── sql/                     # SQL schema templates
```

---

## Core Domain Concepts

### Patient → Admission → FlightPlan Hierarchy

```
Patient (identified by UUID - MRN is PHI!)
    │
    └── has many → Admissions (each = one hospital stay)
                       │
                       └── has one → FlightPlan (care plan for that admission)
                                         │
                                         └── contains → Timeline Events
                                                       Location Steps
                                                       Clinical Events
                                                       Annotations
```

### Key Domain Terms

- **Patient**: Individual with medical record (MRN stored encrypted, never in URLs)
- **Admission**: Single hospital stay with admit/discharge dates
- **FlightPlan**: Care plan and timeline for an admission
- **Location Step**: Patient movement through hospital (ER → ICU → Floor → Discharge)
- **Trajectory**: Time-series view of patient location changes
- **Clinical Event**: Procedures, surgeries, consultations, interventions
- **Annotation**: Clinical notes, markers, or comments on the timeline
- **Conference**: Multi-disciplinary team meeting about a patient
- **Specialty**: Clinical domain plugin (cardiac, orthopedic, etc.)

---

## Getting Started

### Prerequisites

- **Python 3.12+** - Backend runtime
- **PostgreSQL 16** - Production database (or SQLite for dev)
- **Node.js 18+** - Frontend (when implemented)
- **Git** - Version control

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment (copy and edit)
cp .env.example .env.local

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload
```

**API will be available at:** http://localhost:8000
**API docs:** http://localhost:8000/docs

See [backend/README.md](backend/README.md) for detailed setup instructions.

---

## Documentation Reading Order

### For New Developers
1. **[QUICKSTART.md](QUICKSTART.md)** - Get the app running
2. **[docs/domain/FLIGHTPLAN_REFACTOR_REPORT_FOR_CLINICIANS.md](docs/domain/FLIGHTPLAN_REFACTOR_REPORT_FOR_CLINICIANS.md)** - What the app does (non-technical)
3. **[legacy-reference/core/FpCodes.py](legacy-reference/core/FpCodes.py)** - Domain vocabulary (enums, codes)
4. **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

### For Architects
1. **[docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md](docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md)** - Full vision
2. **[docs/architecture/TECHNICAL_ARCHITECTURE.md](docs/architecture/TECHNICAL_ARCHITECTURE.md)** - Current implementation
3. **[docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)** - Database design
4. **[docs/data-model/CURRENT_SCHEMA.md](docs/data-model/CURRENT_SCHEMA.md)** - Schema details

### For API Developers
1. **[docs/API.md](docs/API.md)** - API endpoints and contracts
2. **[backend/docs/event_contracts_v1.md](backend/docs/event_contracts_v1.md)** - Event schema
3. **[docs/TESTING.md](docs/TESTING.md)** - Testing strategy

### For Plugin Developers
1. **[docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md)** - Plugin creation guide
2. **[backend/plugins/cardiac/manifest.yaml](backend/plugins/cardiac/manifest.yaml)** - Example plugin

---

## PHI Security Requirements (CRITICAL)

This application handles **Protected Health Information (PHI)** and must comply with **HIPAA** regulations.

### Never Expose PHI In:
- ❌ URLs or URL parameters
- ❌ System logs or console output
- ❌ HTTP headers
- ❌ Browser history
- ❌ Error messages
- ❌ Code comments or documentation

### Correct URL Patterns:
```
✅ GET /api/v1/patients/{patient_uuid}        # Opaque UUID
✅ GET /api/v1/admissions/{admission_uuid}    # Surrogate key
❌ GET /api/v1/patients/{mrn}                 # PHI EXPOSURE - NEVER DO THIS
```

### MRN Handling:
- MRNs are PHI and **must be encrypted at rest**
- Use **opaque UUIDs** in all API endpoints
- MRN can be searchable/filterable internally but **never** in URL paths
- All PHI must be encrypted in transit (TLS required in production)

---

## Running Tests

```bash
# Backend tests (SQLite in-memory)
cd backend
pytest

# With PostgreSQL
TEST_DATABASE_URL=postgresql+asyncpg://localhost/flightplan_test pytest

# Run specific test
pytest tests/test_event_store.py -v

# With coverage
pytest --cov=app tests/
```

See [docs/TESTING.md](docs/TESTING.md) for comprehensive testing documentation.

---

## Key Files Explained

### Legacy Reference (DO NOT MODIFY - Reference Only)

| File | Size | Purpose |
|------|------|---------|
| `legacy-reference/core/FpCodes.py` | 8KB | **READ FIRST** - All domain enums, locations, teams, roles |
| `legacy-reference/models/Admission.py` | 41KB | **CORE MODEL** - Most business logic lives here |
| `legacy-reference/models/Patient.py` | 10KB | Patient entity with demographics, MRN handling |

### Active Implementation

| File | Purpose |
|------|---------|
| `backend/app/infrastructure/event_store.py` | Event sourcing implementation |
| `backend/app/projections/` | Read model builders (CQRS) |
| `backend/alembic/versions/` | Database migrations |
| `backend/plugins/cardiac/manifest.yaml` | Cardiac specialty plugin |

---

## Contributing

We follow strict development practices to maintain code quality and security:

1. **Evidence-Based Coding** - Always find existing patterns before implementing
2. **Type Safety** - Run `mypy` after every 20 lines
3. **Test Coverage** - Write tests before claiming "done"
4. **PHI Compliance** - Triple-check any PHI-handling code
5. **No Breaking Changes** - Never remove features without explicit permission

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed workflow, coding standards, and PR process.

---

## Architecture Highlights

### Event Sourcing + CQRS
- All state changes captured as immutable events
- Separate write models (event store) and read models (projections)
- Full audit trail for compliance and debugging
- Time-travel queries for historical analysis

### Multi-Tenancy
- Hospital/organization-level isolation
- Tenant-specific feature flags and branding
- Row-level security in database
- Tenant resolution via header or subdomain

### Plugin Architecture
- Specialty-specific workflows (cardiac, orthopedic, etc.)
- Each plugin defines procedures, risk models, data fields
- Hot-loadable without core code changes
- Isolated configuration and dependencies

---

## License

**Proprietary** - Copyright © 2026 FlightPlan Enterprise. All rights reserved.

---

## Support & Contact

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: All docs in `/docs` directory
- **Architecture Questions**: See [docs/architecture/](docs/architecture/)

---

**For AI Coding Assistants**: See [CLAUDE.md](CLAUDE.md) for project-specific guidelines, domain context, and evidence-based coding requirements.
