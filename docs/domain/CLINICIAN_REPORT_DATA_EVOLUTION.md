# FlightPlan Data Architecture Evolution: A Clinical Perspective

**For Clinical Staff, Quality Officers, and Compliance Teams**
**Date:** December 2025

---

## Executive Summary

FlightPlan has undergone a significant architectural transformation from version 2 to version 3, with an ongoing event-stream modernization effort. This report explains these changes in clinical terms—why they matter for your daily workflow, how they improve the reliability of your analytics, and what they mean for patient privacy compliance.

**Key Benefits:**
- **For Clinicians:** Faster, more reliable access to patient timelines and care trajectories
- **For Quality/Analytics Teams:** Complete audit trails enabling accurate retrospective analysis
- **For Compliance Officers:** PHI protection built into the architecture, not bolted on

**2026 Update:** The timeline now uses a **change-point trajectory model** (`trajectory_point`) that captures location and clinical state together at each documented change. This mirrors clinician workflow (no explicit end events) and produces the same step-function line in the UI while improving auditability.

---

## Part 1: The Problems We Solved (Moving Away from v2)

### 1.1 The MRN Exposure Risk

**What was happening:** In v2, the Medical Record Number (MRN) was the primary identifier throughout the system. While MRNs were encrypted in browser URLs, they existed in plain text in:
- Database tables
- System logs
- Export files
- Error messages
- API responses

**Why this matters clinically:** MRN is Protected Health Information (PHI) under HIPAA. If someone accessed a database backup, log file, or even saw an error message, they could potentially link patient data to real identities.

**Real-world example:** A quality analyst exports a CSV for an outcomes study. In v2, that file contained MRNs in plain text—a PHI breach waiting to happen if the file was emailed or stored on an unsecured drive.

**The v3 solution:** Every patient now has a UUID (Universally Unique Identifier)—a random string like `f47ac10b-58cc-4372-a567-0e02b2c3d479`. This UUID appears in URLs, exports, and logs. The MRN exists only in one protected column, accessed only when clinically necessary. You can share a patient's FlightPlan link without exposing their identity.

---

### 1.2 Data Integrity Was Not Enforced

**What was happening:** The v2 database had no enforced relationships between tables. The software *assumed* every admission belonged to a valid patient, but the database itself didn't verify this.

**Why this matters clinically:** Without database-enforced relationships:
- Orphaned records could accumulate (admissions without patients, procedures without admissions)
- Cascade deletes could fail silently (delete a patient but their admissions remain, creating ghost data)
- Analytics queries could return inconsistent results

**Real-world example:** A nurse documents a procedure on an admission. The database accepts this even if the admission ID doesn't exist—creating a procedure record floating in space. Your quality dashboard shows "1,247 total procedures" but some of them belong to non-existent admissions.

**The v3 solution:** Every relationship is enforced with foreign key constraints. The database itself refuses to accept orphaned data. Delete a patient, and all their admissions, procedures, and events are automatically and atomically removed. Your counts are always consistent.

---

### 1.3 Clinical Data Stored as Unstructured Text

**What was happening:** Complex clinical data (team assignments, diagnoses, risk statuses) were stored as JSON text strings in varchar columns. No validation occurred—the database accepted anything.

**Why this matters clinically:**
- No guarantee that "Intubated" was spelled consistently (vs "intubated", "Intub", "INTUBATED")
- Risk status levels weren't enforced (a user could enter "Extubated-kinda-maybe")
- Analytics required extensive data cleaning before any analysis
- Reports could miss patients due to spelling variations

**Real-world example:** You want to count all patients who were intubated during their CICU stay. In v2, you'd need to search for every possible spelling variation. A typo in the source meant that patient was invisible to your query.

**The v3 solution:** All categorical data uses defined types with explicit allowed values:
- Location types: `CICU`, `OR`, `ACCU`, `Ward`, `Discharge` (not free text)
- Clinical statuses: Standardized codes like `INTUBATED`, `EXTUBATED`, `NEUTROPENIC`
- Acuity levels: Integer scale 1-5 (enforced by database constraint)

If a clinician tries to enter an invalid status, the system rejects it immediately rather than accepting garbage data.

---

### 1.4 No Audit Trail for Clinical Changes

**What was happening:** Every record had a `username` and `activity_date` field showing who last modified it and when. But:
- No history of previous values
- No way to see what changed, only that *something* changed
- No way to reconstruct patient state at a prior point in time

**Why this matters clinically:**
- Quality reviews often need to know: "What was the patient's status at 3 AM when the code was called?"
- Incident investigations require before/after comparisons
- Retrospective studies need accurate historical state, not current state

**Real-world example:** An M&M conference is reviewing a patient who deteriorated overnight. In v2, you can see the current documented status, but you cannot see what was documented at 2 AM versus what was documented at 6 AM. If someone updated the record after the fact, you'd never know.

**The v3 solution:** Event-sourced architecture (detailed in Part 3) captures every change as an immutable event. We can now answer: "At 3:17 AM on January 15th, what was this patient's documented location, clinical status, and care team?"

---

### 1.5 SQL Injection Vulnerabilities

**What was happening:** Many database queries in v2 were built by concatenating strings directly into SQL statements.

**Why this matters:** This is a critical security vulnerability. A malicious user could potentially inject SQL commands through input fields, potentially accessing, modifying, or deleting data they shouldn't touch.

**The v3 solution:** All database access uses SQLAlchemy ORM with parameterized queries. User input is never directly concatenated into SQL. The database driver itself prevents injection attacks.

---

## Part 2: What v3 Architecture Delivers

### 2.1 Specialty-Agnostic Design

**The problem v3 solves:** V2 was built specifically for cardiac surgery. Location types (ACCU, CICU, CTOR), risk levels, and team structures were hardcoded for one specialty.

**The v3 architecture:** Everything clinical is configurable per specialty:

| Configuration Type | Cardiac Example | Oncology Example |
|-------------------|-----------------|------------------|
| Locations | ACCU, CICU, CTOR, Cath Lab | Infusion Center, Oncology Ward, Procedure Suite |
| Clinical Statuses | Intubated, On ECMO, Extubated | Neutropenic, Actively Infusing, Post-Chemo Day 7 |
| Therapy Types | ECMO, Dialysis, Pacing | Chemotherapy Regimen, Immunotherapy, Radiation |
| Team Roles | Cardiac Surgeon, Perfusionist | Medical Oncologist, Oncology Nurse Navigator |

**What this means for you:** Adding a new specialty no longer requires code changes. A clinical administrator can configure location types, status codes, and team roles through the system. Your dashboards automatically adapt.

---

### 2.2 Modern Data Validation

**Every piece of data entering v3 passes through validation layers:**

1. **API Layer (Pydantic schemas):** Data types, required fields, and format validation
2. **Business Logic Layer:** Clinical rules (e.g., discharge date cannot precede admission date)
3. **Database Layer:** Constraints, foreign keys, unique indexes

**Real-world example:** A resident tries to document a surgery date in the future for a patient marked as discharged. V2 would accept this contradictory data. V3 rejects it with a clear error message: "Surgery date cannot be after discharge date."

---

### 2.3 Length of Stay Calculated Correctly

**V2 problem:** Length of stay (LOS) was calculated in various places with inconsistent logic. Null dates, timezone issues, and midnight-crossing calculations produced different numbers depending on which report you ran.

**V3 solution:** LOS is a computed property on the Admission model with documented, tested logic:

```
Length of Stay = (Discharge Date - Admission Date) in days
- Returns null if patient not yet discharged
- Handles timezone correctly (all dates stored in UTC)
- Consistent across all reports and dashboards
```

---

### 2.4 Timeline Reconstruction is Now Possible

**The clinical need:** Patient care is a continuous journey. Understanding that journey—where they were, what their status was, who was caring for them—requires reconstructing the timeline accurately.

**V2 limitation:** The timeline was derived from scattered snapshot data. If someone edited a past record, the "history" changed. There was no way to distinguish "what actually happened" from "what was later documented."

**V3 capability:** The event stream architecture (Part 3) maintains an immutable record of every documented event. We can now:

- Reconstruct exactly what was documented at any point in time
- Show corrections as corrections (linked to what they corrected)
- Generate accurate temporal analytics without data cleaning

---

## Part 3: Event Stream Architecture (The Analytics Foundation)

### 3.1 Why Event Sourcing?

Traditional databases store current state: "The patient is currently in CICU." Event sourcing stores what happened: "The patient arrived in CICU at 14:00 on January 15th."

**The difference for analytics:**

| Question | Snapshot Model (v2) | Event Model (v3) |
|----------|-------------------|------------------|
| Where is the patient now? | Direct lookup | Replay events to current |
| Where was patient at 3 AM? | Unknown (data overwritten) | Replay events to 3 AM |
| How long in each location? | Calculate from start/end (if recorded) | Sum duration between arrival/departure events |
| What changed after the code? | Unknown | Compare events before/after timestamp |
| Were there documentation corrections? | Unknown | Corrections are explicit events |

---

### 3.2 The Four Event Streams

We've implemented four clinical event streams that capture the core patient journey:

#### **1. Location Events**
Captures: Patient arriving at or departing from a care location

```
Event Types: arrival, departure
Example:
  - 08:00 arrival at Pre-Op
  - 09:15 departure from Pre-Op
  - 09:20 arrival at OR
  - 14:30 departure from OR
  - 14:45 arrival at CICU
```

**Analytics enabled:** Accurate time-in-location, transfer patterns, throughput analysis

#### **2. Clinical Status Events**
Captures: Changes in clinical state (intubation, acuity level changes)

```
Event Types: started, ended
Example:
  - 09:30 started: Intubated (severity: 4)
  - 14:30 ended: Intubated
  - 14:35 started: Extubated (severity: 3)
```

**Analytics enabled:** Time on ventilator, acuity trends, status change patterns

#### **3. Intervention Events**
Captures: Therapies and procedures through their lifecycle

```
Event Types: planned, started, paused, resumed, completed, cancelled
Example:
  - 08:00 planned: ECMO
  - 10:30 started: ECMO
  - Day 5, 16:00 completed: ECMO (outcome: successful)
```

**Analytics enabled:** Procedure volumes, therapy durations, completion rates, complication tracking

#### **4. Care Team Events**
Captures: Staff assignments and handoffs

```
Event Types: assigned, unassigned
Example:
  - 07:00 assigned: Dr. Smith (Cardiac Surgeon)
  - 07:00 assigned: RN Johnson (Primary Nurse, Day Shift)
  - 19:00 unassigned: RN Johnson
  - 19:00 assigned: RN Williams (Primary Nurse, Night Shift)
```

**Analytics enabled:** Staffing patterns, handoff timing, team composition analysis

---

### 3.3 Immutability and Corrections

**Key principle:** Events are never modified or deleted. They are append-only.

**Handling corrections:** When documentation needs to be corrected, we create a new event that explicitly references the original:

```
Original Event:
  ID: 1001
  Type: arrival
  Location: CICU
  Occurred_at: 2025-01-15 14:45

Correction Event:
  ID: 1042
  Type: arrival
  Location: ACCU  (corrected value)
  Occurred_at: 2025-01-15 14:45
  Corrects_event_id: 1001  (links to original)
  Notes: "Originally documented as CICU in error"
```

**Why this matters:** Corrections are transparent. Quality reviewers can see both what was originally documented and what was corrected. This supports honest retrospective analysis and incident review.

---

### 3.4 Migration Traceability

All events include metadata about their origin:

| Field | Purpose |
|-------|---------|
| `recorded_at` | When this event was entered into the system |
| `recorded_by` | Who documented this event |
| `source_table` | If migrated from v2, which table it came from |
| `source_record_id` | The original v2 record ID |
| `migration_run_id` | Which migration batch imported this event |

**Why this matters for compliance:** Auditors can trace any event back to its origin. If a question arises about legacy data, we can demonstrate exactly how it was transformed during migration.

---

## Part 4: Security and Compliance Improvements

### 4.1 PHI Protection Summary

| Risk | V2 Status | V3 Status |
|------|-----------|-----------|
| MRN in URLs | Encrypted (reversible) | UUID (opaque, not derived from MRN) |
| MRN in database | Plain text, primary key | Single column, not in URLs/exports |
| MRN in logs | Could appear in errors | Never logged |
| MRN in exports | Required manual removal | UUID-based by default |
| MRN in API responses | Included | Excluded unless explicit clinical need |

### 4.2 Access Control

| Capability | V2 | V3 |
|------------|----|----|
| Role-based access | 4 credential levels (1-4) | Named roles (admin, editor, viewer) |
| Specialty filtering | No | Yes - users can be scoped to specialty |
| Audit of access | Activity date only | Full audit trail |
| Azure AD integration | No | Yes (production) |

### 4.3 Data Integrity Guarantees

| Protection | V2 | V3 |
|------------|----|----|
| Foreign key enforcement | Application only | Database + application |
| Unique constraint enforcement | Partial | Complete |
| Valid value enforcement | None | Check constraints + enums |
| Transaction safety | Manual | Automatic (SQLAlchemy sessions) |

### 4.4 Audit Trail for HIPAA/Joint Commission

The event-sourced architecture provides:

1. **Immutable record of all clinical events** - No modification without trace
2. **Correction lineage** - Every correction links to what it corrected
3. **User attribution** - Every event records who documented it
4. **Timestamp accuracy** - UTC timestamps with documented precision
5. **Migration provenance** - Legacy data traced to its source

**For Joint Commission audits:** You can now demonstrate exactly what was documented, when, by whom, and if corrections were made.

---

## Part 5: Real-World Impact Examples

### Example 1: Retrospective Outcome Study

**Scenario:** The quality team wants to analyze 30-day readmission rates for ECMO patients.

**V2 approach:**
1. Export all admissions to Excel
2. Filter for "ECMO" in the therapy notes (hope spelling is consistent)
3. Manually calculate ECMO duration from scattered date fields
4. Link to readmission data (no reliable patient UUID)
5. Extensive data cleaning before any analysis
6. Results may miss patients due to spelling variations

**V3 approach:**
1. Query `intervention_events` for `therapy_type='ECMO'` with `event_type='started'` and `event_type='completed'`
2. Calculate duration directly from timestamps
3. Use `patient_id` UUID to reliably link admissions
4. Clean, consistent data ready for analysis
5. Complete capture—no spelling variations to miss

**Time saved:** Days of data cleaning reduced to minutes of query writing.

---

### Example 2: Incident Investigation

**Scenario:** A patient deteriorated at 3 AM. The M&M conference needs to understand the care timeline.

**V2 approach:**
- Look at current documentation (may have been updated after the incident)
- Interview staff to reconstruct what happened
- No way to verify if documentation was added or changed after the event
- Incomplete picture, subject to recall bias

**V3 approach:**
- Query event streams with `occurred_at < '2025-01-15 03:00'`
- See exactly what was documented before the deterioration
- Compare to events documented after
- If corrections were made, see them explicitly linked
- Complete, verifiable timeline

**Impact:** Objective, complete timeline supporting honest quality review.

---

### Example 3: Staffing Pattern Analysis

**Scenario:** Nursing leadership wants to understand handoff patterns in CICU.

**V2 approach:**
- Team assignments stored as JSON blobs in admission records
- No temporal dimension—only "current" team visible
- Cannot determine when handoffs occurred
- Manual chart review required

**V3 approach:**
- Query `care_team_events` filtered by location
- Calculate handoff times from `assigned`/`unassigned` event pairs
- Analyze shift timing, overlap periods, coverage gaps
- Dashboard-ready data

**Impact:** Data-driven staffing decisions instead of anecdotal observation.

---

### Example 4: PHI-Safe Data Sharing

**Scenario:** A research collaborator needs FlightPlan timeline data for a multi-center study.

**V2 approach:**
- Export contains MRN in multiple places
- Manual de-identification required
- Risk of PHI exposure if step missed
- Each export requires careful review

**V3 approach:**
- Export uses UUID identifiers
- MRN never included unless explicitly requested
- Study-safe by default
- Shareable without additional de-identification steps

**Impact:** Faster, safer research data sharing.

---

## Part 6: What's Coming Next (OMOP Foundation)

### Why OMOP Matters

OMOP (Observational Medical Outcomes Partnership) is a common data model used across hundreds of healthcare institutions worldwide. Mapping FlightPlan data to OMOP enables:

- **Multi-center studies:** Compare outcomes with other institutions
- **Federated learning:** Train AI models across sites without sharing raw data
- **Regulatory submissions:** Standard format for FDA and research submissions
- **Benchmarking:** Compare your outcomes to national/international benchmarks

### How Event Streams Enable OMOP

The event stream architecture we're building is the **foundation** for OMOP mapping:

```
FlightPlan Event Streams → OMOP Vocabulary Mapping → OMOP CDM Tables
     (immutable)              (configuration)          (export)
```

Each clinical status type, procedure type, and therapy type can be mapped to standard OMOP concept IDs. Because our events are immutable and timestamped, they translate cleanly to OMOP's temporal model.

### Current Status

**V1 (Current):** Event stream infrastructure, migration tooling, hybrid model
**V2 (Future):** OMOP concept mapping, export capabilities
**V3 (Future):** Federated learning integration

---

## Conclusion

The evolution from FlightPlan v2 to v3 represents more than a technology upgrade—it's a fundamental improvement in how clinical data is captured, protected, and analyzed.

**For day-to-day clinical work:**
- Faster, more reliable patient timelines
- Configuration without code changes
- Reduced documentation errors through validation

**For quality and analytics:**
- Complete, auditable event history
- Accurate retrospective analysis
- Clean data ready for research

**For compliance and security:**
- PHI protected by design
- Immutable audit trails
- Transparent correction handling

The event-sourced architecture being deployed now creates the foundation for OMOP integration and multi-center analytics in the future. Your careful documentation today becomes the high-quality data that drives better outcomes tomorrow.

---

## Questions?

For technical questions about the data architecture: Contact the FlightPlan development team
For clinical workflow questions: Contact your FlightPlan clinical champion
For compliance questions: Contact your institution's Privacy Officer

---

*Document Version: 1.0*
*Last Updated: December 2025*
*Classification: Internal - Clinical Staff*
