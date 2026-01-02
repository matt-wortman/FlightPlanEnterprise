# FlightPlan v2.0 Complete Rebuild Plan

**Last Updated:** 2026-01-02

## Overview

This plan outlines a complete rebuild of FlightPlan with a modern, secure tech stack. We prioritize starting fresh over adapting legacy code where the technical debt is too high.

**Philosophy**: One section at a time, with real tests proving success before moving on.

---

## Local Development Mode

**Important**: We're developing on a local machine without access to external services initially.

### What's Suspended During Development:
- **Azure AD Authentication** → Use mock auth with configurable test user
- **Azure Blob Storage** → Use local filesystem storage initially
- **CI/CD Pipelines** → Manual testing, add automation later
- **Production Database** → Use SQLite or local PostgreSQL

### Mock Authentication Strategy:
```python
# backend/app/core/auth.py
import os
from typing import Optional

class MockUser:
    def __init__(self, username: str = "dev_user", role: str = "admin"):
        self.username = username
        self.role = role
        self.credentials = "MD"  # Default occupation

def get_current_user():
    if os.getenv("FLIGHTPLAN_ENV") == "local":
        return MockUser(
            username=os.getenv("FP_LOCAL_USER", "dev_user"),
            role=os.getenv("FP_LOCAL_ROLE", "admin"),
        )
    # Production: Azure AD integration
    return get_azure_ad_user()
```

### Local Storage Strategy:
```python
# backend/app/services/storage.py
import os

def get_storage_backend():
    if os.getenv("FLIGHTPLAN_ENV") == "local":
        return LocalFileStorage(path="./uploads")
    return AzureBlobStorage(connection_string=os.getenv("BLOB_STORAGE_CONNECT"))
```

### Environment Configuration:
```bash
# .env.local (for development)
FLIGHTPLAN_ENV=local
DATABASE_URL=sqlite:///./flightplan_dev.db  # or postgresql://localhost/flightplan
FP_LOCAL_USER=dev_user
FP_LOCAL_ROLE=admin
FP_LOCAL_OCCUPATION=MD
```

---

## Pre-Work: Update Project CLAUDE.md

**Why**: The project CLAUDE.md is missing critical coding rules from your master file.

**What to add**:
- Three-Evidence Rule (contextual, type, execution evidence)
- Enforcement checklist
- Red flags for bad practices
- Rules about asking before coding/testing
- Database protection rules
- Context7 usage requirement

**Test of Success**: CLAUDE.md contains all mandatory protocols from master file.

---

## Phase 1: Project Setup & Infrastructure (Start Fresh)

### 1.1 Create New Project Structure

**Decision: START FRESH** - The existing structure mixes concerns and has no type safety.

```
flightplan-v3/
├── backend/                    # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── core/              # Config, security, deps
│   │   └── tests/             # pytest tests
│   ├── alembic/               # DB migrations
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                   # Next.js 14 + TypeScript
│   ├── src/
│   │   ├── app/               # App router pages
│   │   ├── components/        # React components
│   │   ├── lib/               # Utilities
│   │   ├── hooks/             # Custom hooks
│   │   └── types/             # TypeScript types
│   ├── __tests__/             # Jest/Vitest tests
│   ├── package.json
│   └── Dockerfile
├── shared/                     # Shared types/schemas
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

### 1.2 Tech Stack Selection

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend API | FastAPI | Type hints, async, auto-docs, Pydantic |
| ORM | SQLAlchemy 2.0 | Modern async support, type safety |
| Migrations | Alembic | Industry standard |
| Frontend | Next.js 14 | App router, RSC, built-in routing |
| UI Framework | React 18 + TypeScript | Hooks, concurrent features |
| Styling | Tailwind CSS | Utility-first, no CSS files |
| Charts/Timeline | Recharts or D3.js | Rebuild from scratch |
| State | Zustand or React Query | Simpler than Redux |
| Testing | pytest + Vitest | Backend + Frontend |
| Auth | Mock auth (local) → Azure AD (prod) | Suspend external auth during dev |

### Tests of Success - Phase 1

```bash
# 1. Backend starts and serves health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# 2. Frontend builds without errors
cd frontend && npm run build
# Expected: Build successful, 0 TypeScript errors

# 3. Database connection works
cd backend && pytest tests/test_db_connection.py
# Expected: All tests pass

# 4. Docker compose starts all services
docker-compose up -d && docker-compose ps
# Expected: All containers running
```

---

## Phase 2: Database Layer (SQLAlchemy Migration)

### 2.1 SQLAlchemy Models

**Decision: START FRESH** - Current models have 80+ SQL injection vulnerabilities.

**Priority Order** (define models in this order due to relationships):
1. `User` - authentication
2. `Patient` - core entity
3. `Admission` - links to Patient
4. `LocationStep` - links to Admission
5. `LocationRisk` - links to LocationStep
6. `Annotation` - links to Admission
7. `Feedback` - links to Admission
8. `Conference` - links to Admission
9. `CourseCorrection` - links to Admission
10. `Attachment` - links to multiple entities
11. `ContinuousTherapy` - links to Admission
12. `BedsideProcedure` - links to LocationStep

**Key Files to Create**:
- `backend/app/models/patient.py`
- `backend/app/models/admission.py`
- `backend/app/models/location.py`
- `backend/app/models/events.py` (annotations, feedback, conferences)
- `backend/app/models/attachments.py`

### 2.2 Pydantic Schemas

**Purpose**: Request/response validation, replacing unsafe JSON-in-string patterns.

```python
# Example: backend/app/schemas/patient.py
class PatientBase(BaseModel):
    first_name: str
    last_name: str
    dob: date

class PatientCreate(PatientBase):
    mrn: str  # Medical Record Number

class PatientResponse(PatientBase):
    mrn: str
    admissions: list[AdmissionSummary]

    class Config:
        from_attributes = True
```

### 2.3 Database Migration Strategy

1. Create SQLAlchemy models matching existing schema
2. Generate Alembic migration from existing DB
3. Test with copy of production data
4. Run migrations on dev, then staging, then prod

### Tests of Success - Phase 2

```bash
# 1. All models defined and import without error
cd backend && python -c "from app.models import *; print('Models OK')"
# Expected: "Models OK"

# 2. Alembic migration generates correctly
alembic revision --autogenerate -m "initial"
# Expected: Migration file created

# 3. Migration runs against test DB
alembic upgrade head
# Expected: 0 errors, tables created

# 4. CRUD operations work with parameterized queries
pytest tests/test_crud.py -v
# Expected: All CRUD tests pass

# 5. SQL injection test FAILS (proves protection works)
pytest tests/test_sql_injection.py -v
# Expected: Malicious input rejected, no data breach
```

---

## Phase 3: Backend API (FastAPI)

### 3.1 API Routes

**Decision: START FRESH** - Dash callback system is not maintainable.

**Route Structure**:
```
/api/v1/
├── /auth
│   ├── GET /me                    # Current user
│   └── POST /logout               # Clear session
├── /patients
│   ├── GET /                      # List (paginated)
│   ├── POST /                     # Create
│   ├── GET /{mrn}                 # Get by MRN
│   ├── PUT /{mrn}                 # Update
│   └── DELETE /{mrn}              # Delete (soft)
├── /patients/{mrn}/admissions
│   ├── GET /                      # List admissions
│   ├── POST /                     # Create admission
│   ├── GET /{adm_id}              # Get admission detail
│   └── PUT /{adm_id}              # Update admission
├── /admissions/{adm_id}/timeline
│   ├── GET /                      # Get timeline data
│   ├── POST /location-steps       # Add location
│   ├── POST /annotations          # Add annotation
│   ├── POST /feedback             # Add feedback
│   └── POST /conferences          # Add conference
├── /attachments
│   ├── POST /upload               # Upload to Azure Blob
│   ├── GET /{id}                  # Get attachment
│   └── DELETE /{id}               # Delete attachment
└── /health
    └── GET /                      # Health check
```

### 3.2 Service Layer

**Purpose**: Business logic separate from routes.

**Key Services**:
- `PatientService` - patient CRUD + search
- `AdmissionService` - admission management
- `TimelineService` - graph data generation
- `AttachmentService` - Azure Blob operations
- `AuthService` - Mock auth locally, Azure AD in production

### Tests of Success - Phase 3

```bash
# 1. API docs auto-generate
curl http://localhost:8000/docs
# Expected: Swagger UI loads with all endpoints

# 2. Patient list returns paginated data
curl "http://localhost:8000/api/v1/patients?page=1&per_page=20"
# Expected: JSON with patients array and pagination metadata

# 3. Patient creation validates input
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{"mrn": "", "first_name": "Test"}'
# Expected: 422 error with validation message

# 4. Timeline data matches expected format
pytest tests/test_timeline_api.py -v
# Expected: All timeline tests pass

# 5. Load test passes
locust -f tests/load_test.py --headless -u 50 -r 10 -t 60s
# Expected: <200ms p95 latency, 0 errors
```

---

## Phase 4: Frontend Foundation (Next.js)

### 4.1 Project Setup

**Decision: START FRESH** - Dash/React hybrid is unmaintainable.

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app
```

**Key Configuration**:
- TypeScript strict mode
- ESLint + Prettier
- Path aliases (`@/components`, `@/lib`)
- API route proxying to backend

### 4.2 Core Pages

```
src/app/
├── layout.tsx              # Root layout with nav
├── page.tsx                # Redirect to /patients
├── patients/
│   ├── page.tsx            # Patient list
│   └── [mrn]/
│       └── page.tsx        # Patient detail
├── login/
│   └── page.tsx            # Azure AD redirect
└── api/
    └── auth/               # Auth API routes
```

### 4.3 Component Library

**Reusable Components**:
- `PatientTable` - sortable, filterable, paginated
- `PatientCard` - summary view
- `TimelinePlaceholder` - placeholder until Phase 5
- `Modal` - generic modal wrapper
- `Form` sections - input, date, select, file upload

### Tests of Success - Phase 4

```bash
# 1. Build succeeds with 0 TypeScript errors
npm run build
# Expected: Build successful

# 2. Type check passes
npm run type-check  # or: npx tsc --noEmit
# Expected: 0 errors

# 3. Patient list renders with mock data
npm run test -- PatientList.test.tsx
# Expected: Tests pass

# 4. Navigation works
npm run test:e2e -- navigation.spec.ts
# Expected: All routes accessible

# 5. Lighthouse score acceptable
npx lighthouse http://localhost:3000 --output=json
# Expected: Performance > 80, Accessibility > 90
```

---

## Phase 5: Timeline Component (Rebuild)

### 5.1 Analysis

**Decision: START FRESH** - 2,811-line class component is unmaintainable.

**Current Issues**:
- Class-based React (outdated)
- No TypeScript
- 50+ methods in one file
- No tests
- 1.3MB bundle size

**New Architecture**:
```
components/timeline/
├── Timeline.tsx           # Main container
├── TimelineChart.tsx      # Recharts wrapper
├── TimelineBrush.tsx      # Zoom control
├── TimelineTooltip.tsx    # Hover info
├── TimelineMenu.tsx       # Options menu
├── TimelineMarkers.tsx    # Event markers
├── hooks/
│   ├── useTimelineData.ts # Data transformation
│   ├── useTimelineZoom.ts # Zoom state
│   └── useTimelineEvents.ts # Event handlers
├── types.ts               # TypeScript interfaces
└── __tests__/
    ├── Timeline.test.tsx
    └── hooks.test.ts
```

### 5.2 Feature Parity Checklist

Must support all existing features:
- [ ] Location timeline (y-axis: locations, x-axis: dates)
- [ ] Risk status markers
- [ ] Annotation points
- [ ] Feedback/rating markers
- [ ] Conference markers
- [ ] Zoom/pan with brush
- [ ] Tooltip on hover
- [ ] Click to edit
- [ ] Export to image
- [ ] Responsive sizing
- [ ] Loading states

### Tests of Success - Phase 5

```bash
# 1. Component renders with sample data
npm run test -- Timeline.test.tsx
# Expected: All tests pass

# 2. TypeScript types are complete
npx tsc --noEmit src/components/timeline/**/*.ts
# Expected: 0 errors

# 3. Bundle size reduced
npm run build && npm run analyze
# Expected: Timeline chunk < 200KB (down from 1.3MB)

# 4. Visual regression test
npm run test:visual -- timeline.spec.ts
# Expected: No unexpected visual changes

# 5. Interaction tests pass
npm run test:e2e -- timeline-interactions.spec.ts
# Expected: Click, hover, zoom all work

# 6. Performance acceptable
npm run lighthouse -- /patients/TEST001
# Expected: No CLS issues, LCP < 2.5s
```

---

## Phase 6: Integration & Data Migration

### 6.1 API Integration

- Connect frontend to backend API
- Implement authentication flow
- Add error handling and loading states

### 6.2 Data Migration

- Export existing data
- Transform to new schema format
- Import with validation
- Verify data integrity

### Tests of Success - Phase 6

```bash
# 1. End-to-end patient workflow
npm run test:e2e -- patient-workflow.spec.ts
# Expected: Create, view, edit, delete all work

# 2. Data migration completeness
python scripts/verify_migration.py
# Expected: 100% records migrated, 0 data loss

# 3. Authentication works
npm run test:e2e -- auth.spec.ts
# Expected: Login, session, logout all work

# 4. Production smoke test
./scripts/smoke_test.sh https://staging.flightplan.app
# Expected: All critical paths pass
```

---

## Phase 7: Cleanup & Documentation

### 7.1 Remove Legacy Code

- Archive old FlightPlan2 directory
- Remove unused dependencies
- Clean up docker files

### 7.2 Documentation

- Update README.md
- API documentation (auto-generated)
- Deployment guide
- Developer onboarding guide

### Tests of Success - Phase 7

```bash
# 1. No references to old code
grep -r "FlightPlan2" . --exclude-dir=archive
# Expected: No results

# 2. All tests pass
npm run test && cd backend && pytest
# Expected: 100% pass rate

# 3. Production deployment succeeds
./deploy.sh production
# Expected: Deployment successful, health checks pass
```

---

## Summary: What to Keep vs Rebuild

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Backend Framework | **REBUILD** (FastAPI) | Dash callbacks are unmaintainable |
| Database Layer | **REBUILD** (SQLAlchemy) | 80+ SQL injection vulnerabilities |
| Frontend Framework | **REBUILD** (Next.js) | Dash/React hybrid is awkward |
| Timeline Component | **REBUILD** (React hooks) | 2,811-line class is unmaintainable |
| Authentication | **KEEP** pattern | Azure AD works, just modernize code |
| Business Logic | **EXTRACT** & adapt | Core domain knowledge is valuable |
| Database Schema | **KEEP** | Minimize data migration risk |
| Stored Procedures | **KEEP** temporarily | Migrate to ORM over time |
| Azure Blob Storage | **KEEP** | Works fine, update client code |

---

## Decisions Made

1. **Database**: Fresh database - start with empty schema, write migration scripts to import existing data later
2. **Deployment**: Skip CI/CD for now, add later when access is available
3. **Priority**: Patient List + CRUD first - simpler, proves full stack works end-to-end
4. **Test Data**: Need to create synthetic test data for development

---

## Execution Order

Based on decisions above, here's the exact order we'll build:

### Step 1: Project Setup (Pre-Work)
- Update CLAUDE.md with Three-Evidence Rule
- Create new project structure
- Initialize backend (FastAPI + SQLAlchemy)
- Initialize frontend (Next.js + TypeScript)
- Docker compose for local dev
- **Test**: Both servers start, health endpoints work

### Step 2: Database Models
- Define SQLAlchemy models (Patient, Admission, etc.)
- Set up Alembic migrations
- Create test database
- **Test**: Models create tables, basic CRUD works

### Step 3: Synthetic Test Data
- Create data generation scripts
- Generate realistic patient/admission data
- Seed database with test data
- **Test**: Database has 50+ test patients with full data

### Step 4: Backend API - Patient Endpoints
- Patient list (paginated, filterable)
- Patient CRUD operations
- Pydantic schemas for validation
- **Test**: All patient endpoints work via curl/Swagger

### Step 5: Frontend - Patient List
- Patient list page with table
- Pagination, search, filters
- Connect to backend API
- **Test**: Patient list renders, search works

### Step 6: Frontend - Patient Detail
- Patient detail page
- Admission list view
- Basic forms for editing
- **Test**: Can view and edit patient data

### Step 7: Timeline Component (Later Phase)
- Rebuild as modern React hooks
- TypeScript types
- Connect to timeline API
- **Test**: Timeline renders, interactions work

### Step 8: Full Integration
- All features working together
- Data migration from old system
- Production deployment
- **Test**: End-to-end workflow passes
