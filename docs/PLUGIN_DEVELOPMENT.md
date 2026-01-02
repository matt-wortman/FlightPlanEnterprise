# Plugin Development Guide

**Last Updated:** 2026-01-02

Comprehensive guide to creating specialty plugins for FlightPlan Enterprise.

---

## Table of Contents

- [Overview](#overview)
- [Plugin Architecture](#plugin-architecture)
- [Getting Started](#getting-started)
- [Plugin Manifest](#plugin-manifest)
- [UI Configuration](#ui-configuration)
- [Event Handlers](#event-handlers)
- [Domain Logic](#domain-logic)
- [Testing Plugins](#testing-plugins)
- [Deployment](#deployment)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

### What are Specialty Plugins?

Specialty plugins extend FlightPlan Enterprise with **medical specialty-specific** functionality:

- **Custom UI components** (timeline events, risk calculators, care pathways)
- **Domain-specific logic** (cardiac surgery protocols, neurosurgery risk scores)
- **Event handlers** (specialty-specific projections, business rules)
- **Configurable workflows** (admission templates, care milestones)

### Why Plugins?

**Extensibility**: Add new specialties without modifying core codebase
**Separation of Concerns**: Specialty logic isolated from platform logic
**Customizability**: Each hospital/department can customize their specialty plugins
**Maintainability**: Update specialty logic independently of core platform

### Plugin Capabilities

| Capability | Description | Implementation |
|------------|-------------|----------------|
| **UI Configuration** | Timeline events, forms, dashboards | YAML manifest |
| **Event Handling** | Custom projections, business rules | Python code |
| **Domain Models** | Specialty-specific aggregates | Python classes |
| **Workflows** | Care pathways, protocols | YAML + Python |
| **Risk Calculators** | Specialty scoring systems | Python functions |

---

## Plugin Architecture

### Directory Structure

```
backend/plugins/
├── cardiac/                    # Cardiac Surgery plugin
│   ├── manifest.yaml          # Plugin metadata and UI config
│   ├── __init__.py            # Plugin initialization
│   ├── projections.py         # Event projections (optional)
│   ├── domain.py              # Domain logic (optional)
│   ├── risk_calculators.py   # Risk scoring (optional)
│   └── README.md              # Plugin documentation
│
├── neurosurgery/              # Neurosurgery plugin
│   ├── manifest.yaml
│   └── ...
│
└── orthopedics/               # Orthopedic Surgery plugin
    ├── manifest.yaml
    └── ...
```

### Plugin Lifecycle

```
1. Discovery  → 2. Loading → 3. Validation → 4. Registration → 5. Runtime Use
   (startup)      (YAML)       (schema)       (registry)        (API/UI)
```

**Discovery**: PluginRegistry scans `backend/plugins/` directory
**Loading**: Read `manifest.yaml` and import Python modules
**Validation**: Validate manifest against schema
**Registration**: Register plugin in global registry
**Runtime**: API returns plugin config, UI uses specialty logic

### Component Interaction

```
┌─────────────┐
│   Frontend  │ ← GET /api/v1/specialties/cardiac/config
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Backend   │ ← PluginRegistry.get_ui_config('cardiac')
│   FastAPI   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│Plugin System│ ← Load manifest.yaml
│  Registry   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│cardiac/     │
│manifest.yaml│ ← UI config, metadata
└─────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.12+ installed
- Backend setup complete (see [backend/README.md](../backend/README.md))
- Understanding of FlightPlan domain model
- YAML and Python knowledge

### Create Your First Plugin

#### Step 1: Create Plugin Directory

```bash
cd backend/plugins
mkdir my_specialty
cd my_specialty
```

#### Step 2: Create manifest.yaml

```bash
cat > manifest.yaml <<'EOF'
apiVersion: flightplan.io/v1
kind: SpecialtyPlugin
metadata:
  name: my_specialty
  version: 0.1.0
  displayName: "My Specialty"
  description: "Custom specialty plugin for..."

spec:
  ui:
    patient_header:
      primary_fields:
        - name
        - mrn
        - age
    timeline:
      event_categories:
        - name: procedures
          displayName: "Procedures"
          color: "#e74c3c"
          events:
            - type: my_procedure
              displayName: "My Procedure"
              icon: "activity"
EOF
```

#### Step 3: Create __init__.py

```bash
cat > __init__.py <<'EOF'
"""My Specialty Plugin

Custom FlightPlan plugin for [specialty name] care planning.
"""

__version__ = "0.1.0"
EOF
```

#### Step 4: Verify Plugin Loads

```bash
cd ../../  # Return to backend/
python -c "
from app.core.plugins.registry import plugin_registry
plugin_registry.load_all()
plugins = plugin_registry.get_all_plugins()
print(f'Loaded {len(plugins)} plugins:')
for p in plugins:
    print(f'  - {p.name} v{p.version} ({p.display_name})')
"
```

Expected output:
```
Loaded 2 plugins:
  - cardiac v0.1.0 (Cardiac Surgery)
  - my_specialty v0.1.0 (My Specialty)
```

#### Step 5: Test via API

```bash
# Start backend server
uvicorn app.main:app --reload

# In another terminal:
curl http://localhost:8000/api/v1/specialties
# Should include your plugin

curl http://localhost:8000/api/v1/specialties/my_specialty/config
# Should return your UI config
```

---

## Plugin Manifest

### Manifest Schema

The `manifest.yaml` file follows a Kubernetes-inspired structure:

```yaml
apiVersion: flightplan.io/v1     # API version (currently v1)
kind: SpecialtyPlugin             # Resource type (always SpecialtyPlugin)
metadata:                         # Plugin metadata
  name: string                    # Plugin identifier (slug format)
  version: string                 # Semantic version (e.g., "1.2.3")
  displayName: string             # Human-readable name
  description: string             # Plugin description
spec:                             # Plugin specification
  ui: object                      # UI configuration (see below)
  projections: array              # Event projections (future)
  workflows: object               # Care workflows (future)
```

### Metadata Section

```yaml
metadata:
  name: cardiac_surgery           # Required: lowercase, underscores, no spaces
  version: 1.0.0                  # Required: semver format
  displayName: "Cardiac Surgery"  # Optional: display in UI
  description: >                  # Optional: longer description
    Cardiac surgery specialty plugin providing CABG, valve replacement,
    and other cardiac procedures support.
  authors:                        # Optional: plugin authors
    - "Dr. Jane Smith <jane@hospital.org>"
  license: "MIT"                  # Optional: license
  homepage: "https://..."         # Optional: documentation URL
```

### Naming Conventions

**Plugin Name (metadata.name)**:
- Use lowercase with underscores
- Be descriptive but concise
- Match directory name

```yaml
# Good plugin names
name: cardiac_surgery
name: neurosurgery
name: orthopedics
name: transplant

# Bad plugin names
name: CardiacSurgery     # No camelCase
name: cardiac-surgery    # No hyphens
name: cs                 # Too abbreviated
name: "Cardiac Surgery"  # No spaces
```

---

## UI Configuration

The `spec.ui` section defines frontend configuration.

### Patient Header Configuration

Customize which fields appear in the patient header:

```yaml
spec:
  ui:
    patient_header:
      primary_fields:
        - name
        - mrn
        - age
        - gender
      secondary_fields:
        - attending_physician
        - admission_date
        - current_location
      specialty_fields:
        - ejection_fraction     # Cardiac-specific
        - cabg_count           # Number of previous CABGs
```

### Timeline Event Configuration

Define custom timeline events for your specialty:

```yaml
spec:
  ui:
    timeline:
      event_categories:
        - name: cardiac_procedures
          displayName: "Cardiac Procedures"
          color: "#e74c3c"
          icon: "heart"
          events:
            - type: cabg
              displayName: "CABG Surgery"
              icon: "activity"
              color: "#c0392b"
              fields:
                - name: graft_count
                  label: "Number of Grafts"
                  type: number
                  required: true
                - name: bypass_time
                  label: "Bypass Time (min)"
                  type: number
                  unit: "minutes"

            - type: valve_replacement
              displayName: "Valve Replacement"
              icon: "heart-pulse"
              color: "#e74c3c"
              fields:
                - name: valve_type
                  label: "Valve Type"
                  type: select
                  options:
                    - mechanical
                    - bioprosthetic
                - name: valve_position
                  label: "Valve Position"
                  type: select
                  options:
                    - aortic
                    - mitral
                    - tricuspid
                    - pulmonary

        - name: complications
          displayName: "Complications"
          color: "#e67e22"
          icon: "alert-circle"
          events:
            - type: arrhythmia
              displayName: "Arrhythmia"
              icon: "zap"
            - type: bleeding
              displayName: "Post-op Bleeding"
              icon: "droplet"
```

### Risk Factor Configuration

Define risk calculators and scoring systems:

```yaml
spec:
  ui:
    risk_factors:
      - key: euroscore
        displayName: "EuroSCORE II"
        description: "European System for Cardiac Operative Risk Evaluation"
        type: calculated
        inputs:
          - name: age
            type: number
            unit: years
          - name: gender
            type: select
            options: [male, female]
          - name: ejection_fraction
            type: number
            unit: "%"
          - name: recent_mi
            type: boolean
        output:
          type: percentage
          ranges:
            - max: 2
              label: "Low Risk"
              color: "#27ae60"
            - min: 2
              max: 5
              label: "Medium Risk"
              color: "#f39c12"
            - min: 5
              label: "High Risk"
              color: "#e74c3c"

      - key: sts_score
        displayName: "STS Risk Score"
        description: "Society of Thoracic Surgeons Risk Score"
        type: calculated
        # ... similar structure
```

### Care Pathway Configuration

Define milestone-based care pathways:

```yaml
spec:
  ui:
    care_pathways:
      - name: cabg_pathway
        displayName: "CABG Recovery Pathway"
        description: "Standard CABG recovery milestones"
        milestones:
          - name: surgery
            displayName: "Surgery"
            day: 0
            required: true
          - name: extubation
            displayName: "Extubation"
            day: 0
            target_hours: 6
          - name: icu_discharge
            displayName: "ICU Discharge"
            day: 2
            target_hours: 48
          - name: ambulation
            displayName: "Ambulation"
            day: 1
          - name: hospital_discharge
            displayName: "Hospital Discharge"
            day: 5
            target_hours: 120
```

### Dashboard Widget Configuration

Define specialty-specific dashboard widgets:

```yaml
spec:
  ui:
    dashboard:
      widgets:
        - type: metric
          title: "Average Bypass Time"
          query: avg_bypass_time_last_30_days
          unit: "minutes"
          target: 90
          format: number

        - type: chart
          title: "Procedure Volume"
          chart_type: bar
          query: procedure_counts_last_30_days
          x_axis: procedure_type
          y_axis: count

        - type: list
          title: "High-Risk Patients"
          query: patients_euroscore_gt_5
          fields:
            - name
            - euroscore
            - surgery_date
```

---

## Event Handlers

### Creating Custom Projections

Projections transform events into read models. Create `projections.py`:

```python
# backend/plugins/my_specialty/projections.py
"""Custom projections for My Specialty plugin."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.read_models import AdmissionReadModel


class MySpecialtyProjection:
    """Projects specialty-specific events to read models."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def project(self, event: dict[str, Any]) -> None:
        """Project event to read model.

        Args:
            event: Event dictionary with type, data, metadata
        """
        event_type = event["event_type"]

        if event_type == "my_specialty.procedure_completed":
            await self._handle_procedure_completed(event)
        elif event_type == "my_specialty.risk_score_calculated":
            await self._handle_risk_score(event)

    async def _handle_procedure_completed(self, event: dict[str, Any]) -> None:
        """Update admission read model with procedure data."""
        admission_id = UUID(event["stream_id"])
        data = event["data"]

        result = await self.session.execute(
            select(AdmissionReadModel).where(
                AdmissionReadModel.id == admission_id
            )
        )
        admission = result.scalar_one_or_none()

        if admission:
            # Update JSONB data field
            admission_data = admission.data.copy()
            admission_data["last_procedure"] = {
                "type": data["procedure_type"],
                "date": data["occurred_at"],
                "outcome": data.get("outcome"),
            }
            admission.data = admission_data
            admission.version += 1

    async def _handle_risk_score(self, event: dict[str, Any]) -> None:
        """Store calculated risk score."""
        admission_id = UUID(event["stream_id"])
        data = event["data"]

        result = await self.session.execute(
            select(AdmissionReadModel).where(
                AdmissionReadModel.id == admission_id
            )
        )
        admission = result.scalar_one_or_none()

        if admission:
            admission_data = admission.data.copy()
            admission_data["risk_scores"] = admission_data.get("risk_scores", {})
            admission_data["risk_scores"][data["score_type"]] = {
                "value": data["score_value"],
                "calculated_at": data["calculated_at"],
                "inputs": data.get("inputs", {}),
            }
            admission.data = admission_data
            admission.version += 1
```

### Registering Event Handlers

In `__init__.py`:

```python
# backend/plugins/my_specialty/__init__.py
"""My Specialty Plugin"""

from app.core.plugins.registry import plugin_registry
from .projections import MySpecialtyProjection

__version__ = "0.1.0"


def register_projections():
    """Register custom projections with the system."""
    # Future: Register with projection manager
    # projection_manager.register('my_specialty', MySpecialtyProjection)
    pass


# Auto-register on import
register_projections()
```

---

## Domain Logic

### Creating Domain Models

Define specialty-specific domain logic in `domain.py`:

```python
# backend/plugins/cardiac_surgery/domain.py
"""Cardiac surgery domain models and business logic."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ProcedureType(str, Enum):
    """Types of cardiac procedures."""
    CABG = "cabg"
    VALVE_REPLACEMENT = "valve_replacement"
    VALVE_REPAIR = "valve_repair"
    CABG_PLUS_VALVE = "cabg_plus_valve"


class ValvePosition(str, Enum):
    """Heart valve positions."""
    AORTIC = "aortic"
    MITRAL = "mitral"
    TRICUSPID = "tricuspid"
    PULMONARY = "pulmonary"


@dataclass
class CardiacProcedure:
    """Cardiac procedure value object."""
    procedure_type: ProcedureType
    occurred_at: datetime
    surgeon_id: str
    bypass_time_minutes: Optional[int] = None
    cross_clamp_time_minutes: Optional[int] = None
    graft_count: Optional[int] = None
    valve_position: Optional[ValvePosition] = None
    valve_type: Optional[str] = None

    def is_high_risk(self) -> bool:
        """Determine if procedure is high-risk based on parameters."""
        if self.bypass_time_minutes and self.bypass_time_minutes > 120:
            return True
        if self.cross_clamp_time_minutes and self.cross_clamp_time_minutes > 90:
            return True
        if self.procedure_type == ProcedureType.CABG_PLUS_VALVE:
            return True
        return False


@dataclass
class EuroScoreII:
    """EuroSCORE II risk calculator."""
    age: int
    gender: str
    ejection_fraction: float
    recent_mi: bool
    diabetes: bool
    chronic_kidney_disease: bool
    # ... many more factors

    def calculate(self) -> float:
        """Calculate EuroSCORE II percentage.

        Returns:
            Predicted mortality percentage
        """
        # Simplified calculation (real formula is complex)
        score = 0.0

        # Age factor
        if self.age > 60:
            score += (self.age - 60) * 0.2

        # EF factor
        if self.ejection_fraction < 50:
            score += (50 - self.ejection_fraction) * 0.1

        # Comorbidities
        if self.recent_mi:
            score += 2.0
        if self.diabetes:
            score += 1.5
        if self.chronic_kidney_disease:
            score += 2.5

        return min(score, 100.0)  # Cap at 100%

    def risk_category(self) -> str:
        """Categorize risk level."""
        score = self.calculate()
        if score < 2:
            return "low"
        elif score < 5:
            return "medium"
        else:
            return "high"
```

### Business Rules

Implement specialty-specific business rules:

```python
# backend/plugins/cardiac_surgery/rules.py
"""Cardiac surgery business rules."""

from datetime import datetime, timedelta
from typing import Optional


class CardiacAdmissionRules:
    """Business rules for cardiac surgery admissions."""

    @staticmethod
    def validate_surgery_timing(
        admit_date: datetime,
        surgery_date: datetime,
    ) -> tuple[bool, Optional[str]]:
        """Validate surgery is scheduled appropriately after admission.

        Args:
            admit_date: Admission date/time
            surgery_date: Scheduled surgery date/time

        Returns:
            Tuple of (is_valid, error_message)
        """
        if surgery_date < admit_date:
            return False, "Surgery cannot be before admission"

        # Elective surgery should be at least 24 hours after admission
        if surgery_date - admit_date < timedelta(hours=24):
            return False, "Elective surgery requires 24h pre-op period"

        # Surgery should be within reasonable timeframe
        if surgery_date - admit_date > timedelta(days=7):
            return False, "Surgery more than 7 days after admission - verify timing"

        return True, None

    @staticmethod
    def require_pre_op_tests(procedure_type: str) -> list[str]:
        """Return required pre-operative tests for procedure.

        Args:
            procedure_type: Type of cardiac procedure

        Returns:
            List of required test codes
        """
        common_tests = [
            "CBC",
            "BMP",
            "PT_INR",
            "PTT",
            "chest_xray",
            "ekg",
        ]

        if procedure_type in ["cabg", "cabg_plus_valve"]:
            return common_tests + [
                "cardiac_cath",
                "echo",
                "carotid_doppler",
            ]
        elif "valve" in procedure_type:
            return common_tests + [
                "echo",
                "cardiac_mri",
            ]
        else:
            return common_tests
```

---

## Testing Plugins

### Unit Tests

Create `test_my_specialty.py`:

```python
# backend/plugins/my_specialty/test_my_specialty.py
"""Tests for My Specialty plugin."""

import pytest
from .domain import EuroScoreII


def test_euroscore_low_risk():
    """Test EuroSCORE calculation for low-risk patient."""
    score_calc = EuroScoreII(
        age=45,
        gender="male",
        ejection_fraction=60.0,
        recent_mi=False,
        diabetes=False,
        chronic_kidney_disease=False,
    )

    score = score_calc.calculate()
    assert score < 2.0
    assert score_calc.risk_category() == "low"


def test_euroscore_high_risk():
    """Test EuroSCORE calculation for high-risk patient."""
    score_calc = EuroScoreII(
        age=75,
        gender="female",
        ejection_fraction=30.0,
        recent_mi=True,
        diabetes=True,
        chronic_kidney_disease=True,
    )

    score = score_calc.calculate()
    assert score > 5.0
    assert score_calc.risk_category() == "high"


@pytest.mark.asyncio
async def test_projection_handles_procedure_event():
    """Test projection correctly handles procedure event."""
    from .projections import MySpecialtyProjection

    # Setup test database session
    # ... (see TESTING.md for database test setup)

    projection = MySpecialtyProjection(session=mock_session)

    event = {
        "stream_id": "a1b2c3d4-...",
        "event_type": "my_specialty.procedure_completed",
        "data": {
            "procedure_type": "cabg",
            "occurred_at": "2025-01-16T10:00:00Z",
            "outcome": "success",
        },
    }

    await projection.project(event)

    # Verify admission read model updated
    # ...
```

### Integration Tests

Test plugin with real API:

```python
# tests/test_plugin_api.py
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_plugin_list_includes_my_specialty():
    """Test that custom plugin appears in specialty list."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/specialties")

    assert response.status_code == 200
    plugins = response.json()

    plugin_names = [p["name"] for p in plugins]
    assert "my_specialty" in plugin_names


@pytest.mark.asyncio
async def test_plugin_config_returns_ui_settings():
    """Test that plugin config endpoint returns UI configuration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/specialties/my_specialty/config")

    assert response.status_code == 200
    config = response.json()

    assert "timeline" in config
    assert "patient_header" in config
```

---

## Deployment

### Development Deployment

```bash
# 1. Create plugin directory
cd backend/plugins
mkdir my_specialty

# 2. Add manifest.yaml and code
# ... (create files)

# 3. Restart backend server
# Server will auto-discover plugin on startup
uvicorn app.main:app --reload
```

### Production Deployment

```bash
# 1. Version control
cd backend/plugins/my_specialty
git add manifest.yaml *.py
git commit -m "feat(plugins): add my_specialty plugin v0.1.0"

# 2. Deploy with backend
# Plugins are deployed as part of backend deployment
# No separate deployment needed

# 3. Verify in production
curl https://api.flightplan.example.com/api/v1/specialties
```

### Plugin Versioning

Follow semantic versioning:

- **Major** (1.0.0): Breaking changes to manifest schema
- **Minor** (0.1.0): New features, backward compatible
- **Patch** (0.0.1): Bug fixes

```yaml
metadata:
  version: 1.2.3
```

---

## Best Practices

### DO's ✅

1. **Keep plugins focused** - One specialty per plugin
2. **Version carefully** - Use semver and document breaking changes
3. **Test thoroughly** - Unit tests for domain logic, integration tests for projections
4. **Document well** - Add README.md to plugin directory
5. **Validate early** - Use Pydantic models for data validation
6. **Follow conventions** - Match coding style of core codebase
7. **Isolate dependencies** - Minimize external dependencies
8. **Use type hints** - Full type coverage for Python code

### DON'Ts ❌

1. **Don't modify core** - Plugins should extend, not modify core code
2. **Don't share state** - Each plugin should be independent
3. **Don't hardcode data** - Use configuration for customizable values
4. **Don't skip validation** - Always validate manifest and event data
5. **Don't expose PHI** - Follow PHI security rules in plugin code
6. **Don't break isolation** - Don't access other plugins' code directly

### Security Checklist

- [ ] No PHI in manifest.yaml (metadata, descriptions)
- [ ] All database queries include tenant_id filter
- [ ] Input validation on all event handlers
- [ ] No secrets in plugin code (use environment variables)
- [ ] Access control checked before operations

---

## Examples

### Example: Cardiac Surgery Plugin

See `/home/matt/code_projects/FlightPlanEnterprise/backend/plugins/cardiac/` for reference implementation.

### Example: Complete Plugin Template

```
my_specialty/
├── manifest.yaml              # Plugin configuration
├── __init__.py               # Package initialization
├── domain.py                 # Domain models and business logic
├── projections.py            # Event projections
├── rules.py                  # Business rules
├── calculators.py            # Risk calculators
├── test_my_specialty.py      # Unit tests
└── README.md                 # Plugin documentation
```

**manifest.yaml**:
```yaml
apiVersion: flightplan.io/v1
kind: SpecialtyPlugin
metadata:
  name: my_specialty
  version: 1.0.0
  displayName: "My Specialty"
  description: "Comprehensive specialty plugin"
  authors:
    - "Developer Name <dev@example.com>"

spec:
  ui:
    patient_header:
      primary_fields: [name, mrn, age]
    timeline:
      event_categories:
        - name: procedures
          displayName: "Procedures"
          color: "#e74c3c"
          events:
            - type: my_procedure
              displayName: "My Procedure"
              icon: "activity"
    risk_factors:
      - key: my_risk_score
        displayName: "My Risk Score"
        type: calculated
    care_pathways:
      - name: standard_pathway
        displayName: "Standard Care Pathway"
        milestones: [...]
```

---

## Troubleshooting

### Plugin Not Loading

```bash
# Check plugin directory exists
ls backend/plugins/my_specialty/

# Verify manifest.yaml syntax
python -c "import yaml; yaml.safe_load(open('backend/plugins/my_specialty/manifest.yaml'))"

# Check server logs
# Look for plugin discovery messages
```

### Manifest Validation Errors

```python
# Validate manifest manually
from app.core.plugins.manifest import PluginManifest
import yaml

with open('backend/plugins/my_specialty/manifest.yaml') as f:
    data = yaml.safe_load(f)

# This will raise validation errors if manifest is invalid
manifest = PluginManifest.model_validate(data)
```

### Projection Not Running

1. Verify event type matches projection handler
2. Check that projection is registered
3. Add logging to projection code
4. Test projection independently with mock events

---

## Resources

### Documentation

- [Plugin Manifest Schema](../backend/app/core/plugins/manifest.py) - Pydantic model
- [Plugin Registry](../backend/app/core/plugins/registry.py) - Loading and discovery
- [Event Contracts](../backend/docs/event_contracts_v1.md) - Event schemas
- [Domain Model](../docs/domain/) - Core domain concepts

### Example Plugins

- [Cardiac Surgery](../backend/plugins/cardiac/) - Reference implementation
- More examples coming soon

### Support

- **Questions**: Open GitHub Discussion
- **Bugs**: Create Issue with `plugin` label
- **Feature Requests**: Create Issue with `plugin-enhancement` label

---

**Related Documentation:**
- [API.md](API.md) - API reference for plugins
- [TESTING.md](TESTING.md) - Testing guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow
- [backend/README.md](../backend/README.md) - Backend setup

**Happy plugin development!** 🎉
