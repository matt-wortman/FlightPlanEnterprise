# FlightPlan v2.0 — Codebase Analysis & Refactoring Report

**Date:** 2025-12-18
**Last Updated:** 2026-01-02

## Update (2026-01-01): Trajectory change-point model in v3

The v3 backend now supports a **canonical change-point trajectory model** aligned to clinician workflow. Instead of pairing start/end events, each change point captures the **active location + active y-axis state** and the step-function line persists until the next change point.

Key additions:
- Tables: `trajectory_point`, `trajectory_state_type`
- View: `trajectory_segment` (derived intervals for analytics)
- Feature flags: `TIMELINE_USE_TRAJECTORY_POINTS`, `TIMELINE_TRAJECTORY_POINT_ADMISSION_UUIDS`
- Backfill + validation scripts in `flightplan-v3/backend/scripts/`

This update reduces end-event dependency and aligns the data model with how clinicians enter timeline changes.

## 1) What the app is intended to do (user perspective)

**FlightPlan** is a web app for tracking a patient’s hospital journey (locations + risk status over time) and coordinating review/feedback around that journey. The core user experience is:

- **Patient list (daily workflow)**: see all current admissions, sort/filter/search, quickly identify “for review” and “cross-check” (high-risk) patients, and jump into a patient’s detailed timeline.
- **Patient detail (decision-making workflow)**:
  - **Timeline graph**: interactive visualization of the admission timeline across locations (Pre-op, CTOR, CICU, ACCU, Cath, Discharge) and risk status changes (Intubated/Extubated/Procedure/etc.).
  - **Add/edit events**: clinical moments, conferences, imaging, ratings/feedback, suggested edits; edit or build the location timeline.
  - **Documents**: attachment handling (Azure Blob) with thumbnails and a document viewer.
  - **Case management view**: rollups of course corrections + conferences.
- **Admin-ish actions**: add patient/admission; “clean up” (delete) a patient by MRN; role-based access gates some features.

In short: it’s a **clinical timeline + event log + document hub** optimized for cardiac care flows (“jcore”).

---

## 2) As-is architecture (what’s running today)

### Runtime stack
- **Dash (Python)** for UI pages, layout, and callbacks.
- **Flask** underneath Dash for server + **filesystem-backed sessions** (`Flask-Session`).
- **SQL Server (pyodbc)** for all patient/admission/event data.
- **Azure Blob Storage** for document binaries (stored as base64 blobs in code paths).
- **Custom React timeline component** compiled into a Dash component library (`flight_plan_components`).

### High-level data flow
1. Request hits Dash app (`FlightPlan2/FlightPlan2.py` → `App.py` → `FpServer.py`).
2. User identity comes from **Azure header** (`X-MS-CLIENT-PRINCIPAL-NAME`) or local env overrides.
3. Patient list loads from SQL, **caches Patient objects in Flask session**.
4. Patient detail uses cached Patient/Admission objects + SQL reads; graph data is derived by `utils/FP2_GraphUtilities.generateFlightPlanGraph()`.
5. Edits are persisted via model methods (`Admission.addLocationStep`, `Annotation.editAnnotation`, etc.) using direct SQL.

### Key architectural constraint driving complexity
The app is **not layered**: UI callbacks, domain logic, and persistence are tightly interwoven (especially in `pages/PatientDetail.py`, `models/Admission.py`, and the modal implementations). This makes refactoring and “other specialty” reuse harder than it needs to be.

---

## 3) Data model (current DB contract)

Entities (inferred from code + stored procedures):
- `patients (MRN PK)`
- `admissions (MRN, ADM PK)`
- `location_steps (MRN, ADM, LocationStepID PK)`
- `location_risks (MRN, ADM, LocationStepID, LocationRiskID PK)`
- `bedside_procedures (MRN, ADM, LocationStepID, BedsideProcedureID PK)`
- `annotations (MRN, ADM, AnnotaionID PK)` *(note the column name typo “AnnotaionID” is used throughout)*
- `feedbacks (MRN, ADM, FeedbackID PK)`
- `conferences (MRN, ADM, ConferenceID PK)`
- `course_corrections (MRN, ADM, course_correct_id PK)`
- `continuous_therapy (MRN, ADM, CtId PK)`
- `attachments (MRN, ADM, AttachmentID PK)`
- `users (username PK)`

Important characteristics:
- Multiple columns are **JSON-in-a-string** “bags” (e.g., `admissions.Status`, `Diagnosis`, `Interventions`; `location_steps.Teams`, `Notes`, `Extra`; `feedbacks.Performance`, `AttachmentKeys`; `annotations.href`).
- Attachments are stored as:
  - DB row: metadata (`storage_key`, `ContentType`, `Thumbnail`, etc.)
  - Blob: the actual file content (base64 in some code paths).

**Stored procedure mismatch risk:** the `sql/add_*.sql` procedures define much smaller `varchar()` sizes than the table definitions in `dbSetup.py` (e.g., `add_admission` uses `status varchar(500)` while the table allows much more). This can silently truncate payloads (status/diagnosis/interventions/attachments).

---

## 4) Major findings (complexity, performance, correctness, security)

### A) Specialty coupling is pervasive (hard to reuse for other specialties)
Specialty-specific values and behavior appear across *multiple layers*:
- `FlightPlan2/FpCodes.py`: locations, colors, risk statuses, team rosters, schemas, RBAC ops.
- `FlightPlan2/validation/*.py`: clinical codes, conference types, imaging types, rating rubrics.
- `FlightPlan2/components/jcore/*`: location editing UI & save flows hard-coded per unit.
- `utils/FP2_GraphUtilities.py`: risk/location mapping logic for the graph.
- `pages/PatientDetail.py`: menu structure and edit flows aligned to those “jcore” definitions.

Result: creating “another specialty version” currently requires editing **many files across many layers**, which is expensive and risky.

### B) Performance bottlenecks
1. **Eager-loading Admission on patient list**
   - `utils/generate.loadPaginatedPatientData()` builds `Patient` objects, then calls `patient.createAdmission(...)`, which instantiates `Admission(...)`.
   - `Admission.__init__` immediately loads location steps/timeline + course corrections + annotations + feedbacks + conferences + attachments.
   - That’s far more than the patient list needs, and creates a query explosion / heavy object graph per patient.

2. **Graph uDays query does extra DB work**
   - `generateFlightPlanGraph()` does a UNION query across `location_risks`, `annotations`, `feedbacks`, `conferences` to compute plotted days, even though much of this is already loaded/could be derived without round-tripping.

3. **Flask-session caching stores full Python objects**
   - `utils/cache_manager.py` stores Patient objects in server sessions. This risks memory bloat, slower serialization, and scaling limitations (multi-instance deployments, session portability).

### C) Correctness & concurrency hazards
1. **Stateful singleton modals shared across users**
   - `components/roots/register_roots.py` creates global instances like `AddClinicalEventModal = ClinicalEventModal(...)`.
   - Modal classes (BaseModal subclasses and doc/feedback viewers) store per-request state (`self.user`, `self.patient`, `self.admission`, `self.dbId`, `self.document_content`, etc.).
   - In a multi-user server, this is a real risk for cross-user state bleed, incorrect saves, and privacy issues.

2. **BaseModal ID bug**
   - `BaseModal.__init__` sets `self.toggle_graph_visible_id = '{}_{}'.format(id, 'toggle_graph')` where `id` is Python’s built-in, producing a constant/shared component id. This can cause layout collisions and broken callbacks.

3. **Missing/incomplete implementations**
   - `components/jcore/sections/LocationSection.py` calls `self.updateLocationDateTime(...)` but no such method exists in that class or its base.
   - `components/roots/modals/ContinuousTherapyModal.py` does not persist anything (`createOrModify` returns a mapping stub).
   - `components/jcore/sections/EcmoSection.py` references an undefined `self.ecmoTimePicker`.

4. **Bugs in domain logic**
   - `models/Patient.py`: `isPatientOnTrack()` uses `lastSet['detail']` (dict access) but `lastSet` is a `CourseCorrection` object.
   - `models/Patient.py`: `reloadActiveAdmission()` uses `ADM = self.activeAdmissionID` (index) not the admission ID.
   - `components/containers/PatientContainer.py`: references `patient.dob` (should be `patient.DOB`).

### D) Security concerns (high priority)
1. **SQL injection risk**
   - Many SQL statements are built via string formatting / f-strings with user-influenced values (e.g., MRN search, usernames, deletion by MRN, etc.).
   - Some places use parameters, but the codebase is inconsistent.

2. **Secrets in repo**
   - `README.md` and some scripts include plaintext credentials and sensitive deployment assumptions (these should be removed and rotated immediately).

3. **Destructive scripts run at import time**
   - `FlightPlan2/dbSetup.py` calls destructive operations (`removeAllBlobs()`, `createTables()`, etc.) at module import, not behind `if __name__ == '__main__':`.

---

## 5) Refactoring goals (what “success” looks like)

From a user perspective:
- Patient list loads fast and reliably (no “waiting for everything to load”).
- Patient detail graph renders quickly; edits feel responsive.
- Editing/adding events is stable and doesn’t “randomly” mix state between users.
- Specialty variants can be produced without rewriting core logic.

From a developer/maintenance perspective:
- **Core platform** code is stable; **specialty config** is declarative.
- Adding a specialty is primarily configuration + small, well-contained plugin code (not cross-cutting changes everywhere).
- DB access is centralized, parameterized, and testable.
- Pages/components are smaller, composable, and have fewer brittle callback chains.

---

## 6) Recommended refactoring plan (preserve all functionality)

### Phase 1 — Stabilize & secure (high ROI, low feature risk)
Deliverables:
- **Eliminate stateful singleton hazards**
  - Make modals stateless: move `self.user/self.patient/self.admission/self.dbId` into `dcc.Store` state (per session), or derive from `session_store` + URL inside each callback.
  - Avoid global shared lists like `self.document_content` inside `DocViewerModal` and `FeedbackViewerModal`.
- **Fix ID collision and missing methods**
  - Fix `BaseModal.toggle_graph_visible_id` and any other id collisions.
  - Implement or remove `LocationSection.updateLocationDateTime` behavior.
- **Parameterize SQL everywhere**
  - Standardize on `?` parameters for pyodbc.
  - Centralize “query building” in a data-access layer (even before a full ORM).
- **Remove/rotate secrets**
  - Strip credentials from `README.md` and scripts; document env var usage instead.
- **Make destructive scripts safe**
  - Move dbSetup execution behind `if __name__ == '__main__':`.
- **Add minimal regression tests for invariants**
  - Smoke tests: graph generation for a known admission shape; patient list filter/sort; modal save paths (non-DB mocked).

Outcome:
- Fewer production risks (security + privacy), fewer “random” UI issues, safer base for deeper refactors.

### Phase 2 — Data access + performance (no UX change, major speedup)
Deliverables:
- **Split “PatientListRow DTO” from “PatientDetail model”**
  - Patient list should load a lightweight DTO: fields needed for list display only.
  - Only load full `Admission` (timeline + events + attachments) when user enters patient detail.
- **Make Admission lazy-load**
  - Replace “load everything in `Admission.__init__`” with explicit `load_*()` calls or `lazy` properties.
- **Replace Flask-session object caching**
  - Cache only identifiers + minimal DTOs, not full object graphs.
  - If caching is needed server-side, use a real cache store (Redis) or a bounded in-memory LRU keyed by (MRN, ADM) with TTL.
- **Tighten graph generation**
  - Compute `uDays` from already-loaded in-memory data where possible.
  - Add DB indexes for the actual query patterns (MRN/ADM/date).

Outcome:
- Faster patient list, less DB load, smaller session footprint, more predictable performance at scale.

### Phase 3 — Specialty configurability (the “platform + specialty pack” split)
Deliverables:
- Introduce a `specialties/` package with a **single entry config**:
  - `FlightPlan2/specialties/jcore/config.yaml` (or `.json`)
  - `SPECIALTY=jcore` env var selects config.
- Move the following out of hard-coded Python into specialty config:
  - Locations (labels, colors, ordering, display headings)
  - Risk status categories + mapping to y-axis indices
  - Team rosters and “team sections” definitions
  - Clinical nodes / imaging / conference / rating definitions
  - Patient list columns, default filters/sorts, and which toggles appear
- Replace direct imports of `FpCodes` and `validation/*` in UI code with a config loader:
  - `get_specialty().locations`, `get_specialty().clinical_nodes`, etc.
- Define a **specialty plugin interface** for anything truly custom:
  - Example: `specialties/jcore/location_editors.py` registers how to render & persist each location editor.
  - For a new specialty, you provide config + optionally custom editors where needed.

Outcome:
- Creating a new specialty becomes:
  1) copy config, 2) adjust definitions, 3) implement only the truly special workflows.

### Phase 4 — UI modularization & callback simplification (maintenance win)
Deliverables:
- Split `pages/PatientDetail.py` and `pages/Patients.py` into:
  - `layout.py` (pure layout construction)
  - `callbacks/*.py` (grouped by feature area)
  - `services/*.py` (business logic)
- Use pattern-matching callbacks consistently with an ID registry (single source of truth for component IDs).
- Standardize state: one well-defined “session store schema” and one “patient page store schema”.

Outcome:
- Smaller files, clearer responsibilities, easier onboarding, lower regression risk.

### Phase 5 — Timeline component modernization (optional but high leverage)
Deliverables:
- Fix correctness issues in React sources (e.g., `GraphMenu.react.js` React import usage).
- Add a small set of automated component tests (basic interactions + setProps payload shapes).
- Consider incremental modernization:
  - Convert the Timeline class component to hooks only if it materially simplifies maintenance.

Outcome:
- Easier to evolve the visual timeline and reuse it across specialties.

---

## 7) Concrete “specialty config” proposal (how to make new specialties easy)

Minimum viable config schema (conceptual):
- `locations[]`: `{ key, labels[], heading, colors{line,ecmo,annotation}, editorTemplateKey }`
- `risk_statuses[]`: `{ category, y_index, match_values[] }`
- `timeline`: `{ yAxisMapping, lineWidth, defaultVisibility }`
- `patient_list`: `{ columns[], filters[], defaultSort }`
- `events`:
  - `clinical_nodes[]`, `imaging_nodes[]`, `conference_nodes[]`, `rating_nodes{score, performance, outcome}`
- `rbac`: operations + min credential level
- `attachments`: categories per event/location template

Then implement:
- `SpecialtyRegistry` that loads config at startup.
- `LocationEditorRegistry` that maps `editorTemplateKey` → renderer + save handler.
  - Start by wiring existing jcore location editors behind the registry.
  - Later, migrate editors to a generic “form spec” driven renderer.

This approach keeps 100% of current functionality while making “new specialty” a bounded project.

---

## 8) File-by-file map (what each code area does)

### Repo root
- `README.md`: developer setup; currently includes sensitive credentials (should be removed/rotated).
- `CLAUDE.md`: repo usage notes and architecture overview.
- `dev-azure-buildpipeline.yml`, `dev-feature-azure-buildpipeline.yml`, `preview-azure-buildpipeline.yml`, `prod-azure-buildpipeline.yml`: Azure pipeline definitions.
- `jsconfig.json`: JS tooling config (React build support).
- `flightPlan_source_code.zip`: archived backup (contains a full repo snapshot including `.git`).

### `FlightPlan2/` (main application)
- `FlightPlan2/FlightPlan2.py`: main entry point (`app.run_server(...)`).
- `FlightPlan2/App.py`: main layout shell (nav/header/footer) + session/user bootstrap.
- `FlightPlan2/FpServer.py`: DashProxy/Flask server + session configuration.
- `FlightPlan2/FpConfig.py`: env configuration (DB, encryption, chatbot, paging).
- `FlightPlan2/FpDatabase.py`: SQL DB wrapper + Gremlin wrapper (graph DB unused/partial).
- `FlightPlan2/FpCodes.py`: domain constants (locations, risks, teams), schemas, RBAC rules.
- `FlightPlan2/dbSetup.py`: destructive DB + blob setup script (runs on import; unsafe).
- `FlightPlan2/Dockerfile.dash`, `FlightPlan2/docker-compose.yml`, `FlightPlan2/entrypoint.sh`: container build/run.

### `FlightPlan2/pages/`
- `FlightPlan2/pages/index.py`: redirects `/` → `/patients`.
- `FlightPlan2/pages/Home.py`: redirects `/home` → `/patients`.
- `FlightPlan2/pages/Patients.py`: patient list page (filters/sort/search/pagination, add patient, cleanup, chatbot).
- `FlightPlan2/pages/PatientDetail.py`: patient detail page (timeline graph, editing, tabs, modals, chatbot).
- `FlightPlan2/pages/Reviews.py`: placeholder page.
- `FlightPlan2/pages/not_found_404.py`: placeholder 404.
- `FlightPlan2/pages/__init__.py`: empty.

### `FlightPlan2/models/`
- `FlightPlan2/models/Patient.py`: patient model + DB create/update + admission creation.
- `FlightPlan2/models/Admission.py`: admission model; loads all related data; persists events/locations/attachments.
- `FlightPlan2/models/LocationStep.py`: location step model + DB update + JSON helpers.
- `FlightPlan2/models/LocationRisk.py`: risk model + DB update.
- `FlightPlan2/models/TimelineStep.py`: lightweight timeline row.
- `FlightPlan2/models/Annotation.py`: annotation model + DB update + attachment ref cleanup.
- `FlightPlan2/models/Feedback.py`: feedback model + DB update + attachment ref cleanup.
- `FlightPlan2/models/Conference.py`: conference model + DB update + attachment ref cleanup.
- `FlightPlan2/models/Attachment.py`: attachment model; delete implemented, update stubbed.
- `FlightPlan2/models/CourseCorrection.py`: course correction model; DB update stubbed.
- `FlightPlan2/models/__init__.py`: empty.

### `FlightPlan2/utils/`
- `FlightPlan2/utils/FP2_Utilities.py`: shared helpers (Dash context parsing, encryption, user lookup, RBAC checks, default store).
- `FlightPlan2/utils/FP2_GraphUtilities.py`: graph data builder for timeline component + lookup utilities.
- `FlightPlan2/utils/generate.py`: patient list loading, caching, filtering, sorting, search helpers, row rendering.
- `FlightPlan2/utils/cache_manager.py`: Flask-session caching of Patient objects (scaling/perf risk).
- `FlightPlan2/utils/common.py`: attachment thumbnails, parsing, location step deletion helpers.
- `FlightPlan2/utils/FP2_AttachmentUtils.py`: Azure Blob read/write/list/delete.
- `FlightPlan2/utils/FP2_Message_Manager.py`: centralized logging/toast message builder.
- `FlightPlan2/utils/FP2_Logger.py`: console logger + toast generator.
- `FlightPlan2/utils/CallbackManager.py`: helper for registering repeated callbacks for “AddContainer” patterns.
- `FlightPlan2/utils/validations.py`: date/time validation helpers.
- `FlightPlan2/utils/__init__.py`: empty.

### `FlightPlan2/components/`
- `FlightPlan2/components/containers/*`: “container” pattern for modal form bodies (ClinicalEvent/Conference/Imaging/Ratings/Patient/etc.).
- `FlightPlan2/components/sections/*`: reusable form sections (input/date/time/attachments/option select/collapse/etc.).
- `FlightPlan2/components/roots/modals/*`: modal classes (BaseModal + specific event modals + document/feedback viewers).
- `FlightPlan2/components/roots/register_roots.py`: creates global singleton modal instances + timeline editor container.
- `FlightPlan2/components/jcore/*`: specialty-specific timeline editor (location editors and supporting sections).
- `FlightPlan2/components/utils/generate.py`: legacy duplicate generator helpers (unused in current main app flow).

### `FlightPlan2/validation/`
- `clinical.py`, `conference.py`, `imaging.py`, `ratings.py`, `continuous_therapy.py`, `general.py`: hard-coded option definitions for forms and timeline markers.

### `FlightPlan2/flight_plan_components/` (custom Dash React component library)
- `src/lib/components/Timeline.react.js`: main timeline visualization logic (setProps events for edits/viewing/thumbnail).
- `src/lib/components/GraphMenu.react.js`: graph options menu (display/text toggles).
- `src/lib/components/Brush.react.js`: custom brush for zoom/selection.
- `src/lib/components/GraphTooltip.react.js`: tooltip rendering.
- `src/lib/components/EvaluationPill.react.js`: pill markers.
- `src/lib/components/utils/*`: point/overhead SVG builders.
- `flight_plan_components/Timeline.py`: auto-generated Dash component wrapper.
- `usage.py`: demo Dash app for component development/testing.
- `tests/test_usage.py`: dash testing example for component library.

### Legacy FP2 app files (not wired into current `FlightPlan2.py` flow)
- `FlightPlan2/FP2_App.py`, `FlightPlan2/FP2_Server.py`, `FlightPlan2/FP2_PatientsTab.py`, `FlightPlan2/FP2_PatientList.py`: older architecture; reference missing modules; should be removed or archived once confirmed unused.

---

## Bottom line recommendation

To reduce complexity, improve performance, and enable “new specialty versions” without losing functionality, the highest leverage path is:

1) **Stabilize + secure** (stateless modals, parameterized SQL, remove secrets, fix critical bugs),  
2) **Decouple data loading** (DTOs + lazy Admission + safer caching),  
3) **Introduce a specialty configuration layer** (platform core + specialty packs),  
4) **Modularize pages and callbacks**,  
5) Optionally modernize the React timeline component after the backend contract stabilizes.

End of report.
