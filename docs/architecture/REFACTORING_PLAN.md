# FlightPlan v2.0 Refactoring Plan

**Date:** 2025-12-18
**Last Updated:** 2026-01-02
**Purpose:** Simplify technology stack while preserving all functionality

---

## Executive Summary

FlightPlan v2.0 is a medical patient tracking application for cardiac care patients, built with Dash (Python web framework) and custom React components. The application tracks patient journeys through hospital locations (CTOR, CICU, ACCU, Cath, etc.) with timeline visualization, clinical events, feedback/ratings, and document attachments.

**Total Codebase Size:** ~20,500 lines of Python + 2,800 lines of React (Timeline component)

---

## Part 1: Functional Analysis - What The App Actually Does

### Core Features

1. **Patient Management**
   - Create/edit patient records (MRN, name, DOB, sex, diagnosis)
   - Track patient admissions with surgery dates and review dates
   - Mark patients as deceased or discharged
   - CrossCheck (high-risk) patient flagging

2. **Timeline Visualization**
   - Visual graph showing patient journey through hospital locations
   - Location tracking: Pre-op, CTOR, CICU, ACCU, Cath, DC (Discharge)
   - Risk status tracking (Intubated, Extubated, Procedure, Discharged)
   - Interactive timeline with zoom, pan, and tooltips

3. **Clinical Events**
   - Location steps (patient movement between units)
   - Location risks (respiratory status changes)
   - Bedside procedures
   - Clinical annotations (Chest Tubes, Inotropes, Cardiac Arrest, etc.)

4. **Continuous Therapy Tracking**
   - ECMO therapy
   - Other continuous therapies

5. **Feedback System**
   - Performance ratings
   - Outcome tracking
   - Suggested edits
   - Graph visibility controls

6. **Conference Management**
   - Conference scheduling and tracking
   - Action items
   - Notes and attachments

7. **Document Management**
   - File attachments (PDFs, images)
   - Azure Blob Storage integration
   - Document viewer modal
   - Thumbnail generation

8. **User Management**
   - Role-based access (credentials levels 1-4)
   - Azure AD authentication
   - User occupation tracking

9. **Patient List**
   - Sortable/filterable patient list
   - Search by name or MRN
   - Filter by status, location, on-track status
   - Pagination

### Data Entities and Relationships

```
Patient (MRN)
  └── Admission (ADM)
        ├── LocationStep (LocationStepID)
        │     └── LocationRisk (LocationRiskID)
        │     └── BedsideProcedure (BedsideProcedureID)
        ├── Annotation (AnnotationID)
        ├── Feedback (FeedbackID)
        ├── Conference (ConferenceID)
        ├── CourseCorrection (course_correct_id)
        ├── ContinuousTherapy (CtID)
        └── Attachment (AttachmentID)

Users (username) - standalone
```

---

## Part 2: Identified Complexity and Inefficiencies

### 2.1 Hardcoded Values (CRITICAL)

**File: `/FlightPlan2/FpCodes.py`**
- Medical team names hardcoded (lines 173-239):
  - `cath_interventionalist_team_items`: Batlivala, Hirsch, Shahanavaz
  - `accu_attending_team_items`: 17 doctor names
  - `cicu_attending_team_items`: 11 doctor names
  - `surgical_team_items`: 7 surgeon names
  - `anesthesiologist_team_items`: 14 names
- Location colors hardcoded (lines 26-83)
- Risk statuses hardcoded (lines 10-24)
- Respiratory support options hardcoded (lines 241-273)

**File: `/FlightPlan2/validation/clinical.py`**
- Clinical event codes hardcoded (CTO, CTP, IO, CA, MRT, etc.)
- Symbols and colors hardcoded for each code

**File: `/FlightPlan2/dbSetup.py`**
- User credentials hardcoded (lines 309-343)
- Includes email addresses and credential levels

### 2.2 Framework Complexity

**Dash Callback System Issues:**
- Complex callback chains with 10+ inputs/outputs (`FP2_PatientsTab.py` lines 20-62)
- Manual state management via `dcc.Store` components
- Heavy use of `encrypt`/`decrypt` for session data
- Callback registration scattered across multiple files
- No clear separation between presentation and business logic

**Custom React Component:**
- `Timeline.react.js`: 2,811 lines of complex React code
- Built with older patterns (class components, not hooks)
- Complex coordinate transformations for timeline visualization
- Tightly coupled to Dash component interface
- Uses Recharts library but with heavy customization

### 2.3 Database Layer Issues

**Raw SQL Throughout:**
- SQL strings concatenated inline (SQL injection risk)
- No ORM - manual schema definitions in `FpCodes.py`
- Example from `Admission.py` line 74-93: 17 lines of manual SQL string building
- Stored procedures used but SQL still manually constructed
- Multiple database interfaces supported (MySQL, SQLite, SQL Server) but abstractions leak

**N+1 Query Problems:**
- `Patient` class loads all admissions on init
- `Admission` class makes 6+ separate database calls on init:
  - `loadLocationStepsAndTimeline()`
  - `loadCourseCorrections()`
  - `loadAnnotations()`
  - `loadFeedbacks()`
  - `loadConferences()`
  - `loadAttachments()`

### 2.4 Architecture Issues

**Mixed Concerns:**
- Model classes contain database operations (`Patient.addPatientToDatabase()`)
- UI components generate SQL queries
- Business logic scattered across utils, models, and components

**Caching Complexity:**
- Flask session-based caching (`cache_manager.py`)
- Global `cm` CallbackManager
- Multiple levels of patient caching with unclear invalidation

**Configuration Scattered:**
- `FpConfig.py` for database and env vars
- `FpCodes.py` for schemas and domain constants
- `validation/*.py` for dropdown options
- Environment variables mixed with code defaults

### 2.5 Code Duplication

- Similar patterns in location handling: `ACCU.py`, `CICU.py`, `CTOR.py`, `Cath.py`, `DC.py`, `PreOp.py`
- Duplicate "TODO: What to do here?" in all location files (line 126/similar)
- Date formatting repeated throughout
- SQL query patterns duplicated across models

---

## Part 3: Proposed Simplified Architecture

### 3.1 Recommended Technology Stack

| Layer | Current | Proposed | Justification |
|-------|---------|----------|---------------|
| **Frontend** | Dash + Custom React | Next.js 14 + React 18 | Modern SSR, better DX, larger ecosystem |
| **UI Components** | Custom + Bootstrap | shadcn/ui + Tailwind | Consistent, accessible, customizable |
| **Charts** | Custom Recharts wrapper | Recharts or visx | Use library directly, simpler integration |
| **State Management** | Dash stores + Flask session | React Query + Zustand | Better caching, cleaner state |
| **API Layer** | Dash callbacks | FastAPI + Pydantic | Type-safe, async, better docs |
| **ORM** | Raw SQL | SQLAlchemy 2.0 | Modern async, type hints, migrations |
| **Database** | SQL Server | PostgreSQL or keep SQL Server | Both work with SQLAlchemy |
| **Auth** | Azure AD (manual) | NextAuth.js with Azure AD | Simplified auth flow |
| **File Storage** | Azure Blob (direct) | Azure Blob via FastAPI | Centralized file handling |

### 3.2 Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ Pages/Routes │ │ Components  │ │ Timeline Component  │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│                         │                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              React Query + Zustand                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────│────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────│────────────────────────────────┐
│                     FastAPI Backend                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │  API Routes  │ │  Services   │ │    Pydantic Models  │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│                         │                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           SQLAlchemy 2.0 ORM Layer                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────│────────────────────────────────┘
                             │
┌────────────────────────────│────────────────────────────────┐
│            SQL Server / PostgreSQL                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Database Tables (with proper foreign keys)           │   │
│  │ + Configuration Tables (teams, locations, etc.)      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 4: Migration Plan

### Phase 1: Quick Wins (2-3 weeks)

**Goal:** Reduce technical debt without changing architecture

#### 1.1 Move Hardcoded Values to Database
- Create configuration tables:
  ```sql
  CREATE TABLE team_members (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    team_type VARCHAR(50), -- 'surgeon', 'anesthesia', 'cicu', 'accu', 'cath'
    is_active BIT DEFAULT 1
  );

  CREATE TABLE locations (
    id INT PRIMARY KEY,
    category VARCHAR(50),
    labels VARCHAR(500), -- JSON array
    heading VARCHAR(100),
    line_color VARCHAR(50),
    ecmo_color VARCHAR(50),
    annotation_color VARCHAR(50)
  );

  CREATE TABLE risk_statuses (
    id INT PRIMARY KEY,
    category VARCHAR(50),
    level INT,
    values VARCHAR(500) -- JSON array
  );

  CREATE TABLE clinical_codes (
    code VARCHAR(10) PRIMARY KEY,
    description VARCHAR(100),
    symbol_type VARCHAR(20),
    symbol_value VARCHAR(50),
    color VARCHAR(50),
    priority INT
  );
  ```

**Files to modify:**
- `/FlightPlan2/FpCodes.py` - Replace hardcoded lists with database queries
- `/FlightPlan2/validation/clinical.py` - Load from database
- `/FlightPlan2/validation/general.py` - Load dropdowns from database

**Risk:** Low - Data loading changes only
**Testing:** Verify all dropdowns populate correctly

#### 1.2 Consolidate Configuration
- Create `/FlightPlan2/config/` directory
- Move all configuration to structured YAML/JSON files
- Create config loader class

**Files to create:**
- `/FlightPlan2/config/database.yaml`
- `/FlightPlan2/config/app.yaml`
- `/FlightPlan2/config/loader.py`

#### 1.3 Fix SQL Injection Vulnerabilities
- Replace string formatting with parameterized queries
- Example fix in `Admission.py`:
  ```python
  # Before (vulnerable):
  sql = "delete from patients where MRN = '{}'".format(self.MRN)

  # After (safe):
  sql = "DELETE FROM patients WHERE MRN = ?"
  db.sendSqlNoReturn(sql, [self.MRN])
  ```

**Files to modify:**
- `/FlightPlan2/models/Admission.py`
- `/FlightPlan2/models/Patient.py`
- `/FlightPlan2/models/LocationStep.py`
- `/FlightPlan2/models/LocationRisk.py`
- All files using `format()` with SQL

---

### Phase 2: Backend Simplification (4-6 weeks)

**Goal:** Create proper API layer with ORM

#### 2.1 Add SQLAlchemy Models
Create `/FlightPlan2/api/models/`:

```python
# /FlightPlan2/api/models/patient.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Patient(Base):
    __tablename__ = 'patients'

    mrn = Column(String(50), primary_key=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    dob = Column(DateTime, nullable=False)
    sex = Column(String(20), nullable=False)
    key_diagnosis = Column(String(500))
    deceased = Column(Boolean, default=False)
    username = Column(String(100))
    activity_date = Column(DateTime)

    admissions = relationship("Admission", back_populates="patient")
```

**Files to create:**
- `/FlightPlan2/api/models/base.py`
- `/FlightPlan2/api/models/patient.py`
- `/FlightPlan2/api/models/admission.py`
- `/FlightPlan2/api/models/location_step.py`
- `/FlightPlan2/api/models/attachment.py`
- etc.

#### 2.2 Create FastAPI Application
```python
# /FlightPlan2/api/main.py
from fastapi import FastAPI
from .routers import patients, admissions, attachments

app = FastAPI(title="FlightPlan API", version="3.0.0")

app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(admissions.router, prefix="/api/admissions", tags=["admissions"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["attachments"])
```

#### 2.3 Create Service Layer
Separate business logic from data access:

```python
# /FlightPlan2/api/services/patient_service.py
class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_patients(self, page: int, filters: PatientFilters) -> list[Patient]:
        query = select(Patient).options(selectinload(Patient.admissions))
        # Apply filters...
        return await self.db.execute(query)

    async def create_patient(self, data: PatientCreate) -> Patient:
        # Business logic...
        pass
```

**Risk:** Medium - Core data layer changes
**Testing:**
- Create parallel API alongside Dash
- Run both systems simultaneously
- Compare outputs for same operations

---

### Phase 3: Frontend Modernization (6-8 weeks)

**Goal:** Replace Dash with modern React frontend

#### 3.1 Create Next.js Application
```bash
npx create-next-app@latest flightplan-frontend --typescript --tailwind --app
```

**Structure:**
```
flightplan-frontend/
├── app/
│   ├── (auth)/
│   │   └── login/
│   ├── patients/
│   │   ├── page.tsx
│   │   └── [mrn]/
│   │       └── page.tsx
│   └── layout.tsx
├── components/
│   ├── ui/           # shadcn components
│   ├── patients/
│   │   ├── PatientList.tsx
│   │   ├── PatientCard.tsx
│   │   └── PatientFilters.tsx
│   └── timeline/
│       └── Timeline.tsx
└── lib/
    ├── api.ts        # API client
    └── types.ts      # TypeScript types
```

#### 3.2 Migrate Timeline Component
Options:
1. **Port existing component** - Extract Timeline.react.js, update to modern React
2. **Use existing library** - Consider visx, nivo, or Apache ECharts for medical timeline
3. **Build new component** - Use D3.js or vanilla Canvas for maximum control

**Recommendation:** Option 1 with modernization:
- Convert class component to functional component with hooks
- Replace Material-UI v4 with shadcn/ui
- Simplify coordinate transformation logic
- Add TypeScript types

#### 3.3 Create Patient List Page
```tsx
// app/patients/page.tsx
export default function PatientsPage() {
  const { data: patients, isLoading } = useQuery({
    queryKey: ['patients', filters],
    queryFn: () => api.getPatients(filters)
  });

  return (
    <div>
      <PatientFilters onFilterChange={setFilters} />
      <PatientList patients={patients} />
    </div>
  );
}
```

**Risk:** High - Complete UI rewrite
**Testing:**
- Feature parity checklist
- User acceptance testing
- A/B deployment option

---

### Phase 4: Final Cleanup (2-4 weeks)

#### 4.1 Remove Legacy Code
- Delete Dash application files
- Remove custom callback system
- Remove Flask-based session management

#### 4.2 Database Migrations
- Add proper foreign key constraints
- Add indexes for common queries
- Create Alembic migration scripts

#### 4.3 Documentation
- API documentation (auto-generated via FastAPI)
- Component documentation (Storybook)
- Deployment documentation

#### 4.4 Testing
- Unit tests for services
- Integration tests for API
- E2E tests with Playwright

---

## Part 5: Technology Stack Recommendation Summary

### Recommended Stack

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| Frontend Framework | Next.js | 14.x | App router, RSC, excellent DX |
| UI Components | shadcn/ui | Latest | Accessible, customizable, modern |
| Styling | Tailwind CSS | 3.x | Utility-first, consistent |
| State Management | Zustand | 4.x | Simple, performant |
| Data Fetching | TanStack Query | 5.x | Caching, deduplication |
| Backend | FastAPI | 0.100+ | Async, type-safe, auto-docs |
| ORM | SQLAlchemy | 2.0 | Async support, mature |
| Database | SQL Server | Current | Keep existing, or migrate to PostgreSQL |
| Auth | NextAuth.js | 5.x | Azure AD provider built-in |
| File Storage | Azure Blob | Current | Keep existing |
| Hosting | Azure App Service | Current | Keep existing infrastructure |

### Migration Priority

1. **Immediate (Phase 1):** Security fixes, configuration externalization
2. **Short-term (Phase 2):** API layer, reduce Dash complexity
3. **Medium-term (Phase 3):** Frontend modernization
4. **Long-term (Phase 4):** Full migration, legacy removal

### Estimated Timeline

| Phase | Duration | Resources |
|-------|----------|-----------|
| Phase 1 | 2-3 weeks | 1 developer |
| Phase 2 | 4-6 weeks | 2 developers |
| Phase 3 | 6-8 weeks | 2-3 developers |
| Phase 4 | 2-4 weeks | 1-2 developers |
| **Total** | **14-21 weeks** | |

---

## Critical Files for Implementation

1. **`/FlightPlan2/FpCodes.py`** - Contains all hardcoded domain values (teams, locations, statuses) that must be migrated to database
2. **`/FlightPlan2/models/Admission.py`** - Core business logic with 839 lines; central to understanding data relationships and must be refactored for ORM
3. **`/FlightPlan2/flight_plan_components/src/lib/components/Timeline.react.js`** - 2,811-line custom React component that needs modernization or replacement
4. **`/FlightPlan2/FpDatabase.py`** - Database abstraction layer (465 lines) that will be replaced by SQLAlchemy
5. **`/FlightPlan2/FP2_PatientsTab.py`** - Example of Dash callback complexity (251 lines) showing patterns to be eliminated

---

This refactoring plan provides a clear path from the current complex Dash-based architecture to a modern, maintainable stack while preserving all existing functionality. The phased approach minimizes risk and allows for incremental validation at each step.
