# FlightPlan Database Architecture Analysis

**Last Updated:** 2026-01-02

## Executive Summary

**RECOMMENDATION: REDESIGN** with a flexible multi-specialty architecture

The current database schema is fundamentally sound for its core entities (patients, admissions, locations, events) but contains **hardcoded cardiac-specific terminology and rigid specialty-specific patterns** that make multi-specialty support difficult. Since we're rebuilding from scratch with SQLAlchemy 2.0, this is the ideal time to design a flexible, extensible schema that can serve cardiac care, oncology, orthopedics, and other medical specialties.

### 2026-01 Update: Canonical Trajectory Change Points (v3)

The v3 backend now includes a **change-point** trajectory model aligned to clinician workflow. Each change point captures the active location and the active y-axis state in a single row, and the line persists until the next point.

New tables/views:
- `trajectory_point` (canonical change points)
  - `admission_id`, `occurred_at`, `location_type_id`, `trajectory_state_id`, `sequence`, `recorded_at`, `recorded_by`, `notes`, `corrects_point_id`
- `trajectory_state_type` (specialty-aware y-axis vocabulary)
  - `specialty_id`, `code`, `display_name`, `y_level`, `active`
- `trajectory_segment` view (derived intervals for analytics)
  - `start_time`, `end_time`, `duration_hours`

This replaces the need for paired start/end events when drawing the trajectory line; segments are derived from consecutive change points.

---

## Current Schema Analysis

### Core Tables (Universal - Can Be Retained)

#### Generic Tables (Minimal Changes Needed)
1. **patients** - Universal patient demographics
   - Fields: MRN, LastName, FirstName, DOB, sex, Deceased
   - Issue: `KeyDiagnosis` field name could be more generic

2. **admissions** - Core admission tracking
   - Fields: MRN, ADM, ADMDATE, ReviewDate, CrossCheck
   - Issue: JSON fields (`Status`, `Interventions`, `Diagnosis`) contain cardiac-specific structures

3. **annotations** - Clinical notes and timeline markers
   - Fully generic, no specialty-specific fields

4. **conferences** - Multidisciplinary team meetings
   - Fully generic, no specialty-specific fields

5. **feedbacks** - Performance tracking and outcomes
   - Fully generic structure

6. **course_corrections** - Treatment plan adjustments
   - Fully generic structure

7. **attachments** - File storage references
   - Fully generic structure

8. **users** - User authentication and credentials
   - Fully generic structure

#### Partially Generic Tables (Require Abstraction)

9. **location_steps** - Patient movement through care locations
   - Generic concept: tracking patient location over time
   - Issues:
     - `Location` varchar(50) - contains hardcoded values: "ACCU", "CTOR", "CICU", "Cath", "Pre-op", "DC"
     - `Teams` varchar(500) - JSON structure with cardiac-specific team roles
     - `Extra` varchar(3000) - JSON with specialty-specific fields

10. **location_risks** - Clinical status/acuity tracking
    - Generic concept: tracking patient acuity and clinical status
    - Issues:
      - `Risk` varchar(50) - contains cardiac-specific values: "Intubated / Conv Vent", "ECMO", "Extubated / HFNC"
      - Terminology specific to cardiac/ICU care

11. **bedside_procedures** - Procedures at patient location
    - Generic concept exists
    - Issues:
      - `ProcedureType` contains cardiac-specific procedures

12. **continuous_therapy** - Ongoing treatments (ECMO, CRRT)
    - Generic concept: long-running therapies
    - Issues:
      - `Type` field contains cardiac-specific therapies: "VA ECMO", "VV ECMO", "CRRT"

---

## Cardiac-Specific Components Analysis

### Hardcoded Cardiac Terminology

From `FpCodes.py` analysis:

#### Location Names (Cardiac Units)
```python
locationList = [
    {'category': 'ACCU', 'labels': ['ACCU']},  # Acute Cardiovascular Care Unit
    {'category': 'CTOR', 'labels': ['CTOR', 'CVOR']},  # Cardiac/Cardiovascular OR
    {'category': 'Cath', 'labels': ['CATH', 'Cath']},  # Cardiac Catheterization Lab
    {'category': 'CICU', 'labels': ['CICU']},  # Cardiac Intensive Care Unit
]
```

**Impact**: These are hardcoded in application code AND expected in database values. Oncology would need "Oncology Unit", "Radiation Therapy", "Infusion Center", etc.

#### Risk Status (Respiratory Support - Cardiac/ICU Specific)
```python
respiratory_support_risks_cicu = [
    'Intubated / Conv Vent',
    'Extubated / HFNC',
    'Intubated / BiVent',
    'Intubated / HFOV',
    'Trach / Vent Settings'
]
```

**Impact**: Oncology would need different status markers: "Neutropenic", "Febrile", "Pain Score", "Nausea Level", etc.

#### Continuous Therapy (Cardiac-Specific)
```python
typeNodes = [
    {'label': 'Extracorporeal Membrane Oxygenation (ECMO)', 'value': 'ecmo'},
    {'label': 'Continuous Renal Replacement Therapy (CRRT)', 'value': 'crrt'}
]
```

**Impact**: Oncology would need: "Chemotherapy Infusion", "TPN", "Blood Transfusion", "Immunotherapy", etc.

#### Care Team Roles (Cardiac-Specific)
```python
surgical_team_items = ['Lehenbauer', 'Morales', 'Winlaw', 'Backer']  # CT Surgeons
cath_interventionalist_team_items = ['Batlivala', 'Hirsch', 'Shahanavaz']
cicu_attending_team_items = ['Alten', 'Benscoter', 'Cooper', 'Gist']
accu_attending_team_items = ['Critser', 'Gaies', 'Moore', 'Spar']
```

**Impact**: These are individual names (good for a single institution) but the ROLE TYPES are cardiac-specific. Oncology needs: "Medical Oncologist", "Radiation Oncologist", "Oncology Nurse", "Palliative Care", etc.

---

## Multi-Specialty Requirements Analysis

### What Different Specialties Need

| Specialty | Location Types | Clinical Status | Continuous Therapies | Team Roles |
|-----------|---------------|-----------------|---------------------|------------|
| **Cardiac (Current)** | ACCU, CICU, CTOR, Cath | Intubated, ECMO, Extubated | ECMO, CRRT, VAD | Cardiologist, CT Surgeon, Interventionalist |
| **Oncology** | Oncology Unit, Infusion Center, Radiation Therapy | Neutropenic, Pain Score, Nausea Level | Chemotherapy, Immunotherapy, TPN, Blood Products | Medical Oncologist, Radiation Oncologist, Hematologist |
| **Orthopedics** | Ortho Floor, OR, PT/OT Gym | Weight-bearing Status, Pain Score, ROM | DVT Prophylaxis, Antibiotic Therapy | Orthopedic Surgeon, PT, OT, Pain Management |
| **Neurology** | Neuro ICU, Stroke Unit, Epilepsy Monitoring | GCS Score, Seizure Activity, Stroke Scale | Anti-epileptics, tPA, Anticoagulation | Neurologist, Neurosurgeon, Neuro PT |
| **Transplant** | Transplant ICU, Isolation Unit | Rejection Risk, Infection Risk, Graft Function | Immunosuppressants, Dialysis | Transplant Surgeon, Immunologist, Infectious Disease |

**Key Insight**: Each specialty has fundamentally different:
1. Care locations
2. Clinical status markers
3. Ongoing therapies
4. Team composition
5. Terminology and workflow

---

## Recommended Design: Specialty-Agnostic Schema + Reference Tables

### Core Principle
Replace hardcoded values with foreign keys to specialty-aware configuration tables.

### Schema Design

```sql
-- Core Configuration
CREATE TABLE specialties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,  -- 'cardiac', 'oncology', 'orthopedics'
    display_name VARCHAR(200),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Location Types (Replaces hardcoded "ACCU", "CICU", etc.)
CREATE TABLE location_types (
    id SERIAL PRIMARY KEY,
    specialty_id INT REFERENCES specialties(id),
    code VARCHAR(50) NOT NULL,  -- 'accu', 'cicu', 'chemo_infusion'
    display_name VARCHAR(200),  -- 'Acute Cardiovascular Care Unit'
    category VARCHAR(50),  -- 'icu', 'ward', 'procedure_area', 'discharge'
    sort_order INT,
    color_scheme JSONB,  -- {line_color, ecmo_color, annotation_color}
    active BOOLEAN DEFAULT true,
    UNIQUE(specialty_id, code)
);

-- Clinical Status Types (Replaces hardcoded "Intubated", "ECMO", etc.)
CREATE TABLE clinical_status_types (
    id SERIAL PRIMARY KEY,
    specialty_id INT REFERENCES specialties(id),
    code VARCHAR(50) NOT NULL,
    display_name VARCHAR(200),
    category VARCHAR(50),  -- 'respiratory', 'infection', 'mobility'
    acuity_level INT,  -- 1=low, 5=high (for sorting/filtering)
    active BOOLEAN DEFAULT true,
    UNIQUE(specialty_id, code)
);

-- Team Role Types (Replaces hardcoded "Cardiologist", "Surgeon", etc.)
CREATE TABLE team_role_types (
    id SERIAL PRIMARY KEY,
    specialty_id INT REFERENCES specialties(id),
    code VARCHAR(50) NOT NULL,
    display_name VARCHAR(200),
    category VARCHAR(50),  -- 'physician', 'nursing', 'allied_health', 'support'
    sort_order INT,
    active BOOLEAN DEFAULT true,
    UNIQUE(specialty_id, code)
);

-- Therapy Types (Replaces hardcoded ECMO, CRRT, etc.)
CREATE TABLE therapy_types (
    id SERIAL PRIMARY KEY,
    specialty_id INT REFERENCES specialties(id),
    code VARCHAR(50) NOT NULL,
    display_name VARCHAR(200),
    category VARCHAR(50),  -- 'mechanical_support', 'medication', 'procedure'
    requires_monitoring BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    UNIQUE(specialty_id, code)
);

-- Procedure Types (Replaces hardcoded procedure lists)
CREATE TABLE procedure_types (
    id SERIAL PRIMARY KEY,
    specialty_id INT REFERENCES specialties(id),
    code VARCHAR(50) NOT NULL,
    display_name VARCHAR(200),
    category VARCHAR(50),  -- 'surgical', 'interventional', 'diagnostic'
    acuity_level INT,
    active BOOLEAN DEFAULT true,
    UNIQUE(specialty_id, code)
);
```

### Modified Core Tables

```sql
CREATE TABLE patients (
    mrn VARCHAR(50) PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    sex VARCHAR(20),
    primary_specialty_id INT REFERENCES specialties(id),
    key_diagnosis TEXT,
    deceased BOOLEAN DEFAULT false,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admissions (
    id SERIAL PRIMARY KEY,
    mrn VARCHAR(50) REFERENCES patients(mrn),
    admission_number INT NOT NULL,
    specialty_id INT REFERENCES specialties(id),
    admission_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP,
    review_date TIMESTAMP,
    cross_check BOOLEAN DEFAULT false,
    current_location_type_id INT REFERENCES location_types(id),
    current_acuity_level INT,
    specialty_metadata JSONB,  -- Only for truly variable data
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mrn, admission_number)
);

CREATE TABLE location_steps (
    id SERIAL PRIMARY KEY,
    mrn VARCHAR(50) NOT NULL,
    admission_number INT NOT NULL,
    location_type_id INT REFERENCES location_types(id),
    entry_datetime TIMESTAMP NOT NULL,
    weight VARCHAR(50),
    notes TEXT,
    extra_data JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mrn, admission_number) REFERENCES admissions(mrn, admission_number)
);

CREATE TABLE location_clinical_status (
    id SERIAL PRIMARY KEY,
    location_step_id INT REFERENCES location_steps(id) ON DELETE CASCADE,
    clinical_status_type_id INT REFERENCES clinical_status_types(id),
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    notes TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE care_team_assignments (
    id SERIAL PRIMARY KEY,
    location_step_id INT REFERENCES location_steps(id) ON DELETE CASCADE,
    team_role_type_id INT REFERENCES team_role_types(id),
    staff_name VARCHAR(200),
    shift_type VARCHAR(50),  -- 'day', 'night', 'on-call'
    start_datetime TIMESTAMP,
    end_datetime TIMESTAMP,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE continuous_therapies (
    id SERIAL PRIMARY KEY,
    mrn VARCHAR(50) NOT NULL,
    admission_number INT NOT NULL,
    therapy_type_id INT REFERENCES therapy_types(id),
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    status VARCHAR(50),  -- 'active', 'discontinued', 'completed'
    notes TEXT,
    attachment_keys TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mrn, admission_number) REFERENCES admissions(mrn, admission_number)
);

CREATE TABLE bedside_procedures (
    id SERIAL PRIMARY KEY,
    location_step_id INT REFERENCES location_steps(id) ON DELETE CASCADE,
    procedure_type_id INT REFERENCES procedure_types(id),
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    notes TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Annotations, Conferences, Feedbacks, Attachments remain generic
```

---

## Benefits of This Design

| Benefit | Description |
|---------|-------------|
| **Multi-Specialty Support** | Add new specialties by inserting configuration data (no code deployment) |
| **Type Safety** | Foreign key constraints enforce data integrity |
| **Query Performance** | Indexed foreign keys for fast queries |
| **Maintainability** | Configuration changes don't require code deployment |
| **Migration Path** | Can migrate incrementally (one table at a time) |
| **Internationalization Ready** | `display_name` field can be replaced with i18n keys |

---

## Implementation Timeline

- **Week 1**: Configuration schema + cardiac seed data
- **Week 2**: Core table migrations + data migration
- **Week 3-4**: Application layer updates + API development
- **Week 5**: Add oncology specialty + validation
- **Week 6**: Testing, documentation, deployment prep

---

## File Structure

```
flightplan-v3/backend/alembic/versions/
├── 001_create_specialty_configuration.py
├── 002_create_core_entities.py
├── 003_create_location_tracking.py
├── 004_create_clinical_events.py
├── 005_create_attachments.py
├── 006_create_therapies_procedures.py
└── seeds/
    ├── cardiac_specialty.sql
    ├── oncology_specialty.sql
    └── users_and_permissions.sql
```
