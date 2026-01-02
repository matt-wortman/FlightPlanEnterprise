# WhereAmI.md — FlightPlan Enterprise (Plain‑English Status)

**Purpose:** This is a plain‑English snapshot for clinicians. Picture a black‑and‑white drawing of the full system. The colored parts show what exists today. The uncolored parts show what is planned but not built yet.

---

## The Big Picture (the outline)

We are rebuilding FlightPlan as a **hospital‑grade clinical platform** that can:
- Record every meaningful care change as it happens
- Rebuild a patient’s story over time (for safety, auditing, and learning)
- Support different specialties without rewriting the core system
- Keep each hospital’s data strictly separate
- Be reliable, secure, and compliant in real clinical use

---

## What’s Colored In (Built So Far)

### ✅ A Working “Core Engine” Exists
We have a working center of the system that can receive care updates and store them in a structured way.

### ✅ A Timeline Foundation Is in Place
We can already store and retrieve timeline events (e.g., admissions, location changes, procedures).  
This is the groundwork for the “care story” view clinicians care about.

### ✅ Early Versions of Key Views Work
We can return:
- Patient summaries
- Admission summaries
- Care plan summaries
- Timeline entries
- Location path (trajectory)

These are not yet “clinician‑ready” screens, but the system can already provide the information that those screens will display.

### ✅ Specialty Support Has Begun
We created a “reference specialty” called **Cardiac** that shows how a specialty can shape what fields and sections appear.  
This proves the core can support more specialties later without rewriting everything.

### ✅ Safe Hospital Boundaries (Basic Version)
The system can already separate data by hospital or tenant (using a hospital ID passed in each request).  
This is an early, lightweight version of full separation.

### ✅ Quality Checks Are Running
We built automated checks so changes are tested every time we run them.  
Right now, we have a strong base of automated tests that cover most of the system.

---

## What’s Still Uncolored (Planned, Not Built Yet)

### ◻️ “Hard Separation” Between Hospitals
We still need the strongest form of separation inside the database itself (not just passing a hospital ID).  
This is critical for enterprise‑grade privacy and compliance.

### ◻️ A Formal Dictionary of Clinical Events
We need a shared clinical “dictionary” that defines every event type, every required field, and how it evolves over time.  
This ensures long‑term consistency and safe upgrades.

### ◻️ Long‑Running Background Updates
We need a always‑on background service that keeps read‑only views up to date without delays or gaps.

### ◻️ Specialty Plug‑Ins That Do Real Work
The cardiac reference is only a placeholder.  
We still need real specialty logic (calculations, validations, specific forms).

### ◻️ Login, Roles, and Permissions
Right now we are not enforcing user login or roles.  
We still need secure sign‑in and permission controls by role.

### ◻️ Operational Readiness
We still need monitoring, alarms, backup/restore drills, and “what to do when something breaks” playbooks.

### ◻️ Full Clinical User Interface
The clinician interface will be handled by another team.  
Our role is to provide the engine and data they can connect to.

---

## Why This Matters

The **foundation** is real: we can already capture care events and rebuild a patient’s story.  
That is the “heart” of the enterprise system.

The remaining work is about **making it safe, scalable, and reliable for real hospitals**: strong data separation, full security, real specialty logic, and operational readiness.

---

## If You Only Remember One Thing

We’ve **colored in the core engine** of the enterprise system.  
The rest of the picture (security, hospital‑grade operations, specialty depth) is still outlined and waiting to be filled in.
