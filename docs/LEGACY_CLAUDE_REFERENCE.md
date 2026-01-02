# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# MANDATORY EVIDENCE-BASED CODING PROTOCOL

**NO CODE SUBMISSION WITHOUT THREE EVIDENCES - NO EXCEPTIONS**

## The Three-Evidence Rule (MANDATORY)

### 1. CONTEXTUAL EVIDENCE (BEFORE writing code)
```bash
# ALWAYS do this FIRST - find 3 similar implementations:
grep -r "similar_pattern" --include="*.py"
cat path/to/existing/implementation.py
# NEVER assume data formats - always FIND them in existing code
```

### 2. TYPE EVIDENCE (WHILE writing code)
```bash
# After EVERY 20 lines of code:
# For Python: run type checker or linter
# For TypeScript: npx tsc --noEmit
# Fix ALL errors before continuing
```

### 3. EXECUTION EVIDENCE (AFTER writing code)
```bash
# Before claiming "done" - PROVE it works:
pytest tests/        # Run tests
python test_script.py    # Execute test script
# Show actual output
```

## ENFORCEMENT CHECKLIST

Before submitting ANY code, you MUST:
- [ ] Found and read 3 similar examples in the codebase
- [ ] Ran type-check/linter and pasted clean output
- [ ] Executed the code/test and pasted working output
- [ ] NO assumptions - only facts from the codebase

## RED FLAGS - STOP IMMEDIATELY IF YOU:
- Write >20 lines without running type-check
- Use placeholder/example data instead of real formats
- Say "should work" instead of "does work"
- Submit code without execution proof
- Make assumptions about data formats/types

## The Mindset Shift
- **OLD:** Generate code → Hope it works
- **NEW:** Research → Write → Verify → Prove → Submit

**TREAT EVERY SUBMISSION AS PRODUCTION-READY CODE**

---

## Problem-Solving Principles
- Don't create bandaid fixes, always identify the source of problems and implement a best-practices fix
- Never try to correct an error until you understand the root problem
- Always use direct tests of functionality, never indirect tests
- New tests stored in tests directory and each test stores results in its own subfolder

## Rules
- Think first and get permission to start coding
- Plan before coding and consider multiple approaches to a problem
- Check for code documentation in a project when thinking and planning
- Search the internet to find solutions to problems, do not invent solutions until you have searched
- Always ask before starting coding
- Always ask before running tests - include why we're running it, what will be tested, and how results provide understanding
- Don't ever destroy databases or delete them without permission and specifically describing what will happen
- Use context7 to get correct documentation for code, packages, and libraries
- **NEVER remove existing features or functionality without explicit permission** - this includes UI components, drawer panels, toggles, buttons, or any working functionality. Always ask before removing something that was previously working.

## Test Integrity
- Write general-purpose solutions using standard tools
- Never hard-code test values or add hacky helper scripts just to satisfy tests
- If tests look wrong, report the issue instead of working around them

---

## Project Overview

FlightPlan is a medical patient management and clinical care planning web application for managing patient admissions, clinical events, conferences, and surgical care planning.

**STATUS: REBUILDING** - See `docs/REBUILD_PLAN.md` for the complete rebuild plan.

---

## CRITICAL: PHI Security & Data Model

### PHI (Protected Health Information) Requirements

**NEVER expose patient PHI in:**
- URLs or URL parameters
- System logs
- HTTP headers
- Browser history
- Error messages returned to clients

**PHI must be:**
- Encrypted at rest (database storage)
- Encrypted in motion (TLS + application-level encryption for identifiers)
- Accessed only through opaque, non-identifying tokens in URLs

**MRN Handling:**
- MRNs (Medical Record Numbers) are PHI and must NEVER appear in plain text in URLs
- The legacy system encrypts MRNs using Fernet before placing them in URLs (see `FlightPlan2/utils/FP2_Utilities.py`)
- v3 must use opaque identifiers (UUID or surrogate keys) in all API endpoints and URLs
- MRN can be a searchable/filterable field but must not be the URL path parameter

### Core Data Model

```
Patient (identified by MRN - but MRN is PHI, use surrogate ID in URLs)
    │
    └── has many → Admissions (each admission = one hospital stay)
                       │
                       └── has one → FlightPlan (the care plan for that admission)
```

**Key relationships:**
- One Patient can have multiple Admissions (readmissions, different specialties)
- Each Admission has exactly ONE FlightPlan
- FlightPlan is the unit of clinical workflow - it tracks events, locations, procedures for a single admission
- **URL identifiers must be based on Admission ID (or a surrogate), not MRN**

**Example correct URL patterns:**
```
GET /api/v1/flightplans/{admission_id}     ✓ (opaque ID)
GET /api/v1/patients/{patient_uuid}        ✓ (surrogate key)
GET /api/v1/patients/{mrn}                 ✗ NEVER (PHI exposure)
```

---

## Current Tech Stack (Legacy - Being Replaced)

- **Backend**: Python 3 with Dash 2.6.1 (Plotly's reactive framework), Flask 2.1.2
- **Frontend**: Custom React 16.8.6 components compiled to Dash-compatible Python
- **Database**: SQL Server via pyodbc (also supports MySQL, SQLite)
- **Build**: Webpack 5 for React components

## New Tech Stack (v3 Rebuild)

- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Database**: SQLite (local dev) → SQL Server (production)
- **Auth**: Mock auth (local) → Azure AD (production)

## Common Commands

### Running the Legacy Application (Docker - Recommended)

Use `start-legacy.sh` to run the legacy app in Docker with SQL Server. Ports are configured to not conflict with v3 development servers.

```bash
cd FlightPlan2
./start-legacy.sh          # Start in foreground (see logs)
./start-legacy.sh -d       # Start in background (detached)
./start-legacy.sh stop     # Stop all legacy services
./start-legacy.sh status   # Show status of legacy services
./start-legacy.sh logs     # Tail logs from legacy services
```

**Port Assignments:**
| Service | Legacy Port | v3 Reserved Port |
|---------|-------------|------------------|
| Web App | 9050 | 3000 (Next.js), 8000 (FastAPI) |
| SQL Server | 11433 | 1433 |

Access legacy app at: http://localhost:9050

### Running the Legacy Application (Local Python)
```bash
cd FlightPlan2
python FlightPlan2.py
# Requires local SQL Server and environment variables configured
```

### Environment Variables
```bash
DB_SERVER=<server_address>
DB_NAME=<database_name>
DB_USER=<sql_user>
DB_PASSWORD=<sql_password>
ENCRYPTION_KEY=<fernet_key>
FLIGHTPLAN_ENV=local  # enables debug mode and .env.local loading
```

### Docker (Manual)
```bash
cd FlightPlan2
docker-compose -f docker-compose.legacy.yml up -d  # Preferred: non-conflicting ports
# OR
docker-compose up -d  # Original compose file (may conflict with v3 ports)
```

### Building React Components (Legacy)
```bash
cd FlightPlan2/flight_plan_components
npm install
npm run build
# Generates JS bundle AND Python bindings via dash-generate-components
```

### Running Tests
```bash
cd FlightPlan2
python -m pytest tests/test_dash.py
```

### Database Setup
```bash
cd FlightPlan2
python dbSetup.py  # WARNING: Drops all tables first!
# Then import: sql/backups/OFFICIAL_backup.sql
```

---

## Running FlightPlan v3 (New Application)

### Quick Start (Development)

**Recommended**: Use the v3 helper scripts (starts backend + frontend, manages PID files/logs).

```bash
# Start backend (:8000) + frontend (:3000)
bash flightplan-v3/scripts/dev-up.sh

# Stop both
bash flightplan-v3/scripts/dev-down.sh

# Restart both
bash flightplan-v3/scripts/dev-restart.sh
```

Notes:
- `scripts/dev-up.sh` starts Next.js dev using **webpack by default** (more stable). Set `FRONTEND_BUNDLER=turbopack` if you want Turbopack.
- If you see `Performance.measure: Given attribute end cannot be negative`, use webpack (default) and restart.

### Seeding the v3 DB (SQLite)

```bash
cd flightplan-v3/backend
./venv/bin/python scripts/import_csv_data.py --data-dir ../docs/data/seed_capped_54 --reset
```

If you want every admission to have a visible trajectory and in-range timeline markers, run these from repo root before reseeding:
```bash
python flightplan-v3/scripts/simulate_location_steps.py
python flightplan-v3/scripts/align_simulated_event_dates.py
```

### v3 Port Assignments
| Service | Port | URL |
|---------|------|-----|
| v3 Frontend (Next.js) | 3000 | http://localhost:3000 |
| v3 Backend (FastAPI) | 8000 | http://localhost:8000 |
| Legacy Dash App | 9050 | http://localhost:9050 |
| Legacy SQL Server | 11433 | localhost:11433 |

### v3 Architecture Overview

```
Browser Request
    ↓
Next.js Frontend (port 3000)
    ↓ (rewrites /api/* → backend)
FastAPI Backend (port 8000)
    ↓
SQLAlchemy ORM
    ↓
SQLite (dev) / SQL Server (prod)
```

**Key integration points:**

1. **Frontend → Backend**: Next.js `next.config.js` rewrites `/api/*` to `BACKEND_URL`
2. **Server Components**: Pages fetch data server-side via absolute URLs to backend
3. **Auth Flow**: Azure AD headers forwarded from frontend to backend; mock auth for local dev
4. **PHI Safety**: All URLs use UUID surrogate keys, never MRN

**Environment Variables (v3 Backend - `.env.local`):**
```bash
FLIGHTPLAN_ENV=local
DEBUG=true
DATABASE_URL=sqlite:///./flightplan_dev.db
FP_LOCAL_USER=dev_user
FP_LOCAL_ROLE=admin
FP_LOCAL_OCCUPATION=MD
CORS_ORIGINS=["http://localhost:3000"]
```

**Environment Variables (v3 Frontend):**
```bash
BACKEND_URL=http://localhost:8000
```

### v3 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/patients` | GET | List patients (paginated, searchable) |
| `/api/v1/patients/{uuid}` | GET | Get single patient |
| `/api/v1/patients` | POST | Create patient (admin) |
| `/api/v1/patients/{uuid}` | PATCH | Update patient (admin) |
| `/api/v1/patients/{uuid}` | DELETE | Delete patient (admin) |

### v3 Key Files

| File | Purpose |
|------|---------|
| `frontend/next.config.js` | API proxy rewrites |
| `frontend/src/app/patients/page.tsx` | Server-side auth fetch |
| `backend/app/main.py` | FastAPI app setup |
| `backend/app/core/auth.py` | Mock + Azure AD auth |
| `backend/app/core/database.py` | SQLAlchemy session management |
| `backend/app/api/routes/patients.py` | Patient CRUD endpoints |
| `docker-compose.yml` | Full stack configuration |

---

## Architecture

### Legacy Directory Structure (FlightPlan2/)
```
FlightPlan2/
├── App.py                  # Main Dash layout and callbacks
├── FlightPlan2.py          # Entry point
├── FpConfig.py             # Configuration (env vars, DB connections)
├── FpServer.py             # Flask/DashProxy server setup
├── FpDatabase.py           # Database abstraction layer
├── FpCodes.py              # Lookup codes, enums, access control
├── pages/                  # Dash page routes
│   ├── Patients.py         # Patient list with filtering/pagination
│   └── PatientDetail.py    # Patient view with admissions, events
├── components/
│   ├── containers/         # Data-driven UI containers
│   ├── sections/           # Reusable form sections (BaseSection pattern)
│   └── jcore/              # Clinical-specific sections
├── models/                 # Domain models (Patient, Admission, etc.)
├── utils/                  # Utilities (encryption, caching, validation)
└── flight_plan_components/ # Custom React component library
```

### New Directory Structure (flightplan-v3/)
```
flightplan-v3/
├── backend/                    # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── core/              # Config, security, deps
│   └── tests/
├── frontend/                   # Next.js 14 + TypeScript
│   ├── src/
│   │   ├── app/               # App router pages
│   │   ├── components/        # React components
│   │   └── types/             # TypeScript types
│   └── __tests__/
└── docker-compose.yml
```

## Key Patterns (Legacy)

**Dash Callbacks**: Reactive UI updates via `@app.callback` decorators connecting inputs to outputs.

**Container Pattern**: Data containers (PatientContainer, ClinicalEventContainer) encapsulate data fetching and state.

**Section Pattern**: Form sections inherit from `BaseSection` for consistent input handling.

**Database Access**: Use context manager pattern:
```python
with SqlDatabase(config) as db:
    db.query(sql)
```

**Encryption**: Sensitive data (MRNs) encrypted via Fernet. See `FP2_Utilities.py`.

## Database

The application connects to SQL Server by default. Connection configured via environment variables in `FpConfig.py`.

For local development, install Microsoft ODBC Driver 18 for SQL Server.

## Important Files

- `FpConfig.py` - All configuration, database connections, feature flags
- `FpCodes.py` - Enumeration codes, team definitions, role-based access control
- `pages/PatientDetail.py` - Main patient view (2,795 lines, core functionality)
- `models/Admission.py` - Clinical admission logic (largest model file)
- `docs/REBUILD_PLAN.md` - Complete rebuild plan with tests of success
