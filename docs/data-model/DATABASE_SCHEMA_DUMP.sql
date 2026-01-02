-- FlightPlan v3/v4 Database Schema Dump
-- Source: flightplan-v3/backend/flightplan_dev.db (SQLite)
-- Generated: 2025-12-31
--
-- This schema contains:
--   - v3 Entity Tables (patients, admissions, location_steps, etc.)
--   - v3 Reference/Lookup Tables (specialties, location_types, clinical_status_types, etc.)
--   - v4 Event Tables (location_events, clinical_status_events, intervention_events, etc.)
--   - v4 Analytics Tables (fact_event, admission_day, outcome_event)
--   - Projection Views (v_location_intervals, v_clinical_status_intervals, etc.)
--
-- Note: This is SQLite syntax. Some constraints and types differ from SQL Server.
-- For SQL Server deployment, use Alembic migrations which handle cross-database compatibility.

-- ============================================================================
-- REFERENCE/LOOKUP TABLES (v3)
-- ============================================================================

CREATE TABLE specialties (
	id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	description TEXT,
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_specialties PRIMARY KEY (id),
	CONSTRAINT uq_specialties_name UNIQUE (name)
);

CREATE TABLE users (
	id INTEGER NOT NULL,
	username VARCHAR(100) NOT NULL,
	email VARCHAR(255),
	display_name VARCHAR(200),
	role VARCHAR(50) NOT NULL,
	credentials VARCHAR(50),
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_users PRIMARY KEY (id),
	CONSTRAINT uq_users_username UNIQUE (username),
	CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TABLE location_types (
	id INTEGER NOT NULL,
	specialty_id INTEGER NOT NULL,
	code VARCHAR(50) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	category VARCHAR(50),
	sort_order INTEGER NOT NULL,
	color_scheme JSON,
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_location_types PRIMARY KEY (id),
	CONSTRAINT uq_location_type_code UNIQUE (specialty_id, code),
	CONSTRAINT fk_location_types_specialty_id_specialties FOREIGN KEY(specialty_id) REFERENCES specialties (id)
);

CREATE TABLE clinical_status_types (
	id INTEGER NOT NULL,
	specialty_id INTEGER NOT NULL,
	code VARCHAR(50) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	category VARCHAR(50),
	acuity_level INTEGER NOT NULL,
	color VARCHAR(50),
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_clinical_status_types PRIMARY KEY (id),
	CONSTRAINT uq_clinical_status_type_code UNIQUE (specialty_id, code),
	CONSTRAINT fk_clinical_status_types_specialty_id_specialties FOREIGN KEY(specialty_id) REFERENCES specialties (id)
);

CREATE TABLE team_role_types (
	id INTEGER NOT NULL,
	specialty_id INTEGER NOT NULL,
	code VARCHAR(50) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	category VARCHAR(50),
	sort_order INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_team_role_types PRIMARY KEY (id),
	CONSTRAINT uq_team_role_type_code UNIQUE (specialty_id, code),
	CONSTRAINT fk_team_role_types_specialty_id_specialties FOREIGN KEY(specialty_id) REFERENCES specialties (id)
);

CREATE TABLE therapy_types (
	id INTEGER NOT NULL,
	specialty_id INTEGER NOT NULL,
	code VARCHAR(50) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	category VARCHAR(50),
	requires_monitoring BOOLEAN NOT NULL,
	color VARCHAR(50),
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_therapy_types PRIMARY KEY (id),
	CONSTRAINT uq_therapy_type_code UNIQUE (specialty_id, code),
	CONSTRAINT fk_therapy_types_specialty_id_specialties FOREIGN KEY(specialty_id) REFERENCES specialties (id)
);

CREATE TABLE procedure_types (
	id INTEGER NOT NULL,
	specialty_id INTEGER NOT NULL,
	code VARCHAR(50) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	category VARCHAR(50),
	acuity_level INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_procedure_types PRIMARY KEY (id),
	CONSTRAINT uq_procedure_type_code UNIQUE (specialty_id, code),
	CONSTRAINT fk_procedure_types_specialty_id_specialties FOREIGN KEY(specialty_id) REFERENCES specialties (id)
);

CREATE TABLE staff (
	id INTEGER NOT NULL,
	external_id VARCHAR(100),
	display_name VARCHAR(200) NOT NULL,
	credentials VARCHAR(50),
	specialty VARCHAR(100),
	contact_method VARCHAR(50),
	contact_value VARCHAR(100),
	active BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_staff PRIMARY KEY (id)
);

-- ============================================================================
-- ENTITY TABLES (v3)
-- ============================================================================

CREATE TABLE patients (
	id CHAR(32) NOT NULL,                    -- UUID stored without hyphens
	mrn VARCHAR(50) NOT NULL,
	last_name VARCHAR(100) NOT NULL,
	first_name VARCHAR(100) NOT NULL,
	dob DATE NOT NULL,
	sex VARCHAR(20),
	primary_specialty_id INTEGER,
	key_diagnosis TEXT,
	deceased BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_patients PRIMARY KEY (id),
	CONSTRAINT fk_patients_primary_specialty_id_specialties FOREIGN KEY(primary_specialty_id) REFERENCES specialties (id)
);

CREATE UNIQUE INDEX ix_patients_mrn ON patients (mrn);

CREATE TABLE admissions (
	id INTEGER NOT NULL,
	uuid CHAR(32) NOT NULL,                  -- UUID stored without hyphens
	patient_id CHAR(32) NOT NULL,
	admission_number INTEGER NOT NULL,
	specialty_id INTEGER NOT NULL,
	admission_date DATETIME NOT NULL,
	discharge_date DATETIME,
	review_date DATETIME,
	surgery_date DATETIME,
	current_location_type_id INTEGER,
	current_acuity_level INTEGER,
	cross_check BOOLEAN NOT NULL,
	specialty_metadata JSON,
	notes TEXT,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_admissions PRIMARY KEY (id),
	CONSTRAINT uq_admission_patient_number UNIQUE (patient_id, admission_number),
	CONSTRAINT uq_admissions_uuid UNIQUE (uuid),
	CONSTRAINT fk_admissions_patient_id_patients FOREIGN KEY(patient_id) REFERENCES patients (id),
	CONSTRAINT fk_admissions_specialty_id_specialties FOREIGN KEY(specialty_id) REFERENCES specialties (id),
	CONSTRAINT fk_admissions_current_location_type_id_location_types FOREIGN KEY(current_location_type_id) REFERENCES location_types (id)
);

CREATE INDEX ix_admissions_dates ON admissions (admission_date, discharge_date);

-- ============================================================================
-- OPERATIONAL TABLES (v3 - Mutable)
-- ============================================================================

CREATE TABLE location_steps (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	location_type_id INTEGER NOT NULL,
	entry_datetime DATETIME NOT NULL,
	exit_datetime DATETIME,
	weight VARCHAR(50),
	notes TEXT,
	extra_data JSON,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_location_steps PRIMARY KEY (id),
	CONSTRAINT fk_location_steps_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT fk_location_steps_location_type_id_location_types FOREIGN KEY(location_type_id) REFERENCES location_types (id)
);

CREATE INDEX ix_location_steps_timeline ON location_steps (admission_id, entry_datetime);

CREATE TABLE annotations (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	annotation_datetime DATETIME NOT NULL,
	title VARCHAR(200),
	content TEXT NOT NULL,
	category VARCHAR(50),
	color VARCHAR(50),
	pinned BOOLEAN NOT NULL,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_annotations PRIMARY KEY (id),
	CONSTRAINT fk_annotations_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE
);

CREATE INDEX ix_annotations_timeline ON annotations (admission_id, annotation_datetime);

CREATE TABLE conferences (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	conference_datetime DATETIME NOT NULL,
	conference_type VARCHAR(100),
	title VARCHAR(200),
	summary TEXT,
	decisions TEXT,
	attendees TEXT,
	follow_up_required BOOLEAN NOT NULL,
	follow_up_notes TEXT,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_conferences PRIMARY KEY (id),
	CONSTRAINT fk_conferences_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE
);

CREATE TABLE feedbacks (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	feedback_datetime DATETIME NOT NULL,
	rating INTEGER,
	rating_category VARCHAR(100),
	feedback_type VARCHAR(100),
	comments TEXT,
	source VARCHAR(100),
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_feedbacks PRIMARY KEY (id),
	CONSTRAINT fk_feedbacks_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE
);

CREATE TABLE course_corrections (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	correction_datetime DATETIME NOT NULL,
	title VARCHAR(200),
	previous_plan TEXT,
	new_plan TEXT NOT NULL,
	rationale TEXT,
	severity VARCHAR(50),
	category VARCHAR(100),
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_course_corrections PRIMARY KEY (id),
	CONSTRAINT fk_course_corrections_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE
);

CREATE TABLE continuous_therapies (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	therapy_type_id INTEGER NOT NULL,
	start_datetime DATETIME NOT NULL,
	end_datetime DATETIME,
	status VARCHAR(50) NOT NULL,
	notes TEXT,
	attachment_keys TEXT,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_continuous_therapies PRIMARY KEY (id),
	CONSTRAINT fk_continuous_therapies_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT fk_continuous_therapies_therapy_type_id_therapy_types FOREIGN KEY(therapy_type_id) REFERENCES therapy_types (id)
);

CREATE INDEX ix_continuous_therapies_timeline ON continuous_therapies (admission_id, start_datetime);

CREATE TABLE attachments (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	storage_key VARCHAR(500) NOT NULL,
	original_filename VARCHAR(255) NOT NULL,
	content_type VARCHAR(100),
	file_size INTEGER,
	category VARCHAR(100),
	description TEXT,
	attachment_datetime DATETIME,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_attachments PRIMARY KEY (id),
	CONSTRAINT fk_attachments_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT uq_attachments_storage_key UNIQUE (storage_key)
);

CREATE TABLE location_clinical_statuses (
	id INTEGER NOT NULL,
	location_step_id INTEGER NOT NULL,
	clinical_status_type_id INTEGER NOT NULL,
	start_datetime DATETIME NOT NULL,
	end_datetime DATETIME,
	notes TEXT,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_location_clinical_statuses PRIMARY KEY (id),
	CONSTRAINT fk_location_clinical_statuses_location_step_id_location_steps FOREIGN KEY(location_step_id) REFERENCES location_steps (id) ON DELETE CASCADE,
	CONSTRAINT fk_location_clinical_statuses_clinical_status_type_id_clinical_status_types FOREIGN KEY(clinical_status_type_id) REFERENCES clinical_status_types (id)
);

CREATE INDEX ix_location_clinical_statuses_timeline ON location_clinical_statuses (location_step_id, start_datetime);

CREATE TABLE care_team_assignments (
	id INTEGER NOT NULL,
	location_step_id INTEGER NOT NULL,
	team_role_type_id INTEGER NOT NULL,
	staff_name VARCHAR(200) NOT NULL,
	shift_type VARCHAR(50),
	start_datetime DATETIME,
	end_datetime DATETIME,
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_care_team_assignments PRIMARY KEY (id),
	CONSTRAINT fk_care_team_assignments_location_step_id_location_steps FOREIGN KEY(location_step_id) REFERENCES location_steps (id) ON DELETE CASCADE,
	CONSTRAINT fk_care_team_assignments_team_role_type_id_team_role_types FOREIGN KEY(team_role_type_id) REFERENCES team_role_types (id)
);

CREATE TABLE bedside_procedures (
	id INTEGER NOT NULL,
	location_step_id INTEGER NOT NULL,
	procedure_type_id INTEGER NOT NULL,
	start_datetime DATETIME NOT NULL,
	end_datetime DATETIME,
	notes TEXT,
	outcome VARCHAR(50),
	performed_by VARCHAR(200),
	created_by VARCHAR(100),
	created_at DATETIME NOT NULL,
	updated_at DATETIME NOT NULL,
	CONSTRAINT pk_bedside_procedures PRIMARY KEY (id),
	CONSTRAINT fk_bedside_procedures_location_step_id_location_steps FOREIGN KEY(location_step_id) REFERENCES location_steps (id) ON DELETE CASCADE,
	CONSTRAINT fk_bedside_procedures_procedure_type_id_procedure_types FOREIGN KEY(procedure_type_id) REFERENCES procedure_types (id)
);

-- ============================================================================
-- EVENT TABLES (v4 - Immutable, Append-Only)
-- ============================================================================

CREATE TABLE location_events (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	location_type_id INTEGER NOT NULL,
	event_type VARCHAR(20) NOT NULL,         -- 'arrival' | 'departure'
	occurred_at DATETIME NOT NULL,
	corrects_event_id INTEGER,               -- For corrections (immutable pattern)
	recorded_at DATETIME NOT NULL,
	recorded_by VARCHAR(100),
	notes TEXT,
	source_table VARCHAR(100),               -- Migration provenance
	source_record_id VARCHAR(100),           -- Migration provenance
	migration_run_id VARCHAR(36),
	CONSTRAINT pk_location_events PRIMARY KEY (id),
	CONSTRAINT ck_location_events_ck_location_events_event_type CHECK (event_type IN ('arrival', 'departure')),
	CONSTRAINT fk_location_events_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT fk_location_events_location_type_id_location_types FOREIGN KEY(location_type_id) REFERENCES location_types (id),
	CONSTRAINT fk_location_events_corrects_event_id_location_events FOREIGN KEY(corrects_event_id) REFERENCES location_events (id)
);

CREATE INDEX ix_location_events_timeline ON location_events (admission_id, occurred_at);

CREATE TABLE clinical_status_events (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	status_type_id INTEGER NOT NULL,
	event_type VARCHAR(20) NOT NULL,         -- 'started' | 'ended'
	occurred_at DATETIME NOT NULL,
	severity INTEGER,                         -- 1-5 scale
	corrects_event_id INTEGER,
	recorded_at DATETIME NOT NULL,
	recorded_by VARCHAR(100),
	notes TEXT,
	source_table VARCHAR(100),
	source_record_id VARCHAR(100),
	migration_run_id VARCHAR(36),
	CONSTRAINT pk_clinical_status_events PRIMARY KEY (id),
	CONSTRAINT ck_clinical_status_events_ck_clinical_status_events_event_type CHECK (event_type IN ('started', 'ended')),
	CONSTRAINT ck_clinical_status_events_ck_clinical_status_events_severity CHECK (severity BETWEEN 1 AND 5),
	CONSTRAINT fk_clinical_status_events_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT fk_clinical_status_events_status_type_id_clinical_status_types FOREIGN KEY(status_type_id) REFERENCES clinical_status_types (id),
	CONSTRAINT fk_clinical_status_events_corrects_event_id_clinical_status_events FOREIGN KEY(corrects_event_id) REFERENCES clinical_status_events (id)
);

CREATE INDEX ix_clinical_status_events_timeline ON clinical_status_events (admission_id, occurred_at);

CREATE TABLE intervention_events (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	event_type VARCHAR(20) NOT NULL,         -- 'planned'|'started'|'paused'|'resumed'|'completed'|'cancelled'
	therapy_type_id INTEGER,                  -- XOR with procedure_type_id
	procedure_type_id INTEGER,                -- XOR with therapy_type_id
	occurred_at DATETIME NOT NULL,
	performed_by VARCHAR(200),
	outcome VARCHAR(50),
	corrects_event_id INTEGER,
	recorded_at DATETIME NOT NULL,
	recorded_by VARCHAR(100),
	notes TEXT,
	source_table VARCHAR(100),
	source_record_id VARCHAR(100),
	migration_run_id VARCHAR(36),
	CONSTRAINT pk_intervention_events PRIMARY KEY (id),
	CONSTRAINT ck_intervention_events_ck_intervention_events_event_type CHECK (event_type IN ('planned', 'started', 'paused', 'resumed', 'completed', 'cancelled')),
	CONSTRAINT ck_intervention_events_ck_intervention_events_single_type CHECK ((therapy_type_id IS NOT NULL AND procedure_type_id IS NULL) OR (therapy_type_id IS NULL AND procedure_type_id IS NOT NULL)),
	CONSTRAINT fk_intervention_events_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT fk_intervention_events_therapy_type_id_therapy_types FOREIGN KEY(therapy_type_id) REFERENCES therapy_types (id),
	CONSTRAINT fk_intervention_events_procedure_type_id_procedure_types FOREIGN KEY(procedure_type_id) REFERENCES procedure_types (id),
	CONSTRAINT fk_intervention_events_corrects_event_id_intervention_events FOREIGN KEY(corrects_event_id) REFERENCES intervention_events (id)
);

CREATE INDEX ix_intervention_events_timeline ON intervention_events (admission_id, occurred_at);

CREATE TABLE care_team_events (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	team_role_type_id INTEGER NOT NULL,
	location_step_id INTEGER,                 -- Optional link to location context
	staff_id INTEGER,                         -- Optional FK to staff table
	staff_name VARCHAR(200) NOT NULL,
	shift_type VARCHAR(50),
	event_type VARCHAR(20) NOT NULL,         -- 'assigned' | 'unassigned'
	occurred_at DATETIME NOT NULL,
	corrects_event_id INTEGER,
	recorded_at DATETIME NOT NULL,
	recorded_by VARCHAR(100),
	notes TEXT,
	source_table VARCHAR(100),
	source_record_id VARCHAR(100),
	migration_run_id VARCHAR(36),
	CONSTRAINT pk_care_team_events PRIMARY KEY (id),
	CONSTRAINT ck_care_team_events_ck_care_team_events_event_type CHECK (event_type IN ('assigned', 'unassigned')),
	CONSTRAINT fk_care_team_events_admission_id_admissions FOREIGN KEY(admission_id) REFERENCES admissions (id) ON DELETE CASCADE,
	CONSTRAINT fk_care_team_events_team_role_type_id_team_role_types FOREIGN KEY(team_role_type_id) REFERENCES team_role_types (id),
	CONSTRAINT fk_care_team_events_location_step_id_location_steps FOREIGN KEY(location_step_id) REFERENCES location_steps (id),
	CONSTRAINT fk_care_team_events_staff_id_staff FOREIGN KEY(staff_id) REFERENCES staff (id),
	CONSTRAINT fk_care_team_events_corrects_event_id_care_team_events FOREIGN KEY(corrects_event_id) REFERENCES care_team_events (id)
);

CREATE INDEX ix_care_team_events_timeline ON care_team_events (admission_id, occurred_at);

-- ============================================================================
-- ANALYTICS TABLES (v4 - Derived from Events)
-- ============================================================================

CREATE TABLE fact_event (
	id INTEGER NOT NULL,
	patient_uuid CHAR(32) NOT NULL,
	admission_id INTEGER NOT NULL,
	event_time DATETIME NOT NULL,
	domain VARCHAR(50) NOT NULL,             -- 'location', 'clinical_status', 'intervention', 'annotation'
	event_type VARCHAR(50) NOT NULL,         -- Domain-specific event type
	type_code VARCHAR(50),                    -- Code from type table (e.g., 'CICU', 'VENT')
	type_id INTEGER,                          -- FK to type table (denormalized)
	value_numeric NUMERIC(18, 4),
	value_text TEXT,
	severity INTEGER,
	source_table VARCHAR(100) NOT NULL,
	source_record_id VARCHAR(100) NOT NULL,
	ingestion_run_id CHAR(32),
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_fact_event PRIMARY KEY (id)
);

CREATE INDEX ix_fact_event_patient ON fact_event (patient_uuid, event_time);
CREATE INDEX ix_fact_event_admission ON fact_event (admission_id, event_time);
CREATE INDEX ix_fact_event_domain ON fact_event (domain, event_time);

CREATE TABLE admission_day (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	day_date DATE NOT NULL,
	pod INTEGER,                              -- Post-operative day
	dominant_location_type_id INTEGER,
	hours_in_icu NUMERIC(5, 2),
	hours_in_ward NUMERIC(5, 2),
	location_change_count INTEGER,
	max_acuity_level INTEGER,
	hours_high_acuity NUMERIC(5, 2),
	active_therapy_count INTEGER,
	therapy_hours_total NUMERIC(8, 2),
	annotation_count INTEGER,
	procedure_count INTEGER,
	course_correction_count INTEGER,
	has_location_data BOOLEAN NOT NULL,       -- Data quality flag
	has_status_data BOOLEAN NOT NULL,         -- Data quality flag
	therapy_category_hours JSON,
	procedure_category_counts JSON,
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_admission_day PRIMARY KEY (id),
	CONSTRAINT uq_admission_day UNIQUE (admission_id, day_date)
);

CREATE INDEX ix_admission_day_lookup ON admission_day (admission_id, day_date);

CREATE TABLE outcome_event (
	id INTEGER NOT NULL,
	admission_id INTEGER NOT NULL,
	label_name VARCHAR(100) NOT NULL,         -- e.g., 'mortality', 'complication', 'readmission'
	label_version VARCHAR(20) NOT NULL,       -- For ML model versioning
	label_time DATETIME,                       -- When outcome occurred
	label_value INTEGER,                       -- Binary or categorical outcome
	censor_time DATETIME,                      -- For survival analysis
	created_at DATETIME NOT NULL,
	CONSTRAINT pk_outcome_event PRIMARY KEY (id)
);

CREATE INDEX ix_outcome_event_lookup ON outcome_event (admission_id, label_time);

-- ============================================================================
-- PROJECTION VIEWS (Derived from Event Streams)
-- ============================================================================

-- View: Location intervals derived from arrival/departure events
CREATE VIEW v_location_intervals AS
WITH arrivals AS (
    SELECT
        admission_id,
        location_type_id,
        occurred_at AS entry_datetime,
        ROW_NUMBER() OVER (
            PARTITION BY admission_id, location_type_id
            ORDER BY occurred_at
        ) AS rn
    FROM location_events
    WHERE event_type = 'arrival'
),
departures AS (
    SELECT
        admission_id,
        location_type_id,
        occurred_at AS exit_datetime,
        ROW_NUMBER() OVER (
            PARTITION BY admission_id, location_type_id
            ORDER BY occurred_at
        ) AS rn
    FROM location_events
    WHERE event_type = 'departure'
)
SELECT
    a.admission_id,
    a.location_type_id,
    a.entry_datetime,
    d.exit_datetime,
    (julianday(COALESCE(d.exit_datetime, CURRENT_TIMESTAMP)) - julianday(a.entry_datetime)) * 24.0
        AS duration_hours
FROM arrivals a
LEFT JOIN departures d
    ON a.admission_id = d.admission_id
    AND a.location_type_id = d.location_type_id
    AND a.rn = d.rn;

-- View: Clinical status intervals derived from started/ended events
CREATE VIEW v_clinical_status_intervals AS
WITH starts AS (
    SELECT
        admission_id,
        status_type_id,
        occurred_at AS start_datetime,
        severity,
        ROW_NUMBER() OVER (
            PARTITION BY admission_id, status_type_id
            ORDER BY occurred_at
        ) AS rn
    FROM clinical_status_events
    WHERE event_type = 'started'
),
ends AS (
    SELECT
        admission_id,
        status_type_id,
        occurred_at AS end_datetime,
        ROW_NUMBER() OVER (
            PARTITION BY admission_id, status_type_id
            ORDER BY occurred_at
        ) AS rn
    FROM clinical_status_events
    WHERE event_type = 'ended'
)
SELECT
    s.admission_id,
    s.status_type_id,
    s.start_datetime,
    e.end_datetime,
    s.severity
FROM starts s
LEFT JOIN ends e
    ON s.admission_id = e.admission_id
    AND s.status_type_id = e.status_type_id
    AND s.rn = e.rn;

-- View: Current location for active admissions
CREATE VIEW v_current_locations AS
SELECT
    a.id AS admission_id,
    a.patient_id,
    lt.id AS location_type_id,
    lt.display_name AS location_name,
    lt.category,
    le.occurred_at AS since
FROM admissions a
JOIN location_events le ON le.admission_id = a.id
JOIN location_types lt ON lt.id = le.location_type_id
WHERE a.discharge_date IS NULL
  AND le.event_type = 'arrival'
  AND NOT EXISTS (
      SELECT 1
      FROM location_events le2
      WHERE le2.admission_id = le.admission_id
        AND le2.location_type_id = le.location_type_id
        AND le2.event_type = 'departure'
        AND le2.occurred_at > le.occurred_at
  );

-- View: Active clinical statuses for active admissions
CREATE VIEW v_active_clinical_statuses AS
SELECT
    a.id AS admission_id,
    a.patient_id,
    cst.id AS status_type_id,
    cst.display_name AS status_name,
    cst.acuity_level,
    cse.occurred_at AS since
FROM admissions a
JOIN clinical_status_events cse ON cse.admission_id = a.id
JOIN clinical_status_types cst ON cst.id = cse.status_type_id
WHERE a.discharge_date IS NULL
  AND cse.event_type = 'started'
  AND NOT EXISTS (
      SELECT 1
      FROM clinical_status_events cse2
      WHERE cse2.admission_id = cse.admission_id
        AND cse2.status_type_id = cse.status_type_id
        AND cse2.event_type = 'ended'
        AND cse2.occurred_at > cse.occurred_at
  );

-- View: Active interventions (therapies/procedures in progress)
CREATE VIEW v_active_interventions AS
WITH ranked_events AS (
    SELECT
        ie.admission_id,
        ie.therapy_type_id,
        ie.procedure_type_id,
        ie.source_table,
        ie.source_record_id,
        ie.event_type,
        ie.occurred_at,
        ie.performed_by,
        ie.outcome,
        ROW_NUMBER() OVER (
            PARTITION BY ie.source_table, ie.source_record_id
            ORDER BY ie.occurred_at DESC, ie.id DESC
        ) AS rn
    FROM intervention_events ie
)
SELECT
    re.admission_id,
    re.source_table,
    re.source_record_id,
    re.event_type,
    CASE
        WHEN re.event_type IN ('started', 'resumed') THEN 'in_progress'
        WHEN re.event_type = 'paused' THEN 'on_hold'
        WHEN re.event_type = 'planned' THEN 'planned'
        WHEN re.event_type = 'completed' THEN 'completed'
        WHEN re.event_type = 'cancelled' THEN 'cancelled'
        ELSE re.event_type
    END AS status,
    re.therapy_type_id,
    re.procedure_type_id,
    re.performed_by,
    re.outcome,
    re.occurred_at AS status_since,
    (julianday(CURRENT_TIMESTAMP) - julianday(re.occurred_at)) * 24.0 AS hours_active
FROM ranked_events re
JOIN admissions a ON a.id = re.admission_id
WHERE re.rn = 1
  AND a.discharge_date IS NULL
  AND re.event_type IN ('started', 'resumed', 'paused');

-- ============================================================================
-- ALEMBIC VERSION TRACKING
-- ============================================================================

CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
