# Trajectory Model (Change Points)

## Canonical model
Clinicians record **change points** (not explicit end events). Each point captures the location and the active Y‑axis state at a single timestamp. The state persists until the next point.

### Tables
- `trajectory_point`
  - `trajectory_point_id` (PK)
  - `admission_id` (FK to `admissions`)
  - `occurred_at` (clinical time)
  - `recorded_at` (audit time)
  - `recorded_by` (nullable)
  - `location_type_id` (FK to `location_types`)
  - `trajectory_state_id` (FK to `trajectory_state_type`)
  - `notes` (nullable)
  - `corrects_point_id` (nullable, self‑FK)
  - `sequence` (tie‑breaker when multiple points share the same `occurred_at`)

- `trajectory_state_type`
  - `trajectory_state_id` (PK)
  - `specialty_id` (FK to `specialties`)
  - `code` (unique per specialty)
  - `display_name`
  - `y_level` (optional ordering/banding)
  - `active`

### Derived view
- `trajectory_segment`
  - Derived from consecutive `trajectory_point` rows per admission.
  - `start_time = occurred_at`
  - `end_time = next occurred_at` (nullable for last open segment)
  - `duration_hours` computed when `end_time` is present.

## Corrections
Use `corrects_point_id` to supersede an earlier point. A point is **active** only if no other point corrects it. The `trajectory_segment` view and timeline loader exclude corrected points. The backfill script does **not** generate corrections; it only creates new points from existing location/status history.

## Adding new Y‑axis states (per specialty)
1. Insert a row into `trajectory_state_type` with:
   - `specialty_id`
   - unique `code`
   - `display_name`
   - optional `y_level` (for UI ordering). For the current UI mapping, set `y_level` to the desired risk status (1–5).
2. Keep `active = true` for selectable states.
3. If you change the vocabulary, re-run `scripts/backfill_trajectory_points.py` (or update points manually) so admissions carry the new state at the right change points.

## Rollout notes
- Feature flags:
  - `TIMELINE_USE_TRAJECTORY_POINTS` (bool)
  - `TIMELINE_TRAJECTORY_POINT_ADMISSION_UUIDS` (comma‑separated UUIDs)
  - `TIMELINE_COMPARE_TRAJECTORY_POINTS` (bool, logs mismatches)
- Backfill script: `scripts/backfill_trajectory_points.py`
- Validation script: `scripts/validate_trajectory_points.py`
