# PROJECT_PLAN.md - FlightPlan Enterprise

> **Single Source of Truth** for all project planning, progress tracking, and documentation.
>
> Last Updated: 2026-01-02
> Status: **Planning Phase** - Architecture & Reference Documentation

---

## Project Goals & Success Criteria

### Problem Statement
Clinical care teams managing cardiac surgery patients need a modern, scalable platform to:
- Track patient admissions and hospital stays
- Visualize patient trajectory through locations (ICU → Floor → Discharge)
- Coordinate multi-team care planning with timeline visualization
- Maintain complete audit trails for HIPAA compliance

### Success Criteria (User Perspective)

| Criterion | Measure | Target |
|-----------|---------|--------|
| **Care Coordination** | Clinicians can view patient timeline and current location | 100% of active admissions visible |
| **Data Security** | Zero PHI exposure in URLs, logs, or errors | 0 HIPAA violations |
| **Performance** | Page load time for patient detail view | < 2 seconds |
| **Reliability** | System uptime during business hours | 99.9% |
| **Extensibility** | Add a new specialty plugin without core code changes | Reference plugin + second stub validated |
| **Tenant Isolation** | Cross-tenant access prevention | 100% tenant-scoped access validated |

### Non-Goals (Explicitly Out of Scope for Enterprise Skeleton)
- Production cutover or clinical deployment
- Full legacy feature parity
- Multi-specialty production modules beyond one reference plugin
- EHR integration (Epic/Cerner)
- Mobile app development

---

## Enterprise Skeleton Delivery Plan (Baseline)

**Plan Owner:** TBD  
**Target Start:** 2026-01-05 (adjust as needed)  
**Cadence:** 2-week sprints; architecture reviews every sprint; phase-gate reviews at each milestone  

### Decision Gates (must resolve by date)

| Decision | Due (Latest) | Why It Blocks Delivery |
|----------|-------------|------------------------|
| Production database of record (PostgreSQL 16 vs SQL Server) | 2026-01-16 | Drives schema, drivers, event store design, dev/prod parity |
| Tenant isolation model (shared schema + RLS vs separate schema/db) | 2026-01-16 | Impacts schema, auth, data access patterns |
| Event store strategy (Postgres-only vs Postgres + Kafka) | 2026-01-16 | Drives infrastructure and projection architecture |
| Plugin contract v1 (manifest schema + extension model) | 2026-01-16 | Required for specialty modules and UI config |
| Auth + tenant resolution approach (OIDC + claims model) | 2026-01-16 | Required for secure multi-tenant access |
| Hosting + CI/CD target (Azure vs on-prem) | 2026-01-30 | Needed for environments, monitoring, and compliance tooling |

### Delivery Model & Governance
- **Roles:** Product Owner (requirements & priority), Tech Lead (architecture), Security/Compliance Lead (HIPAA), DevOps (env/CI/CD), Backend/Frontend leads.
- **Definition of Done (feature):** security review complete, tests added + passing, docs updated, PHI review complete, performance baselined.
- **Reporting:** weekly demo + status update; risks reviewed every sprint.
- **Change Control:** scope changes require PO + Tech Lead approval; major architectural changes require decision log entry.

### Milestones & Timeline (Baseline)

| Phase | Dates | Primary Goal | Exit Criteria |
|------|-------|--------------|---------------|
| **Phase E0: Legacy Discovery & Domain Contracts** | 2026-01-05 → 2026-01-30 | Understand legacy and define enterprise contracts | Domain glossary + event contracts v1 approved |
| **Phase E1: Platform Foundations** | 2026-02-02 → 2026-03-06 | Event store, tenant model, plugin registry skeleton | Event store append/load works; tenant model validated |
| **Phase E2: Read Models & API Surface** | 2026-03-09 → 2026-04-17 | Projections + query APIs + config endpoints | Projections running; read-model APIs live |
| **Phase E3: Plugin-Driven UI Skeleton** | 2026-04-20 → 2026-05-29 | Config-driven UI + reference plugin | Specialty config renders core views |
| **Phase E4: Hardening & Ops** | 2026-06-01 → 2026-06-26 | Security, observability, performance baseline | Security review + monitoring baseline complete |

### Workstream Deliverables by Phase

#### Phase E0: Legacy Discovery & Domain Contracts (2026-01-05 → 2026-01-30)
| Workstream | Deliverables | Owner | Dependencies | Exit Criteria |
|------------|-------------|-------|--------------|---------------|
| Product | Legacy feature inventory + domain glossary | Product Owner | Legacy access | Inventory approved |
| Data | Legacy schema mapping + entity glossary | Data Lead | DB decision | Mapping doc approved |
| Backend | Event contracts v1 (domain events + schemas) | Backend Lead | Legacy mapping | Contract review complete |
| UI/UX | Workflow map + core clinical views inventory | UX Lead | Stakeholder access | Workflow notes captured |

#### Phase E1: Platform Foundations (2026-02-02 → 2026-03-06)
| Workstream | Deliverables | Owner | Dependencies | Exit Criteria |
|------------|-------------|-------|--------------|---------------|
| Backend | Event store service + projection runner skeleton | Backend Lead | Event store decision | Append/load + replay demo |
| Data | Tenant model + system schema | Data Lead | Tenant decision | Tenant resolution validated |
| DevOps | CI pipeline + environments + secrets strategy | DevOps | Hosting decision | CI green on main |
| Security | Auth scaffolding + audit log standards | Security Lead | Auth decision | JWT validation demo |

#### Phase E2: Read Models & API Surface (2026-03-09 → 2026-04-17)
| Workstream | Deliverables | Owner | Dependencies | Exit Criteria |
|------------|-------------|-------|--------------|---------------|
| Backend | Projections for Patient/Admission/FlightPlan | Backend Lead | Event store | Read models updated from events |
| Data | Read-model schemas + indexes | Data Lead | Projections | Query performance baseline |
| Backend | Config endpoints for specialty UI | Backend Lead | Plugin contract | `/specialties/{id}/config` works |

#### Phase E3: Plugin-Driven UI Skeleton (2026-04-20 → 2026-05-29)
| Workstream | Deliverables | Owner | Dependencies | Exit Criteria |
|------------|-------------|-------|--------------|---------------|
| Frontend | Plugin loader + config-driven layouts | Frontend Lead | Config endpoints | Core shell renders |
| UI/UX | Design tokens + core clinical components | UX Lead | None | Token doc complete |
| Backend | Plugin registry + manifest validation | Backend Lead | Plugin contract | Registry loads reference plugin |

#### Phase E4: Hardening & Ops (2026-06-01 → 2026-06-26)
| Workstream | Deliverables | Owner | Dependencies | Exit Criteria |
|------------|-------------|-------|--------------|---------------|
| Security | Security review + PHI leakage tests | Security Lead | All | Findings closed |
| DevOps | Monitoring/alerts + backup/restore drill | DevOps | Hosting decision | Alerts + DR proof |
| Performance | Baseline perf tests on read models | Tech Lead | Read models | Latency budget documented |

### Critical Path (Must-Hit Items)
- Decision gates resolved by 2026-01-16.
- Event contracts v1 approved by 2026-01-30.
- Event store + projection skeleton live by 2026-03-06.
- Read models + query APIs live by 2026-04-17.
- Plugin registry + config-driven UI skeleton by 2026-05-29.

### Platform Readiness Checklist (Enterprise Skeleton)
- Event store append/load + replay proven with sample events.
- Tenant resolution + isolation validated (RLS or schema).
- Plugin registry loads manifest and exposes config.
- Read models update via projections (no direct writes).
- AuthN/AuthZ enforced across API gateway boundary.
- Monitoring + logging redaction in place.

### Open Risks & Mitigations
- **Legacy domain complexity:** mitigate with Phase E0 mapping + event contracts review.
- **Event sourcing scope creep:** mitigate with strict contract v1 and minimal projections.
- **Plugin contract churn:** mitigate with versioned manifest schema.
- **Tenant isolation risks:** mitigate with early RLS/schema decision and tests.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Browser / Clinician UI                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Next.js Frontend (Port 3000)                    │
│  • Config-driven UI                                          │
│  • Plugin-aware components                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     API Gateway                              │
│  • AuthN/AuthZ (OIDC/JWT)                                    │
│  • Tenant resolution                                         │
│  • Versioned APIs                                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Core Services                              │
│  • Patient / Admission / FlightPlan                          │
│  • Clinical Events                                           │
│  • Plugin Registry                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 Event Bus (Kafka?)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Data Layer                              │
│  • Operational DB (Postgres/SQL Server)                      │
│  • Event Store (append-only)                                 │
│  • Read Models / Projections                                 │
│  • Redis Cache / Blob Storage                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Function: Backend

### Rationale
The backend provides the event store, projection engine, plugin registry, and API gateway for a multi-tenant, event-sourced platform. It must enforce PHI security at all boundaries and provide versioned APIs for config-driven UI.

### Success Tests
- [ ] Event store append/load + replay works
- [ ] Projections update read models deterministically
- [ ] Plugin registry loads at least one manifest
- [ ] Tenant isolation enforced in data access
- [ ] PHI never appears in URLs or logs
- [ ] Type checking passes with `mypy --strict`
- [ ] Core APIs have OpenAPI documentation

### Approach
- **Framework:** FastAPI with async support
- **Event Store:** Append-only events in Postgres/SQL Server (per decision gate)
- **Projections:** Background projection runner + read-model tables
- **Plugin Registry:** Manifest validation + specialty config endpoints
- **Validation:** Pydantic v2 schemas
- **Auth:** Mock auth for local dev, OIDC with JWT validation for production
- **Database:** PostgreSQL 16 for dev/prod parity (SQLite only for unit tests)

### Interactions with Other Functions
- **Frontend:** Provides REST API endpoints consumed by Next.js
- **Data:** Owns database schema and migrations via Alembic

---

### Phase: Project Setup

#### Rationale
Establish the foundational project structure, dependencies, and development environment before implementing features.

#### Success Tests
- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] `/health` endpoint returns 200 OK
- [ ] `mypy app/` passes with no errors
- [ ] `pytest tests/` runs (even if no tests yet)

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Create backend directory structure | Pending | Organize code by domain | Directories exist per architecture spec |
| Initialize Python virtual environment | Pending | Isolate dependencies | `pip list` shows installed packages |
| Create requirements.txt | Pending | Pin dependencies | `pip install -r requirements.txt` succeeds |
| Create FastAPI app skeleton | Pending | Entry point for API | Server starts on port 8000 |
| Add health check endpoint | Pending | Verify service is running | `GET /health` returns `{"status": "ok"}` |
| Configure mypy for strict checking | Pending | Type safety | `mypy app/` passes |
| Set up pytest configuration | Pending | Test framework ready | `pytest` runs without config errors |

---

### Phase: Event Store & Read Models

#### Rationale
Define the append-only event store, projection infrastructure, and read-model tables that power query APIs.

#### Success Tests
- [ ] Event store tables created via Alembic
- [ ] Append + load events with optimistic concurrency
- [ ] Projection runner updates read models from events
- [ ] Read-model tables created with required indexes

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Create events table schema | Pending | Append-only store | Migration creates events table |
| Create snapshots/subscriptions tables | Pending | Replay + projections | Migration creates tables |
| Implement EventStore service | Pending | append/load/replay | Unit tests pass |
| Implement projection runner skeleton | Pending | read model updates | Replay updates read models |
| Create read-model tables (patient/admission/flightplan) | Pending | query optimized | Tables + indexes created |

---

### Phase: Read Model Query APIs

#### Rationale
Expose query APIs backed by projections and read models (no direct writes).

#### Success Tests
- [ ] All endpoints use UUID, never MRN in URL
- [ ] Pagination works with limit/offset
- [ ] Search by MRN works via request body (no MRN in URL or query params)
- [ ] Tenant scoping enforced on all queries

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| GET /api/v1/patients | Pending | List patients | Returns paginated read models |
| GET /api/v1/patients/{uuid} | Pending | Patient detail | Returns read model by UUID |
| GET /api/v1/admissions | Pending | List admissions | Supports filtering by patient, status |
| GET /api/v1/flightplans/{uuid} | Pending | FlightPlan detail | Returns read model by UUID |
| POST /api/v1/patients/search | Pending | PHI-safe MRN search | MRN in body returns matches |

---

### Phase: Event Ingestion & Command APIs

#### Rationale
Provide write endpoints that append domain events and drive projections.

#### Success Tests
- [ ] Events append with optimistic concurrency checks
- [ ] Idempotent command handling for retries
- [ ] Timeline/trajectory projections update after events

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| POST /api/v1/events (append) | Pending | Central event ingestion | Event persisted with version |
| POST /api/v1/admissions (command) | Pending | admission.created event | Event appended + projection updated |
| POST /api/v1/admissions/{uuid}/location | Pending | location.changed event | Trajectory projection updates |
| POST /api/v1/clinical-events | Pending | procedure/note events | Timeline projection updates |

---

### Phase: Authentication & Tenant Resolution

#### Rationale
Secure endpoints with OIDC/JWT validation and enforce tenant isolation at the API boundary.

#### Success Tests
- [ ] Unauthenticated requests return 401
- [ ] Mock auth works with env variables in local dev
- [ ] OIDC/JWT validation works in prod mode; claims extracted correctly
- [ ] Tenant resolved per request and applied to data access

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Create auth dependency | Pending | Inject user into routes | `request.state.user` populated |
| Mock auth for local dev | Pending | Dev without OIDC | `FP_LOCAL_USER` env var works |
| OIDC/JWT validation | Pending | Production auth | Token validated and claims mapped |
| Tenant resolution middleware | Pending | Tenant scoping | `request.state.tenant` populated |
| Role-based access control | Pending | Restrict by role | Admin-only endpoints enforced |

---

## Function: Frontend

### Rationale
The frontend provides a config-driven, specialty-aware UI shell that renders clinical views from plugin manifests and server config.

### Success Tests
- [ ] All pages render without JavaScript errors
- [ ] TypeScript compilation passes with no errors
- [ ] Config-driven UI renders from plugin config
- [ ] Core Web Vitals meet targets (LCP < 2.5s, FID < 100ms)
- [ ] WCAG 2.1 AA accessibility compliance

### Approach
- **Framework:** Next.js 14 with App Router
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui primitives
- **State:** React Server Components + client state where needed
- **Plugin UI:** Dynamic component loading + config-driven layouts

### Interactions with Other Functions
- **Backend:** Consumes REST API via fetch/server components
- **UI/UX:** Implements designs from component specifications

---

### Phase: Project Setup

#### Rationale
Establish Next.js project structure with TypeScript and Tailwind configuration.

#### Success Tests
- [ ] `npm run dev` starts without errors
- [ ] `npm run build` completes successfully
- [ ] `npm run type-check` passes

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Initialize Next.js project | Pending | App foundation | `npm run dev` works |
| Configure TypeScript strict mode | Pending | Type safety | `tsconfig.json` has strict: true |
| Set up Tailwind CSS | Pending | Styling framework | Tailwind classes apply |
| Configure API proxy to backend | Pending | Local dev routing | `/api/*` proxies to :8000 |
| Add shadcn/ui | Pending | Component primitives | Button component renders |
| Create layout structure | Pending | App shell | Header, sidebar, main area |

---

### Phase: Plugin-Driven App Shell

#### Rationale
Create the base shell that loads specialty configuration and renders plugin-aware layouts.

#### Success Tests
- [ ] Specialty config fetched and cached
- [ ] App shell renders dynamic sidebar sections
- [ ] Dynamic components load without errors

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Create PluginContext + provider | Pending | Central config loading | Config available in app |
| Specialty selector (tenant-aware) | Pending | Context switching | UI updates by specialty |
| Dynamic panel loader | Pending | Plugin UI composition | Component renders by name |
| Base shell layout | Pending | Consistent nav | Header/sidebar render |

---

### Phase: Config-Driven Clinical Views

#### Rationale
Render clinical views (header, timeline, trajectory) driven by specialty config and read models.

#### Success Tests
- [ ] Patient header renders configured fields
- [ ] Timeline renders events by category
- [ ] Trajectory view renders location history

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Config-driven patient header | Pending | Specialty fields | Fields render from config |
| Timeline skeleton | Pending | Event visualization | Events appear by category |
| Trajectory view | Pending | Location history | Path renders from read model |
| Read-model data adapters | Pending | Stable API mapping | UI renders with mock data |

---

## Function: Data

### Rationale
Manage event store schema, read-model tables, tenant isolation, and migrations.

### Success Tests
- [ ] Event store schema created and versioned
- [ ] Read-model tables created with required indexes
- [ ] Tenant isolation enforced (RLS or schema separation)
- [ ] Migrations are reversible

### Approach
- **Event Store:** Append-only events + optional snapshots
- **Read Models:** Query-optimized tables updated by projections
- **Migrations:** Alembic for version control
- **Tenant Isolation:** RLS or schema separation (per decision gate)

### Interactions with Other Functions
- **Backend:** Provides models and database sessions

---

### Phase: Event Store Schema

#### Rationale
Define append-only event store tables and constraints for enterprise auditability.

#### Success Tests
- [ ] Events table created with stream/version constraints
- [ ] Indexes support common event queries

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Define events table schema | Pending | Event sourcing core | Migration creates events table |
| Define snapshots table schema | Pending | Replay performance | Migration creates snapshots |
| Define subscriptions table schema | Pending | Projection checkpoints | Migration creates subscriptions |

---

### Phase: Read Model Schema

#### Rationale
Create query-optimized read-model tables for UI and reporting.

#### Success Tests
- [ ] Read-model tables created with indexes
- [ ] Projections can update read models

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Define patient/admission/flightplan read models | Pending | Core queries | Tables created |
| Define timeline/trajectory read models | Pending | UI performance | Tables created |
| Define index strategy | Pending | Query performance | Key queries have indexes |

---

### Phase: Tenant Isolation

#### Rationale
Ensure tenant boundaries are enforced at the data layer.

#### Success Tests
- [ ] Tenant scoping enforced on read models
- [ ] Tenant admin bypass documented and audited

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Define tenant model + system schema | Pending | Tenant config | Tables created |
| Implement RLS policies or schema isolation | Pending | Data isolation | Cross-tenant access blocked |
| Tenant context session hooks | Pending | Enforce scoping | Tenant set per session |

---

## Function: UI/UX

### Rationale
Define visual design, component specifications, and interaction patterns for clinical workflows.

### Success Tests
- [ ] Design tokens documented
- [ ] Component specifications complete
- [ ] Clinical workflows validated with stakeholders
- [ ] Accessibility requirements met

### Approach
- **Design System:** Tailwind + shadcn/ui customized with clinical tokens
- **Colors:** Clinical status colors (critical=red, stable=green, etc.)
- **Typography:** Inter font family, readable at clinical workstation distances

### Interactions with Other Functions
- **Frontend:** Provides design specifications for implementation

---

### Phase: Design System Foundation

#### Rationale
Establish consistent visual language before building pages.

#### Success Tests
- [ ] Color palette defined including clinical status colors
- [ ] Typography scale documented
- [ ] Spacing scale documented
- [ ] Component variants specified

#### Tasks

| Task | Status | Rationale | Success Test |
|------|--------|-----------|--------------|
| Define color tokens | Pending | Consistent colors | Tailwind config extended |
| Define typography scale | Pending | Readable text | Font sizes documented |
| Define spacing scale | Pending | Consistent layout | Spacing values documented |
| Clinical status colors | Pending | Quick visual cues | Critical/warning/stable colors |

---

## Enterprise Roadmap (from Enterprise Architecture Plan)

Note: This roadmap tracks enterprise platform maturity beyond the skeleton delivery plan above.

### Phase 0: Enterprise Foundation (Current)
- [ ] Complete architecture documentation
- [ ] Establish event contracts + plugin manifest v1
- [ ] Build event store + projection framework
- [ ] Establish tenant model and auth boundaries

### Phase 1: Core Platform (Future)
- [ ] Event sourcing infrastructure
- [ ] Plugin system foundation
- [ ] Multi-tenant support
- [ ] Design system / component library

### Phase 2: Enterprise Features (Future)
- [ ] SSO integration (Azure AD, SAML)
- [ ] Full audit trail
- [ ] Second specialty plugin
- [ ] EHR integration framework

### Phase 3: Scale & Expand (Future)
- [ ] Additional specialty plugins
- [ ] Reporting & analytics
- [ ] Mobile companion app
- [ ] Customer self-service

---

## Appendix

### Key Reference Documents

| Document | Purpose |
|----------|---------|
| [ENTERPRISE_ARCHITECTURE_PLAN.md](docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md) | Full enterprise vision |
| [LEGACY_CLAUDE_REFERENCE.md](docs/LEGACY_CLAUDE_REFERENCE.md) | Legacy system context |
| [FpCodes.py](legacy-reference/core/FpCodes.py) | Domain enums and codes |
| [Admission.py](legacy-reference/models/Admission.py) | Core business logic |
| [DATABASE_SCHEMA_DUMP.sql](docs/data-model/DATABASE_SCHEMA_DUMP.sql) | Legacy schema |

### Environment Variables

**Backend (.env.local)**
```bash
FLIGHTPLAN_ENV=local
DEBUG=true
DATABASE_URL=postgresql+asyncpg://localhost/flightplan_dev
FP_LOCAL_USER=dev_user
FP_LOCAL_ROLE=admin
FP_LOCAL_OCCUPATION=MD
CORS_ORIGINS=["http://localhost:3000"]
```

**Frontend (.env.local)**
```bash
BACKEND_URL=http://localhost:8000
```

---

*This plan follows the Structured Project Planning Methodology from ~/.claude/CLAUDE.md*

---

## Claude's Independent Critique (2026-01-02, Revised)

This is a fundamentally different plan from the previous version. The plan now builds the enterprise architecture—event sourcing, plugin system, multi-tenant—rather than deferring it. This is the right call.

### What's Now Right

**1. Architecture alignment.** The plan now matches the ENTERPRISE_ARCHITECTURE_PLAN.md. Event sourcing is core infrastructure (Phase E1), not a future retrofit. Plugin registry and config-driven UI are explicit deliverables. Tenant isolation is addressed early.

**2. Honest scope.** Non-Goals explicitly exclude "Production cutover," "Full legacy feature parity," and "Multi-specialty production modules." This is a skeleton, not a pilot. That framing prevents scope creep.

**3. Discovery-first.** Phase E0 is "Legacy Discovery & Domain Contracts" before building. Event contracts v1 must be approved before implementation starts. This inverts the typical "build first, understand later" anti-pattern.

**4. Realistic timeline.** Six months (Jan–June) for an enterprise skeleton is defensible. The previous 4-month pilot timeline was aggressive for CRUD; it would have been impossible for event sourcing + plugins + multi-tenant.

**5. Clear exit criteria.** Each phase has specific exit criteria. The Platform Readiness Checklist defines what "skeleton" means in concrete terms.

**6. Success criteria include enterprise properties.** Extensibility ("add a specialty plugin without core code changes") and Tenant Isolation ("100% tenant-scoped access validated") are now explicit success criteria, not afterthoughts.

### Remaining Concerns

**1. Decision gates are front-loaded and aggressive.**

Five major architectural decisions must be resolved by 2026-01-16 (11 days from plan date):

| Decision | Complexity |
|----------|------------|
| Event store strategy (Postgres-only vs Kafka) | High - impacts infrastructure, ops, and projection architecture |
| Plugin contract v1 (manifest schema + extension model) | High - defines extensibility model for the platform |
| Tenant isolation model (RLS vs schema separation) | High - impacts every table and query |
| Auth + tenant resolution (OIDC + claims model) | Medium - well-understood but needs tenant mapping |
| Database of record (PostgreSQL vs SQL Server) | Medium - mostly organizational/political |

Making these decisions well requires some exploration. The plan assumes decisions can be made before Phase E0 discovery completes, but the discovery might reveal constraints that inform these decisions.

**Recommendation:** Consider splitting decision gates:
- 2026-01-16: Database, Auth approach (lower risk, can be made with existing knowledge)
- 2026-01-23: Event store strategy, Tenant model (after 2 weeks of legacy discovery)
- 2026-01-30: Plugin contract v1 (informed by event contracts v1 work)

**2. Phase E0 is ambitious for 4 weeks.**

Phase E0 deliverables across workstreams:
- Legacy feature inventory + domain glossary (Product)
- Legacy schema mapping + entity glossary (Data)
- Event contracts v1 (domain events + schemas) (Backend)
- Workflow map + core clinical views inventory (UI/UX)

The legacy `Admission.py` is 41KB of business logic. `FpCodes.py` contains complex domain enums. Extracting event contracts from this—deciding what events exist, what their schemas are, what their semantics mean—is significant design work.

Four weeks for discovery + contracts + approval is tight. If contracts v1 is wrong, everything downstream (projections, APIs, UI) is wrong.

**Recommendation:** Either extend Phase E0 to 6 weeks, or explicitly scope contracts v1 to a minimal set (e.g., 5-7 core events for Patient/Admission/Location) with a contracts v1.1 expansion planned.

**3. Plugin contract v1 is a decision gate but not a deliverable.**

The decision gate says "Plugin contract v1 (manifest schema + extension model)" must be resolved by 2026-01-16. But:
- Phase E0 deliverables don't include plugin manifest design
- Phase E3 "Plugin Registry" assumes the contract exists

Where does the manifest schema get designed? It should either be:
- A Phase E0 Backend deliverable (alongside event contracts), or
- The decision gate should move later (after some exploration)

Currently, the plan requires defining the plugin contract before understanding the domain, which may produce a generic contract that doesn't fit clinical needs.

**4. Event contracts v1 work isn't reflected in tasks.**

Phase E0 workstream says Backend delivers "Event contracts v1 (domain events + schemas)" but there's no Backend Phase for contract design. The Backend phases are:
- Project Setup
- Event Store & Read Models
- Read Model Query APIs
- Event Ingestion & Command APIs
- Authentication & Tenant Resolution

Event contracts design happens... where? It's a Phase E0 deliverable but the tasks don't show it.

**Recommendation:** Add a "Phase: Domain Events & Contracts" to Backend (or a separate "Domain Modeling" function) with tasks like:
- Define core domain events (Patient, Admission, Location, Clinical)
- Define event schemas (Pydantic/JSON Schema)
- Document event semantics and invariants
- Review contracts with clinical stakeholders

**5. Testing strategy is still implicit.**

The plan mentions:
- "Unit tests pass"
- "Security review + PHI leakage tests" (Phase E4)
- "Baseline perf tests on read models" (Phase E4)

But there's no:
- Event replay correctness testing plan
- Projection determinism testing plan
- Tenant isolation testing plan
- Integration testing strategy (events → projections → APIs → UI)
- Contract compatibility testing (can old events replay through new projections?)

Event sourcing introduces testing challenges that CRUD doesn't have. The plan should acknowledge this.

**6. "Skeleton" scope boundaries are soft.**

The Platform Readiness Checklist defines what the skeleton must do:
- Event store append/load + replay proven with sample events
- Tenant resolution + isolation validated
- Plugin registry loads manifest and exposes config
- Read models update via projections
- AuthN/AuthZ enforced
- Monitoring + logging redaction in place

But it doesn't define scope limits:
- How many event types in contracts v1? (5? 20? 50?)
- How many projections/read models? (3? 10?)
- What does "reference plugin" include? (Just config? Custom UI components?)
- What clinical views does the UI skeleton render? (List + detail? Timeline? Everything?)

Without scope limits, "skeleton" can expand.

**Recommendation:** Add explicit scope caps to Phase deliverables. Example: "Event contracts v1: 8-12 core events covering Patient, Admission, Location, and one clinical event category."

**7. The Enterprise Roadmap section is confusing.**

The plan has two phase numbering schemes:
- Phases E0–E4 (the delivery plan, Jan–June 2026)
- Phases 0–3 (the enterprise roadmap, "Current" to "Future")

The relationship is unclear. Phase E0–E4 seems to cover most of "Phase 0: Enterprise Foundation" and some of "Phase 1: Core Platform." Consider either:
- Removing the Enterprise Roadmap section (it's in ENTERPRISE_ARCHITECTURE_PLAN.md already), or
- Mapping E0–E4 explicitly to the roadmap phases

**8. Clinical domain depth in Phase E0.**

Phase E0 has "Workflow map + core clinical views inventory" (UI/UX) but no explicit tasks for:
- Understanding `FpCodes.py` domain enums (teams, locations, procedures, risk levels)
- Mapping `Admission.py` business rules to events
- Documenting clinical invariants (e.g., "a patient can't be in two locations simultaneously")
- Validating event contracts with a clinical stakeholder

The event contracts will encode clinical semantics. If the Backend Lead defines them without clinical input, they may miss domain constraints.

**Recommendation:** Add a clinical domain review checkpoint to Phase E0, where event contracts are validated by someone who understands the clinical workflow.

### Summary Assessment

| Aspect | Previous Plan | Current Plan |
|--------|--------------|--------------|
| Architecture alignment | Poor (CRUD vs enterprise) | Good (builds enterprise) |
| Scope control | Medium (100% parity trap) | Good (explicit non-goals) |
| Timeline realism | Poor (4 months) | Reasonable (6 months) |
| Discovery phase | Missing | Present (Phase E0) |
| Event sourcing | Deferred | Core |
| Plugin system | Missing | Included |
| Multi-tenant | Deferred | Included |
| Testing strategy | Absent | Still implicit |
| Decision gate timing | N/A | Aggressive |
| Task/workstream alignment | Poor | Better but gaps remain |

**Bottom Line**

This plan is **ready to start** with manageable risks. The architecture is right. The scope is honest. The timeline is defensible.

The main risks are:
1. Decision gates are front-loaded before discovery completes
2. Event contracts v1 work isn't reflected in Backend tasks
3. Phase E0 may be too short for quality contract design
4. Testing strategy needs definition before Phase E1

**Recommended actions before Phase E0 start:**
1. Add explicit "Domain Events & Contracts" tasks to Backend or a new Domain function
2. Consider staggering decision gates (simpler decisions first, contract decisions after some discovery)
3. Define scope caps for contracts v1 and reference plugin
4. Assign clinical stakeholder review checkpoint for event contracts

If these are addressed in Week 1, the plan is executable.
