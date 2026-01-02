# CLAUDE.md - FlightPlan Enterprise

This file provides guidance to Claude Code when working with this repository.

---

## Project Overview

**FlightPlan Enterprise** is a medical patient management and clinical care planning web application being rebuilt from a legacy Python/Dash application to a modern stack.

**Domain:** Healthcare (cardiac surgery care planning, multi-specialty clinical platform)
**Status:** Pre-development - architecture and reference documentation phase

### Key Documentation (Reading Order)
1. [README.md](README.md) - Project overview and directory structure
2. [docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md](docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md) - Full enterprise vision
3. [docs/LEGACY_CLAUDE_REFERENCE.md](docs/LEGACY_CLAUDE_REFERENCE.md) - Legacy system context
4. [legacy-reference/core/FpCodes.py](legacy-reference/core/FpCodes.py) - **CRITICAL** - Domain enums, teams, locations, access roles

---

## CRITICAL: PHI Security Requirements

### Protected Health Information (PHI) Rules - HIPAA Compliance

**NEVER expose patient PHI in:**
- URLs or URL parameters
- System logs or console output
- HTTP headers
- Browser history
- Error messages returned to clients
- Code comments or documentation

**PHI must be:**
- Encrypted at rest (database storage)
- Encrypted in motion (TLS + application-level encryption for identifiers)
- Accessed only through opaque, non-identifying tokens in URLs

**MRN (Medical Record Number) Handling:**
- MRNs are PHI and must NEVER appear in plain text in URLs
- Use opaque identifiers (UUID or surrogate keys) in all API endpoints
- MRN can be searchable/filterable but never the URL path parameter

**Correct URL patterns:**
```
GET /api/v1/flightplans/{admission_uuid}     # Opaque ID
GET /api/v1/patients/{patient_uuid}          # Surrogate key
GET /api/v1/patients/{mrn}                   # NEVER - PHI exposure
```

---

## Target Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14+ / TypeScript / Tailwind | React framework with SSR |
| Backend | Python 3.12 / FastAPI / SQLAlchemy 2.0 | API and business logic |
| Database | PostgreSQL 16 (prod) / SQLite (dev) | Primary datastore |
| Auth | Azure AD (prod) / Mock auth (dev) | Identity management |
| Messaging | Kafka | Event streaming (enterprise) |

---

## Core Domain Concepts

### Patient -> Admission -> FlightPlan Hierarchy
```
Patient (identified by MRN - but MRN is PHI, use surrogate ID)
    |
    +-- has many -> Admissions (each = one hospital stay)
                        |
                        +-- has one -> FlightPlan (care plan for that admission)
```

### Key Domain Terms (see FpCodes.py)
- **Admission**: A single hospital stay for a patient
- **FlightPlan**: The care plan/timeline for an admission
- **Location Step**: Patient movement (ICU -> Floor -> Discharge)
- **Location Risk**: Risk assessment at a location
- **Conference**: Multi-disciplinary team meeting about a patient
- **Annotation**: Clinical note or marker on the timeline
- **Trajectory**: The path showing patient location over time

---

## Evidence-Based Coding Protocol

### The Three-Evidence Rule (MANDATORY)

**1. CONTEXTUAL EVIDENCE (BEFORE writing code)**
```bash
# Find similar implementations in legacy or docs:
grep -r "similar_pattern" legacy-reference/
cat docs/data-model/DATABASE_SCHEMA_DUMP.sql
# NEVER assume data formats - find them in existing code
```

**2. TYPE EVIDENCE (WHILE writing code)**
```bash
# After EVERY 20 lines of code:
npm run type-check   # Frontend (TypeScript)
mypy app/            # Backend (Python)
# Fix ALL errors before continuing
```

**3. EXECUTION EVIDENCE (AFTER writing code)**
```bash
# Before claiming "done" - PROVE it works:
pytest tests/        # Backend tests
npm test             # Frontend tests
# Show actual output
```

### Enforcement Checklist
- [ ] Found and read similar examples in legacy-reference/ or docs/
- [ ] Ran type-check and pasted clean output
- [ ] Executed the code/test and pasted working output
- [ ] NO assumptions - only facts from the codebase

---

## Rules for This Project

### Planning & Permissions
- Think first and get permission to start coding
- Plan before coding and consider multiple approaches
- Check existing documentation before implementing
- Use context7 MCP to get correct documentation for packages and libraries
- Always ask before running tests - explain what, why, and expected outcomes

### Code Quality
- Don't create bandaid fixes - identify root problems and implement best-practices fixes
- Never try to correct an error until you understand the root problem
- Always use direct tests of functionality, never indirect tests
- Write general-purpose solutions using standard tools
- Never hard-code test values or add hacky helper scripts
- **Always use the most recent stable versions of packages** while ensuring compatibility with existing project dependencies - check context7 or package documentation for latest stable versions

### Safety
- NEVER remove existing features or functionality without explicit permission
- Don't destroy databases or delete data without permission and explicit description
- When modifying PHI-handling code, triple-check for security implications

---

## Project Structure

```
FlightPlanEnterprise/
├── CLAUDE.md                    # This file - AI coding guidelines
├── README.md                    # Project overview
├── PROJECT_PLAN.md              # Implementation planning (create when starting dev)
├── docs/
│   ├── architecture/            # System design, rebuild plans
│   │   └── ENTERPRISE_ARCHITECTURE_PLAN.md  # Full enterprise vision
│   ├── domain/                  # Clinical/medical domain knowledge
│   ├── data-model/              # Database schema and relationships
│   └── sample-data/             # CSV files for testing
└── legacy-reference/
    ├── core/                    # Key Python modules (config, codes, database)
    │   └── FpCodes.py           # CRITICAL - all domain enums
    ├── models/                  # Domain model classes
    │   └── Admission.py         # LARGEST MODEL - core business logic
    └── sql/                     # SQL schema and query templates
```

---

## Test Organization

Tests and docs created at EVERY level. Directory naming convention:
```
{project_root}/tests-{Function}-{Phase}-{Task}-{MM_DD_YYYY}_{HHMM}/
```
Example: `tests-Backend-PatientAPI-crud_endpoints-01_02_2025_1436`

---

## Code Locking Principle

When working on a specific Function (Frontend, Backend, Data, etc.):
- **LOCK code for Functions you are NOT working on** - do not touch
- If cross-Function changes are required:
  1. Declare upfront BEFORE starting work
  2. Document which Functions will be affected
  3. Plan rollback/mitigation strategy
  4. Get explicit user acknowledgment

---

## Quick Reference Commands

### When Development Starts
```bash
# Backend (FastAPI)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (Next.js)
cd frontend
npm install
npm run dev  # Port 3000
```

### Type Checking
```bash
# Backend
mypy app/ --strict

# Frontend
npm run type-check
# or: npx tsc --noEmit
```

### Testing
```bash
# Backend
pytest tests/ -v

# Frontend
npm test
```

---

*This CLAUDE.md inherits from ~/.claude/CLAUDE.md and adds project-specific context.*
