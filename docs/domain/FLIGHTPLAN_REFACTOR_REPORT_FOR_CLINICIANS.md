# FlightPlan Refactoring Report (Clinician-Facing)
**Date:** 2025-12-19  
**Audience:** Clinicians and clinical operations stakeholders  
**Purpose:** Explain (in non-technical terms) why FlightPlan is being refactored, what the current system does well and poorly, and what the refactored system will deliver—covering **all major functionality** (timeline “line graphic”, database, security, chatbot, attachments, roles, and overall architecture).

**Terminology note:** This report refers to the current, legacy application as **“FlightPlan v2”** and the refactored rebuild as **“FlightPlan v3.”**

---

## 1) Executive summary (one page)

**FlightPlan is a clinical coordination tool.** It helps teams track a patient’s inpatient journey over time (locations + clinical status), capture key events and decisions, manage conferences, and keep relevant documents together in one place.

**Why we’re refactoring it:** The current system works and contains valuable clinical workflow knowledge—especially the timeline visualization—but the software foundation has become difficult to change safely. Important parts of the “internal plumbing” are tightly interwoven, inconsistent, and hard to audit. That creates operational risk: slower improvements, higher chance of regressions, more difficulty investigating discrepancies, and increased risk around protected health information (PHI).

**What will change for clinicians:** The goal is to preserve the core workflows and information clinicians rely on—patient list, patient detail timeline (the line graphic), event capture, conferences, attachments, and feedback—while making the system **more reliable, more secure, and easier to improve**. Some screens may modernize in look-and-feel, but the intent is continuity of clinical workflow.

**What will change behind the scenes:** We are rebuilding FlightPlan into clearer “modules” with well-defined boundaries:
- A **user interface** (what you see in the browser)
- A **data and rules layer** (how information is stored and validated)
- A **security and audit layer** (who can see/do what, plus traceability)

**Tradeoffs (honest):** Refactoring is a major investment. During the transition there is risk of temporary feature gaps, new bugs, and “change fatigue.” We will mitigate these with phased delivery, side-by-side validation, clinician review, and a clear go/no-go process.

---

## 1b) Continuity commitments (what stays the same vs what might change)

This section is here to make the coding target explicit: **v3 should preserve the clinician workflow and the timeline “line graphic” behavior**. Any differences discovered during side-by-side validation are treated as **regressions** until reviewed and accepted.

| Area | What stays the same (parity goal) | What may change (by design) |
|------|-----------------------------------|------------------------------|
| Timeline (“line graphic”) | Same step-style trajectory, colors, markers/symbols, click-to-open callouts, zoom/brush controls, and category toggles | Faster load time, better stability; under-the-hood code structure |
| Events/annotations | Same event types and where/how they appear on the timeline | More consistent validation and fewer “weird” edge-case states |
| Conferences/feedback | Same pills/visibility and attachment behavior | Clearer data model; improved auditability |
| Attachments/viewer | Same ability to open/view attachments from the timeline and other UI | Storage/security improvements; better metadata consistency |
| Editing (where enabled) | Same right-click → edit workflow and overall editing capabilities | Safer permissions/auditing; clearer error messages |

**PHI note for documentation and screenshots:** Any screenshots used for validation or training must be **synthetic or de-identified**. Do not include PHI in repo docs.

---

## 2) What FlightPlan is for (clinical purpose)

FlightPlan exists to support **situational awareness, care planning, and team communication** for complex admissions. In practical terms, it helps teams:
- See **where a patient has been** (unit/location timeline) and **when** transitions occurred.
- See **clinical status changes** over time aligned to those transitions.
- Document and review **clinical events**, **procedures**, and **therapies** that shape the admission course.
- Capture conference outcomes, action items, and follow-ups in a consistent place.
- Attach and view relevant documents (PDFs/images) without leaving the workflow.
- Quickly identify patients needing review (for example, “high-risk / cross-check” workflows).

FlightPlan is **not** intended to replace the EHR. Instead, it is a workflow-focused “timeline and coordination layer” that provides a **course-of-stay view** that many EHRs do not present clearly.

FlightPlan is also **not a clinical decision support system**: it is a way to organize and communicate information, not a tool that generates clinical recommendations.

---

## 3) What the current FlightPlan system does today (all major functionality)

This section describes the current system in “what you can do” language. The refactor is intended to preserve these major functions.

### A) Patient and admission management (creating and maintaining records)
**What it does**
- Creates and edits patient records (core demographics and key clinical descriptors as used in FlightPlan).
- Creates and updates admissions (one hospital stay), including key dates used for review workflows.
- Records important status outcomes such as discharge and (when applicable) deceased status.
- Supports operational flags such as “CrossCheck/high-risk” to support prioritization.

**Clinical value**
- Ensures the timeline and event history is tied to the correct admission.
- Enables teams to standardize where “the shared narrative” of the admission lives.

### B) Patient list (the daily starting point)
**What it does**
- Shows a list of current/recent admissions.
- Supports search (name/MRN), filtering, sorting, and paging through results.
- Surfaces operational flags (for example, “CrossCheck/high-risk”) and other status indicators to prioritize review.

**Clinical value**
- Enables rapid triage of which patients need attention.
- Reduces cognitive load by presenting a curated list rather than forcing chart-by-chart searching.

### C) Patient detail workspace (the decision-making view)
The patient detail view combines the timeline visualization with data entry and review.

#### 1) Timeline visualization (“the line graphic”)
**What it is**
- An interactive timeline graph of the admission.
- Displays **locations/units over time** (e.g., pre-op, OR, ICU, floor, cath lab, discharge).
- Displays **clinical status markers** aligned to time (e.g., respiratory support status changes).
- Displays additional markers for events, procedures, and therapies depending on what is documented.

**Deep-dive documentation (exact current behavior, v2):** `docs/FLIGHTPLAN_V2_TIMELINE_LINE_GRAPH_HYPERDOCUMENTATION.md`

**What users can do**
- Scroll/zoom through time; click markers to see details.
- Toggle what categories of information are visible to reduce clutter when needed.

#### 2) Location steps (movement through care settings)
**What it does**
- Records transitions between locations/units with timestamps.
- Supports editing/correction when timing or unit labeling needs updates.

#### 3) Clinical status / “risk” tracking over time
**What it does**
- Captures changes in clinically meaningful status categories.
- Links those changes to the timeline so trajectory is visible across the admission.

#### 4) Clinical events and annotations
**What it does**
- Allows adding structured events and notes (annotations) for clinically meaningful moments.
- Uses standardized labels so events can be consistently displayed and reviewed.

#### 4b) Imaging (where applicable in the workflow)
**What it does**
- Records imaging-related entries (type, notes, and associated files when needed) so they can be reviewed in context of the admission timeline.

#### 5) Bedside procedures
**What it does**
- Records bedside procedures linked to the admission course and (when appropriate) to a location/time.

#### 6) Continuous therapy tracking (e.g., ECMO and other ongoing therapies)
**What it does**
- Records therapies that span time (start/stop intervals), not just single time-point events.

#### 7) Conferences and multidisciplinary planning
**What it does**
- Creates/edits conference entries (type, notes, action items).
- Supports attaching documents to conference items.

#### 8) Feedback, ratings, and suggested edits
**What it does**
- Captures structured feedback (performance/outcome categories depending on workflow).
- Captures suggested edits and review-oriented notes.

#### 9) Course corrections / plan adjustments
**What it does**
- Captures changes to the plan over time that are important to the admission narrative.

#### 10) Documents and attachments (file management)
**What it does**
- Attaches files (PDFs, images, etc.) to a patient/admission and/or specific events.
- Generates thumbnails for quick scanning.
- Includes an in-app document viewer so users can review without leaving the workflow.

#### 11) Administrative “cleanup” (high-impact action)
**What it does**
- Supports removal of records in situations like erroneous/test entries (this is typically restricted because it can permanently remove data).

**Clinical considerations**
- This function is operationally useful, but it must be tightly permissioned and auditable due to patient safety and compliance implications.

### D) User access, roles, and permissions
**What it does**
- Uses organizational identity (enterprise sign-in in production) to determine who the user is.
- Uses role/credential levels to restrict sensitive actions (role-based access control).

### E) Chatbot integration (optional feature)
**What it does today**
- If enabled in configuration, FlightPlan displays a floating chatbot/help button.
- The chatbot itself is external; FlightPlan provides the entry point.

**Clinical considerations**
- Helpful for “how do I…?” workflow questions and navigation help.
- Must be managed to avoid accidental PHI disclosure and to prevent unverified advice being mistaken for clinical guidance.

### F) Database and storage (where information lives)
**What it does today (conceptually)**
- Clinical timeline data (patients, admissions, events, etc.) is stored in a **central database**.
- Attachments are stored in **file storage** (cloud storage), while the database stores the metadata and links tying a file to a patient or event.

---

## 4) The state of the codebase when refactoring started (honest strengths and weaknesses)

This section is about the *software foundation*, not the clinical intent. A system can be clinically excellent and still be built on foundations that are hard to maintain safely.

### Strengths of the current system (what it gets right)
- **Clinically aligned workflow:** The patient list → patient detail timeline pattern matches real clinical review behavior.
- **High-value visualization:** The timeline (line graphic) provides a clear “course-of-stay” view.
- **Comprehensive feature coverage:** Events, conferences, feedback, therapies, and attachments support real operational needs.
- **Speed of past iteration:** The system was able to evolve quickly to meet immediate needs, which is common for early-stage clinical tools.
- **Embedded domain knowledge:** Specialty-specific terminology, locations, and team roles reflect real practice.

### Weaknesses and risks (why change is needed)

#### A) Reliability risk (“small changes can break unrelated things”)
Over time, the codebase evolved into large, tightly coupled parts. The same areas of the software often handle:
- What the user sees on-screen
- What gets saved
- How the timeline graph is assembled
- What permissions apply

When many responsibilities are mixed together, it becomes harder to change one thing without unintended side effects.

#### B) Maintainability risk (“key clinical vocabulary is trapped in the software”)
Many critical lists and definitions—units/locations, status labels, team rosters, event types—are embedded directly in the software. That means:
- Updating terminology or adding new options can require software changes rather than configuration.
- Supporting a new specialty/service line requires substantial development effort and increases risk of inconsistency.

#### C) Data consistency and auditability risk (“the same concept can be stored in different ways”)
Some clinically relevant information is stored in flexible “mixed” structures rather than consistently structured fields. Over time this can lead to:
- Inconsistent data entry patterns
- Increased effort to validate “is the timeline truly correct?”
- More difficulty producing reliable operational reporting

#### D) Performance and scalability risk (“speed varies and can become unpredictable”)
The current system uses caching approaches that can make it feel fast in some cases, but can also create:
- Large in-memory session footprints
- Occasional “stale data” behavior (what you see may lag behind a recent change)
- Slower performance as patient volume and event density grows

#### E) Security and PHI risk (“protections need modernization”)
In a clinical system, security is not optional. A formal review of the codebase identified multiple high-risk patterns typical of older custom applications, including:
- Database access patterns that are harder to secure and audit than modern standards.
- PHI exposure risks if identifiers appear in places they should not (for example, in web addresses).
- Credential and secret-management concerns (e.g., values that should never appear in documentation or source control).

This does not mean the system is “unsafe to use” in day-to-day practice, but it does mean the foundation needs modernization to meet the expectations of a durable clinical platform.

#### F) Testing and change-control gaps (“hard to prove a change is safe”)
The legacy system has limited automated “prove it works” checks. This creates a practical problem:
- Even careful changes can take longer because we must rely more heavily on manual testing.
- Confidence in changes depends on institutional memory and individual expertise rather than repeatable validation.

---

## 5) What we are proposing (the refactored FlightPlan) and what will stay the same

### What will stay the same (clinical intent and workflow)
The refactor is not an attempt to change clinical practice. The intent is to preserve:
- Patient list triage workflow
- Patient detail timeline review workflow
- Timeline visualization (line graphic) as the central “course-of-stay” view
- Event capture (annotations, procedures, therapies, conferences, feedback, course corrections)
- Attachments and document viewing
- Role-based restrictions on sensitive actions

### What will change (the “internal plumbing”)
We are rebuilding FlightPlan into a more standard, modular design. In clinician terms:
- The **screen layer** becomes easier to update without risking the database layer.
- The **data layer** becomes more consistent and more strictly validated (fewer ambiguous fields, fewer edge cases).
- The **security layer** becomes more standardized, reducing PHI exposure risk and strengthening access controls.

### The refactored architecture (plain-language description)
Instead of a single tightly coupled application, the refactored system separates responsibilities:
1. **Frontend (the app you use in the browser):** focuses on user experience, speed, and clarity.
2. **Backend (the data service):** enforces rules, permissions, validation, and provides a consistent way to read/write information.
3. **Database + file storage:** stores structured clinical timeline data and attachments with clearer relationships.

This separation is a standard pattern in modern healthcare software because it is easier to secure, test, and evolve.

### Specialty support (“platform + specialty pack” concept)
Today, many specialty-specific items are embedded in the software (units, labels, team roles). The refactored approach moves toward:
- A stable core (“platform”) for patients/admissions/timeline/events
- Configurable specialty definitions (“specialty packs”) that define:
  - locations/units and their display conventions
  - status categories and labels
  - event types and form options
  - team role categories

Clinically, this means the system can adapt to evolving workflows without requiring code changes for every vocabulary update.

**Governance (how this works in practice):**
- A specialty pack should be **owned** by a designated clinical operations lead / FlightPlan admin group for that service line.
- Changes should be requested through an agreed channel (e.g., a ticket/form/project queue) and reviewed before release.
- Packs should be **versioned** (so changes are traceable and reversible).
- For initial v3 delivery, the specialty pack goal is: **match v2 defaults first**, then evolve safely after parity is validated.

---

## 6) Feature-by-feature: what the refactor will deliver (strengths + weaknesses per area)

This section maps every major feature area to the refactor goal, so there is clarity on what is preserved and what is expected to improve.

### A) Patient and admission management
**Goal in the refactor**
- Preserve the ability to create and maintain patient and admission records that drive the timeline.
- Keep key workflow fields (e.g., review dates and operational flags) while making their meaning and validation more consistent.
- Make updates more traceable (who changed what and when) to support clinical trust.

**Expected strengths**
- Fewer “mystery mismatches” where fields behave differently depending on where they were edited.
- Clearer guardrails around high-impact status changes (e.g., discharge, deceased) and admission selection.

**Possible weaknesses / tradeoffs**
- Some legacy fields may be standardized or clarified, which can feel like “the form changed” even if the workflow is the same.

### B) Patient list
**Goal in the refactor**
- Preserve the “single list to start the day” workflow.
- Improve speed and consistency of filtering/sorting.
- Improve clarity of which data elements are “current” vs “historical”.

**Expected strengths**
- Faster load times and fewer “odd” refresh behaviors.
- Clearer, more consistent filtering across users.

**Possible weaknesses / tradeoffs**
- Some filters or columns may need to be reintroduced in phases if they depend on legacy-only data structures.

### C) Patient detail timeline (line graphic)
**Goal in the refactor**
- Preserve the timeline as the central view.
- Make it easier to maintain and enhance without risking unrelated features.

**Expected strengths**
- More predictable rendering and interaction as admissions get “dense” with events.
- Better support for specialty differences without custom one-off logic.

**Possible weaknesses / tradeoffs**
- A “timeline rewrite” can introduce visual/interaction differences (even if the data is the same).
- Some display behaviors may differ initially (e.g., exact color mappings or labeling) until fully calibrated with clinician feedback.

### D) Location steps (including care team context)
**Goal in the refactor**
- Preserve ability to record and correct transitions.
- Improve validation (e.g., preventing impossible overlaps, clarifying end-times).
 - Make associated context (e.g., team roles recorded during a location step) more consistent and easier to update when workflows change.

**Expected strengths**
- Fewer confusing edge cases (e.g., overlapping stays).
- Cleaner audit trail of edits (who changed what and when).

**Possible weaknesses / tradeoffs**
- Stricter validation may “reject” entries that the old system allowed; we will need a clear workflow for exceptions.

### E) Clinical status / risk tracking
**Goal in the refactor**
- Preserve timeline-linked status changes.
- Make definitions easier to update (configurable labels, categories).

**Expected strengths**
- Clearer and more consistent categorization; easier training for new team members.

**Possible weaknesses / tradeoffs**
- Specialty teams may want different labels and “level” concepts; aligning on shared definitions can take time.

### F) Clinical events, annotations, and imaging
**Goal in the refactor**
- Preserve event entry and timeline markers.
- Improve consistency of event definitions and reduce duplicate/ambiguous labels.
 - Ensure imaging-related entries (where used) remain easy to record and review in timeline context.

**Expected strengths**
- Better searchability and reporting.
- Less variability in how “the same thing” is documented.

**Possible weaknesses / tradeoffs**
- Some legacy event labels may need mapping/translation to a cleaner standardized set.

### G) Bedside procedures
**Goal in the refactor**
- Preserve procedure entry and timeline linkage.
- Improve consistency of procedure types and documentation.

**Expected strengths**
- Cleaner reporting and quality review comparisons.

**Possible weaknesses / tradeoffs**
- Some procedure lists may need to be curated per specialty/site.

### H) Continuous therapies (e.g., ECMO)
**Goal in the refactor**
- Preserve interval-based therapy tracking.
- Improve display and data validation (start/stop logic).

**Expected strengths**
- Fewer “missing stop time” ambiguities; clearer duration visualization.

**Possible weaknesses / tradeoffs**
- Stricter rules may require workflow adjustments for documenting “ongoing” therapies.

### I) Conferences
**Goal in the refactor**
- Preserve conference documentation and action items.
- Improve linkage between conferences, timeline, and attachments.

**Expected strengths**
- More consistent access to prior conference decisions.

**Possible weaknesses / tradeoffs**
- If conference types or templates change, users may experience an adjustment period.

### J) Feedback, ratings, suggested edits
**Goal in the refactor**
- Preserve structured feedback and “suggested edits” workflows.
- Clarify which feedback is “for review” vs part of the longitudinal record.
 - Preserve the ability to control timeline visibility/readability (so the timeline can be “decluttered” when needed).

**Expected strengths**
- Better separation between clinical timeline record and quality-review workflows (if desired by stakeholders).

**Possible weaknesses / tradeoffs**
- Some organizations prefer tighter coupling; others prefer separation—this may require stakeholder alignment.

### K) Course corrections / plan adjustments
**Goal in the refactor**
- Preserve ability to record major plan pivots in a structured way.
- Improve consistency and audit trail.

### L) Attachments and document viewer
**Goal in the refactor**
- Preserve attachment upload/view workflows.
- Improve reliability of thumbnails and document loading.
- Improve permission checks and reduce the chance of “broken links”.

**Expected strengths**
- More robust storage handling and clearer error messages when a file cannot be retrieved.

**Possible weaknesses / tradeoffs**
- File migration can be complex (ensuring every legacy attachment continues to resolve correctly).

### M) User identity, roles, and permissions
**Goal in the refactor**
- Preserve role-based restrictions and enterprise sign-in.
- Make permission logic more consistent and auditable.

**Expected strengths**
- Clearer answers to “who can do what” and “why was this action allowed/blocked?”

**Possible weaknesses / tradeoffs**
- Tightening permission checks may expose legacy inconsistencies (some users may lose access to actions they previously had if those were effectively “unrestricted”).

### N) Administrative cleanup (restricted)
**Goal in the refactor**
- Preserve the operational ability to remove erroneous/test records when necessary.
- Make this action highly permissioned, clearly labeled, and fully auditable.

**Expected strengths**
- Reduced risk of accidental data loss; clearer accountability when cleanup is performed.

**Possible weaknesses / tradeoffs**
- Tighter controls can slow urgent cleanup requests unless operational escalation paths are defined.

### O) Chatbot integration
**Goal in the refactor**
- Keep as optional, intentionally controlled capability.
- Ensure it cannot become a route for PHI leakage.

**Expected strengths**
- Safer integration boundaries and clearer disclaimers on intended use.

**Possible weaknesses / tradeoffs**
- Chatbot availability may be staged or restricted depending on institutional policy.

### P) Database and reporting
**Goal in the refactor**
- Preserve the essential patient/admission/timeline record.
- Improve consistency of how data is stored so reporting is more reliable.

**Expected strengths**
- Easier to answer operational questions with confidence (counts, durations, time-to-event, pathway comparisons).
- Reduced need for “manual interpretation” of mixed-format fields.

**Possible weaknesses / tradeoffs**
- Converting legacy “flexible” fields into cleaner structure takes time and requires careful mapping.

---

## 7) Security and privacy: what changes and why it matters

In clinician terms, the refactor strengthens four protections:

1) **Minimize PHI exposure surfaces**
- Avoid placing identifiers in places that are hard to control (for example, web addresses).
- Ensure logs and errors do not accidentally capture PHI.

2) **Stronger access control consistency**
- Ensure role restrictions apply uniformly across all actions.
- Reduce “implicit access” that can happen when logic is scattered.

3) **Safer database interaction**
- Use modern, standardized patterns that reduce the chance of data leakage or manipulation through malformed inputs.

4) **Better auditability**
- Make it easier to answer: who viewed what, who changed what, and when.

This is essential not only for compliance, but for clinical trust in the system.

---

## 8) Strengths and weaknesses of the refactored approach (system-level)

### Expected strengths
- **Reliability:** fewer regressions; clearer “what changed” when something looks different.
- **Security:** modern protections around PHI, access control, and secret management.
- **Maintainability:** faster, safer improvements; easier onboarding of developers.
- **Configurability:** easier updates to units/status labels/event types without deep code changes.
- **Scalability:** more predictable performance as patient/event volume grows.
- **Quality:** better automated checks to prove changes are safe before deployment.

### Expected weaknesses / risks
- **Transition risk:** any rewrite can temporarily miss edge-case behaviors that clinicians rely on.
- **Change management:** users may need light retraining even when workflows are kept similar.
- **Parallel system complexity:** running legacy and new side-by-side during validation requires coordination.
- **Data migration complexity:** attachments and mixed-format fields need careful mapping to avoid “missing” historical context.
- **More moving parts (behind the scenes):** modern systems separate components; that can increase operational complexity, even if it improves clarity and security.

---

## 9) How we will validate safety and continuity during the refactor

To protect clinical operations, validation will be approached like any high-stakes workflow change:

1) **Phased delivery**
- Deliver core read-only views early (patient list + patient detail timeline view).
- Add editing functions in controlled phases (events, conferences, attachments).

2) **Side-by-side comparison**
- For a defined set of test admissions (de-identified or synthetic where needed), compare:
  - timeline rendering
  - event counts and placement
  - attachment availability

3) **Clinician review checkpoints**
- Scheduled review sessions with representative end-users to confirm:
  - terminology matches practice
  - timeline readability
  - editing workflows match mental models

4) **Go/no-go criteria**
- A clear definition of “ready to use” for each phase (performance, accuracy, permissions).

5) **Rollback plan**
- Legacy remains available during initial rollout windows to prevent clinical disruption.

### Validation “gates” (how we decide what’s ready)

Instead of promising dates we can’t stand behind, we will use clear readiness gates:

| Gate | What it means (clinician view) | Minimum proof |
|------|--------------------------------|---------------|
| Gate 0: Timeline parity | The timeline “line graphic” behaves the same as v2 in read-only mode | Side-by-side comparison on test admissions; “must not break” checklist signed off |
| Gate 1: Attachments parity | Attachments open reliably from timeline and other entry points | Correct documents open; permissions enforced; no missing files |
| Gate 2: Editing parity | Right-click/edit workflows work with correct permissions | Editing produces correct timeline changes; auditability and rollback exist |
| Gate 3: Pilot readiness | A small group can use v3 without disruption | Training/job aids; support channel; fallback to v2 |

If/when calendar dates are published, they will be explicitly labeled as **estimates** unless formally committed.

---

## 10) Frequently asked questions (clinician-focused)

**Will this change clinical care decisions?**  
No. The refactor is about reliability, security, and maintainability of the tool. It does not add automated clinical recommendations or change clinical standards.

**Will the workflow change?**  
The intent is to keep the core workflow (patient list → patient timeline → events/conferences/attachments) the same. For the initial v3 rollout, **parity comes first**; cosmetic “modernization” is intentionally deferred until the workflow and timeline behavior are validated.

**Will historical information be lost?**  
The goal is to preserve historical admissions, events, and attachments. Some legacy fields may be mapped into cleaner structures; when this happens, we will validate that the meaning and timeline placement are preserved.

**Will the timeline “line graphic” change?**  
The goal is **behavioral parity**: same step-style trajectory, same colors/labels, same markers/symbols, same click-to-open callouts, and the same zoom/menu controls. Any differences found during side-by-side validation are treated as **regressions** until reviewed and accepted.  
Deep-dive parity spec (v2): `docs/FLIGHTPLAN_V2_TIMELINE_LINE_GRAPH_HYPERDOCUMENTATION.md`

**Will there be downtime or a cutover period?**  
The goal is **no scheduled downtime** for clinical operations. We plan to deliver in phases and keep the legacy system available during initial rollout windows so you can fall back immediately if something is off. If a cutover window is ever required, it will be announced clearly in advance.

**Will I need training?**  
Likely minimal. Expect a short orientation (quick-start guide + optional 15–30 minute sessions) focused on what is identical vs what is new, plus how to report issues during the pilot.

**Who decides what labels/locations/event types exist?**  
The refactor explicitly moves toward clinician-governed configuration (“specialty packs”) so terminology and options can evolve with practice without requiring deep software changes.

**What about the chatbot—can it see patient information?**  
Chatbot integration is an **optional feature**. If enabled, it will be intentionally constrained and treated as a support/navigation aid, with guardrails to minimize PHI exposure risk aligned with institutional policy.

**How do I report problems or request changes during the transition?**  
Use the designated FlightPlan support channel/project queue (to be communicated before pilot). Please **do not include PHI** in tickets/messages; use MRN-only when required by policy and only in approved systems.

---

## 11) How clinicians can help (optional but high impact)

- Identify the top 5–10 “must not break” workflows and edge cases.
- Provide feedback on timeline readability (what is clutter, what is essential).
- Review proposed terminology/configuration for units, status labels, and event types.
- Participate in short validation sessions before each rollout phase.
- Submit issues/feedback through the designated FlightPlan support channel/project queue (to be communicated before pilot). Please **do not include PHI** in tickets/messages.

---

## 12) Glossary (plain language)

- **Admission:** One hospital stay (a patient can have multiple admissions over time).
- **Timeline / line graphic:** A time-based visual display of locations and events across the admission.
- **Location step:** A recorded movement from one unit/location to another.
- **Clinical status / risk:** A tracked status category over time (e.g., respiratory support state) used to contextualize acuity changes.
- **Annotation:** A structured timeline marker and/or note tied to the course of care.
- **Continuous therapy:** A therapy that spans time with a start and stop, not a single timestamp.
- **Attachment:** A file (PDF/image) linked to the patient/admission or a specific event.
- **Role-based access:** Rules that restrict sensitive actions to specific user groups.

---

## 13) Optional appendix (technical details, if stakeholders request)

This clinician report intentionally avoids deep technical language. If stakeholders need it, a separate appendix can summarize:
- the legacy and target technology stacks
- security remediation themes
- migration approach for database and attachments
- high-level delivery milestones

---

# Critique of This Document

**Date of critique:** 2025-12-19
**Reviewer:** Claude (AI assistant, upon request for honest critique)

> Note: Some items raised below have since been incorporated (continuity commitments table, validation gates, clearer FAQ language, PHI-safe visuals note). This critique is kept for historical context.

## Overall Assessment

This is a well-intentioned document that successfully avoids technical jargon and speaks to clinicians in accessible language. However, it is too long, too repetitive, and too vague on specifics that clinicians would actually need to make decisions or plan their work.

## Strengths

1. **Appropriate tone for audience**: The language is genuinely non-technical. Terms like "internal plumbing" and "the same concept can be stored in different ways" translate abstract software problems into relatable ideas.

2. **Honest about tradeoffs**: Unlike many project documents that oversell benefits and hide risks, this report explicitly lists "possible weaknesses" for each feature area. This builds trust.

3. **Good structure**: Executive summary up front, FAQ section, glossary at the end. A busy clinician can get the gist from section 1 and skip to section 10 for quick answers.

4. **Validation plan is concrete**: Section 9 describes a phased, testable approach with rollback options. This is the kind of safety net clinicians need to hear about.

5. **"How clinicians can help" is valuable**: Section 11 gives actionable ways for stakeholders to participate rather than just being informed.

## Weaknesses and Issues

### 1. Too Long
At 566 lines (~12 pages), this document will not be read in full by most clinicians. The executive summary claims to be "one page" but is actually ~1.5 pages. Busy clinicians will skim, miss important details, and then be surprised later.

**Recommendation**: Cut to 4-5 pages. Move detailed feature-by-feature analysis (section 6) to an appendix.

### 2. Redundant Content
The same information appears multiple times:
- Section 3 describes all features in detail
- Section 6 describes all features again with goals/strengths/weaknesses
- This duplication adds length without adding value

**Recommendation**: Merge sections 3 and 6 into a single, tighter feature overview.

### 3. No Timeline or Milestones
The document repeatedly says "phased delivery" but never says:
- When will Phase 1 be ready?
- How long is the transition period?
- When will the legacy system be retired?

Clinicians cannot plan their workflows without dates. Even rough estimates ("Q2 2025") would be better than nothing.

**Recommendation**: Add a simple milestone table, even if dates are approximate.

### 4. "Specialty Packs" Undefined
Section 5 introduces "specialty packs" as a key concept but never explains:
- Who creates them?
- Who maintains them?
- How does a team request changes to their specialty pack?
- Are they versioned?

This concept is central to the claim that "terminology can evolve without code changes" but the lack of detail makes it feel like vaporware.

**Recommendation**: Either define specialty packs concretely or remove the term and just say "configurable settings."

### 5. Missing Visuals
A report explaining a UI-heavy application contains zero screenshots. Clinicians should see:
- What the current timeline looks like
- What the new timeline might look like (even a mockup)
- Before/after comparisons of any screens that will change

**Recommendation**: Add 3-5 annotated screenshots.

### 6. Overly Diplomatic Language
The "possible weaknesses" sections often hedge rather than being direct:
- "Some legacy fields may need mapping" — which fields?
- "Some filters may need to be reintroduced in phases" — which ones?
- "Visual/interaction differences may occur" — like what?

Clinicians would benefit from specific examples so they know what to watch for.

**Recommendation**: Replace vague hedges with concrete examples, even if hypothetical.

### 7. Chatbot Section Feels Out of Place
The chatbot is mentioned in sections 3E, 6O, and the FAQ, but it's clearly a peripheral feature. Giving it equal weight to core features (timeline, events, conferences) creates a misleading impression of its importance.

**Recommendation**: Move chatbot to a single footnote or "optional features" subsection.

### 8. Assumes Reader Knows FlightPlan
While targeted at current users, the document would be difficult for:
- New clinicians who haven't used FlightPlan
- Administrators evaluating the system
- Leadership making funding decisions

There's no "what is FlightPlan?" introduction beyond the brief executive summary.

**Recommendation**: Add a 1-paragraph "About FlightPlan" section for new readers.

### 9. FAQ Could Be Stronger
The FAQ answers are somewhat generic. Compare:
- Current: "Will there be downtime? We plan to deliver in phases..."
- Better: "Will there be downtime? No scheduled downtime. Both systems will run in parallel during the 6-week transition. If a problem occurs, you can continue using the legacy system immediately."

**Recommendation**: Make FAQ answers more specific and direct.

### 10. No Contact or Feedback Mechanism
The document says clinicians can help but doesn't say:
- Who to contact with questions
- Where to submit feedback
- How to report problems during transition

**Recommendation**: Add a "Questions? Contact..." section with names/emails.

## Structural Recommendations

If I were to reorganize this document:

1. **Page 1**: Executive summary (trim to 0.5 pages)
2. **Page 2**: What FlightPlan is + screenshot
3. **Page 2-3**: What's changing (high-level, 1 page max)
4. **Page 3-4**: Validation plan + timeline with dates
5. **Page 4**: FAQ (trim to 5-6 most important questions)
6. **Page 5**: How to get involved + contacts
7. **Appendix A**: Feature-by-feature details (for those who want depth)
8. **Appendix B**: Glossary

## Verdict

**Grade: B**

This document demonstrates good intentions and clinician empathy, but it needs aggressive editing. The length and repetition will cause most readers to skim rather than engage. The lack of specific dates, concrete examples, and visual aids limits its usefulness as a planning tool.

The writing quality is good. The structure is reasonable. The content is accurate. But "good enough to read" is different from "concise enough to be read," and this document fails the latter test.

**Bottom line**: Cut it in half, add a timeline, add screenshots, and it becomes an A- document.

---

# Critique of the Critique

**Date:** 2025-12-19  
**Reviewer:** Codex (OpenAI)  
**Scope:** Assess the strengths/weaknesses of the critique above (not the refactor plan itself).

## What the critique gets right

- **Length + repetition are the biggest adoption risk.** Clinicians will skim; repeated feature inventories increase the chance they miss the actual “what changes for me” content.
- **Asking for milestones is reasonable.** Even approximate ranges help operations plan staffing, training, and expectations.
- **Missing visuals is a real gap.** A timeline-heavy product is hard to understand without at least one annotated screenshot.
- **“How to give feedback/contact” is essential.** Without a clear path, “clinicians can help” becomes performative.

## Where the critique needs nuance

1) **“Add dates” can backfire if they are speculative.**  
   The critique is right that clinicians need timelines, but it should emphasize: only publish dates that leadership will stand behind, label estimates explicitly, and prefer “gates” (pilot start, parallel run, go/no-go criteria) over precise calendar commitments if uncertainty is high.

2) **“Add screenshots” must include a PHI safety constraint.**  
   The critique should explicitly require de-identified/mock data or redaction guidance. Otherwise it unintentionally encourages putting PHI into a shareable planning doc.

3) **“Chatbot feels out of place” is not obviously true given PHI/compliance risk.**  
   Even if it’s peripheral, chatbot integration can materially affect privacy posture and user trust. The better critique would be: keep it short, clearly label it optional, and emphasize guardrails—rather than removing it entirely.

4) **“Cut it in half” is directionally correct, but “split into layers” may be safer than “delete content.”**  
   A better approach might be: keep a 1–2 page clinician-facing brief, then move deep feature-by-feature material into appendices so leaders/ops can still audit the plan without burdening clinicians.

5) **Contact mechanism suggestion should avoid personal identifiers in repo docs.**  
   Depending on distribution, listing named individuals/emails may be undesirable. The critique should suggest role/group contacts (team alias, ticket link, or “submit feedback via…”), and explicitly warn: don’t send PHI in feedback channels.

## What the critique misses

- **Training and change-management specifics.** Clinicians care about: “Will I need training?”, “What’s the fallback if something breaks?”, “Who is on call?”, and “How do I report urgent issues during rollout?” The critique hints at planning needs but doesn’t call these out.
- **A “what stays the same vs what might change” table.** This is often the single most useful artifact for a clinician-facing refactor document and would align with the stated goal of preserving interface/workflow where possible.
