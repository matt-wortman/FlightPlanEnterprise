# FlightPlan Enterprise Architecture Plan

**Last Updated:** 2026-01-02

> **Document Purpose**: High-level architecture design and migration strategy for rebuilding FlightPlan as a scalable, multi-specialty clinical platform.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Layer Deep Dives](#layer-deep-dives)
   - [Specialty Plugin System](#1-specialty-plugin-system)
   - [Event Sourcing for Clinical Events](#2-event-sourcing-for-clinical-events)
   - [Multi-Tenant Database Strategy](#3-multi-tenant-database-strategy)
   - [Frontend Design System](#4-frontend-design-system)
4. [Infrastructure & DevOps](#infrastructure--devops)
5. [Migration Strategy](#migration-strategy)
6. [Risk Mitigation](#risk-mitigation)
7. [Decision Log](#decision-log)

---

## Architecture Documentation Index

This document is the **master architecture blueprint** for FlightPlan Enterprise. Related architecture documents provide deep dives into specific areas:

### Core Architecture Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **[ENTERPRISE_ARCHITECTURE_PLAN.md](ENTERPRISE_ARCHITECTURE_PLAN.md)** | **THIS DOCUMENT** - High-level architecture vision, design patterns, and migration strategy | Start here for overall architecture understanding |
| [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) | Deep dive into v2.0 legacy technical implementation (Dash/Flask/React) | Understanding legacy system, migration planning |
| [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) | Database schema analysis and multi-specialty redesign recommendations | Database design, schema planning, multi-tenant strategy |
| [REBUILD_PLAN.md](REBUILD_PLAN.md) | Phase-by-phase rebuild execution plan with testing strategy | Active development, implementation roadmap |

### Analysis & Review Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [REFACTORING_PLAN.md](REFACTORING_PLAN.md) | Technology stack simplification and refactoring strategy | Understanding tech debt, planning improvements |
| [CODEBASE_ANALYSIS_AND_REFACTOR_REPORT.md](CODEBASE_ANALYSIS_AND_REFACTOR_REPORT.md) | Comprehensive analysis of v2.0 codebase functionality and structure | Deep code understanding, feature extraction |
| [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) | Security vulnerabilities and code quality issues in v2.0 | Security planning, avoiding legacy pitfalls |

### Implementation Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [../data-model/CURRENT_SCHEMA.md](../data-model/CURRENT_SCHEMA.md) | Current v3 database schema (from Alembic migrations) | Active development, understanding current implementation |
| [../data-model/DATABASE_SCHEMA_DUMP.sql](../data-model/DATABASE_SCHEMA_DUMP.sql) | Legacy database schema (reference only) | Migration data mapping, legacy compatibility |
| [../../backend/docs/event_contracts_v1.md](../../backend/docs/event_contracts_v1.md) | Event sourcing contracts and validation rules | Implementing events, API integration |

### Developer Guides

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [../TESTING.md](../TESTING.md) | Comprehensive testing strategy and guide | Writing tests, running test suite |
| [../DATABASE_SETUP.md](../DATABASE_SETUP.md) | PostgreSQL setup, migrations, and database operations | Database setup, migration creation |
| [../API.md](../API.md) | Complete API endpoint reference with examples | API development, integration |
| [../PLUGIN_DEVELOPMENT.md](../PLUGIN_DEVELOPMENT.md) | Creating specialty plugins for the system | Building specialty extensions |
| [../../CONTRIBUTING.md](../../CONTRIBUTING.md) | Development workflow, PR process, coding standards | Contributing code, development workflow |

### Quick Start Guides

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [../../README.md](../../README.md) | Project overview and quick start | First-time setup, project introduction |
| [../../QUICKSTART.md](../../QUICKSTART.md) | 5-minute getting started guide | Quick local setup, rapid onboarding |
| [../../backend/README.md](../../backend/README.md) | Backend setup and development | Backend development setup |

### Reference Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [../LEGACY_CLAUDE_REFERENCE.md](../LEGACY_CLAUDE_REFERENCE.md) | Context about legacy system for AI-assisted development | AI coding context, historical decisions |
| [../../legacy-reference/core/FpCodes.py](../../legacy-reference/core/FpCodes.py) | **CRITICAL** - Domain enums, teams, locations, roles | Understanding domain model, valid values |
| [../../CLAUDE.md](../../CLAUDE.md) | AI-assisted development guidelines and project rules | AI pair programming, development best practices |

### Reading Path by Role

**New Developers:**
1. README.md → QUICKSTART.md → CONTRIBUTING.md → TESTING.md

**Architects:**
1. ENTERPRISE_ARCHITECTURE_PLAN.md (this doc) → DATABASE_ARCHITECTURE.md → REBUILD_PLAN.md

**Backend Developers:**
1. backend/README.md → docs/API.md → docs/DATABASE_SETUP.md → backend/docs/event_contracts_v1.md

**Frontend Developers:**
1. QUICKSTART.md → docs/API.md → docs/PLUGIN_DEVELOPMENT.md

**DevOps/Infrastructure:**
1. ENTERPRISE_ARCHITECTURE_PLAN.md → REBUILD_PLAN.md → DATABASE_SETUP.md

**Security/Compliance:**
1. ENTERPRISE_ARCHITECTURE_PLAN.md → CODE_REVIEW_REPORT.md → TESTING.md (PHI sections)

**Product/Clinical:**
1. README.md → LEGACY_CLAUDE_REFERENCE.md → CODEBASE_ANALYSIS_AND_REFACTOR_REPORT.md

---

## Executive Summary

### Current State
- Monolithic Dash/Flask application with tightly coupled specialty logic
- Single-tenant design with SQL Server backend
- Custom React components compiled to Dash bindings
- v3 rebuild in progress (FastAPI + Next.js) but still single-specialty focused

### Target State
- Multi-specialty clinical platform with pluggable specialty modules
- Event-sourced architecture for complete audit trail and HIPAA compliance
- Multi-tenant capable (hospital/health-system isolation)
- Configuration-driven UI that adapts to specialty requirements
- Horizontally scalable microservices architecture

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Configuration > Code** | Specialty differences are data, not branches |
| **Events as Truth** | All state changes are immutable events |
| **API-First** | All functionality exposed through versioned APIs |
| **Tenant Isolation** | Data and compute isolation by design |
| **Progressive Enhancement** | Core works everywhere; specialties add capabilities |

---

## Architecture Overview

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              External Systems                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Epic/Cerner EHR  │  Lab Systems (HL7)  │  PACS/Imaging  │  Identity (AAD)  │
└────────┬──────────┴─────────┬───────────┴────────┬───────┴────────┬─────────┘
         │                    │                    │                │
         ▼                    ▼                    ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Integration Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ HL7 FHIR    │  │ ADT Feed    │  │ Results     │  │ SSO/SAML Gateway    │ │
│  │ Adapter     │  │ Processor   │  │ Listener    │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                                     │
│  • Authentication & Authorization (JWT/OAuth2)                               │
│  • Rate Limiting & Throttling                                                │
│  • API Versioning (v1, v2, ...)                                              │
│  • Request/Response Logging                                                  │
│  • Tenant Resolution                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────────┐
│  Core Domain    │        │   Specialty     │        │   Shared Services   │
│  Services       │        │   Modules       │        │                     │
│                 │        │                 │        │                     │
│ • Patient       │        │ • Cardiac       │        │ • Identity/Auth     │
│ • Admission     │        │ • Orthopedics   │        │ • Notification      │
│ • FlightPlan    │        │ • Oncology      │        │ • Document Mgmt     │
│ • ClinicalEvent │        │ • Neurosurgery  │        │ • Audit Service     │
│ • Location      │        │ • Transplant    │        │ • Search (Elastic)  │
│ • Procedure     │        │ • (pluggable)   │        │ • Reporting         │
└────────┬────────┘        └────────┬────────┘        └──────────┬──────────┘
         │                          │                            │
         └──────────────────────────┼────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Event Bus (Kafka)                                  │
│                                                                              │
│  Topics: patient.created, admission.started, event.recorded, location.changed│
│                                                                              │
│  • Guaranteed delivery                                                       │
│  • Event replay capability                                                   │
│  • Consumer groups per service                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                      │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   PostgreSQL    │   Event Store   │   Redis Cache   │   Blob Storage        │
│   (Operational) │   (Immutable)   │   (Sessions)    │   (Documents)         │
│                 │                 │                 │                       │
│ • Current state │ • All events    │ • Session data  │ • Images, PDFs        │
│ • JSONB fields  │ • Audit trail   │ • Projections   │ • Clinical docs       │
│ • Tenant-aware  │ • Replay source │ • Hot data      │ • Encrypted at rest   │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

### Service Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Bounded Contexts                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     PATIENT CONTEXT                                  │    │
│  │  Owns: Patient, Demographics, Insurance, Contacts                   │    │
│  │  Events: PatientCreated, PatientUpdated, PatientMerged              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ADMISSION CONTEXT                                 │    │
│  │  Owns: Admission, Location, Bed, LOS                                │    │
│  │  Events: AdmissionCreated, LocationChanged, DischargeInitiated      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   FLIGHT PLAN CONTEXT                                │    │
│  │  Owns: FlightPlan, Trajectory, Milestones, Projections              │    │
│  │  Events: FlightPlanCreated, TrajectoryUpdated, MilestoneReached     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                  CLINICAL EVENT CONTEXT                              │    │
│  │  Owns: Procedures, Labs, Vitals, Notes, Orders                      │    │
│  │  Events: ProcedureScheduled, ProcedureCompleted, LabResultReceived  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   SPECIALTY CONTEXT (Pluggable)                      │    │
│  │  Owns: Specialty-specific fields, workflows, calculations           │    │
│  │  Events: Defined per specialty module                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer Deep Dives

### 1. Specialty Plugin System

The specialty plugin system allows adding new clinical specialties without modifying core code.

#### Plugin Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Plugin Registry                                    │
│  • Discovers and loads specialty modules at startup                          │
│  • Validates plugin contracts                                                │
│  • Manages plugin lifecycle                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Cardiac Plugin  │      │ Ortho Plugin    │      │ Oncology Plugin │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│ • manifest.yaml │      │ • manifest.yaml │      │ • manifest.yaml │
│ • schema/       │      │ • schema/       │      │ • schema/       │
│ • workflows/    │      │ • workflows/    │      │ • workflows/    │
│ • components/   │      │ • components/   │      │ • components/   │
│ • calculations/ │      │ • calculations/ │      │ • calculations/ │
│ • validations/  │      │ • validations/  │      │ • validations/  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

#### Specialty Manifest Schema

```yaml
# plugins/cardiac/manifest.yaml
apiVersion: flightplan.io/v1
kind: SpecialtyPlugin
metadata:
  name: cardiac
  version: 2.1.0
  displayName: "Cardiac Surgery"
  description: "Cardiac surgery care planning module"
  author: "FlightPlan Team"

spec:
  # Database schema extensions
  schema:
    patient_extensions:
      - name: ejection_fraction
        type: decimal
        precision: 5
        scale: 2
        nullable: true
        validation:
          min: 0
          max: 100
        ui:
          label: "Ejection Fraction (%)"
          component: number-input
          placement: vital-signs

      - name: nyha_class
        type: enum
        values: ["I", "II", "III", "IV"]
        ui:
          label: "NYHA Classification"
          component: radio-group
          placement: assessment

      - name: sts_score
        type: decimal
        precision: 5
        scale: 3
        computed: true  # Calculated field
        calculator: "cardiac.calculators.sts_score"
        ui:
          label: "STS Risk Score"
          component: read-only
          placement: risk-assessment

    admission_extensions:
      - name: perfusion_time
        type: integer
        nullable: true
        ui:
          label: "Perfusion Time (min)"

      - name: cross_clamp_time
        type: integer
        nullable: true
        ui:
          label: "Cross Clamp Time (min)"

  # Clinical event types specific to this specialty
  event_types:
    - id: cardiac.cath_lab
      name: "Cardiac Catheterization"
      category: procedure
      fields:
        - name: access_site
          type: enum
          values: ["Radial", "Femoral", "Brachial"]
        - name: findings
          type: text
      milestone: pre_operative

    - id: cardiac.cabg
      name: "CABG Surgery"
      category: procedure
      fields:
        - name: grafts
          type: integer
        - name: technique
          type: enum
          values: ["On-Pump", "Off-Pump", "Hybrid"]
      milestone: operative

    - id: cardiac.valve_replacement
      name: "Valve Replacement"
      category: procedure
      fields:
        - name: valve_position
          type: enum
          values: ["Aortic", "Mitral", "Tricuspid", "Pulmonary"]
        - name: valve_type
          type: enum
          values: ["Mechanical", "Bioprosthetic", "Transcatheter"]

  # Trajectory/Timeline configuration
  trajectory:
    default_los_days: 7
    phases:
      - id: pre_op
        name: "Pre-Operative"
        duration_days: 1
        milestones:
          - cath_complete
          - clearances_obtained
          - consent_signed

      - id: operative
        name: "Operative Day"
        duration_days: 1
        milestones:
          - surgery_complete
          - to_icu

      - id: icu
        name: "ICU Recovery"
        duration_days: 2
        milestones:
          - extubated
          - chest_tubes_removed
          - transfer_floor

      - id: floor
        name: "Floor Recovery"
        duration_days: 3
        milestones:
          - ambulating
          - diet_advanced
          - discharge_ready

  # Workflow definitions
  workflows:
    pre_op_checklist:
      name: "Pre-Operative Checklist"
      trigger: admission.created
      steps:
        - id: verify_consent
          type: checkbox
          label: "Surgical consent signed"
          required: true

        - id: type_screen
          type: checkbox
          label: "Type & Screen completed"
          required: true

        - id: cardiac_clearance
          type: approval
          label: "Cardiology clearance"
          approvers:
            - role: cardiologist

    discharge_criteria:
      name: "Discharge Readiness"
      steps:
        - id: pain_controlled
          type: checkbox
          label: "Pain controlled on oral medications"
        - id: ambulating
          type: checkbox
          label: "Ambulating independently"
        - id: wound_check
          type: checkbox
          label: "Wound healing appropriately"

  # UI Layout customizations
  ui:
    patient_header:
      primary_fields:
        - mrn
        - name
        - age
        - ejection_fraction
        - nyha_class
      secondary_fields:
        - sts_score
        - attending

    timeline:
      event_categories:
        - id: cardiac_procedures
          name: "Cardiac Procedures"
          color: "#DC2626"
          icon: "heart"
          events:
            - cardiac.cath_lab
            - cardiac.cabg
            - cardiac.valve_replacement

    sidebar_sections:
      - id: risk_scores
        name: "Risk Assessment"
        component: "cardiac/RiskScorePanel"
        position: 1

      - id: perfusion_data
        name: "Perfusion Data"
        component: "cardiac/PerfusionPanel"
        position: 2
        collapsed_by_default: true

  # Calculations and derived fields
  calculators:
    - id: sts_score
      name: "STS Risk Score"
      inputs:
        - age
        - gender
        - ejection_fraction
        - nyha_class
        - diabetes
        - renal_function
      output: decimal
      implementation: "cardiac.calculators.compute_sts_score"

    - id: euroscore
      name: "EuroSCORE II"
      inputs:
        - age
        - gender
        - ejection_fraction
        - procedure_type
      output: decimal
      implementation: "cardiac.calculators.compute_euroscore"

  # Validation rules
  validations:
    - id: cabg_requires_cath
      description: "CABG requires prior catheterization"
      trigger: event.cardiac.cabg.scheduled
      rule: |
        EXISTS(events WHERE type = 'cardiac.cath_lab' AND status = 'completed')
      severity: error
      message: "Cannot schedule CABG without completed catheterization"

    - id: ef_warning
      description: "Low EF warning"
      trigger: patient.ejection_fraction.updated
      rule: |
        patient.ejection_fraction < 30
      severity: warning
      message: "Ejection fraction below 30% - high risk patient"

  # Reports specific to specialty
  reports:
    - id: cabg_outcomes
      name: "CABG Outcomes Report"
      type: aggregate
      fields:
        - surgery_date
        - grafts_count
        - perfusion_time
        - los_days
        - complications

    - id: valve_registry
      name: "Valve Registry Export"
      type: registry
      format: STS_AVR_FORMAT
```

#### Plugin Loading Mechanism (Python/FastAPI)

```python
# app/core/plugins/registry.py
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel

class SpecialtyPlugin(BaseModel):
    """Loaded specialty plugin"""
    name: str
    version: str
    display_name: str
    manifest: dict
    schema_extensions: List[dict]
    event_types: List[dict]
    workflows: List[dict]
    ui_config: dict
    calculators: Dict[str, callable]
    validations: List[dict]

class PluginRegistry:
    """
    Discovers, loads, and manages specialty plugins.
    """

    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._plugins: Dict[str, SpecialtyPlugin] = {}
        self._loaded = False

    def discover_plugins(self) -> List[str]:
        """Find all plugin directories with manifest.yaml"""
        plugins = []
        for path in self.plugins_dir.iterdir():
            if path.is_dir() and (path / "manifest.yaml").exists():
                plugins.append(path.name)
        return plugins

    def load_plugin(self, name: str) -> SpecialtyPlugin:
        """Load a single plugin by name"""
        plugin_path = self.plugins_dir / name
        manifest_path = plugin_path / "manifest.yaml"

        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)

        # Validate manifest against schema
        self._validate_manifest(manifest)

        # Load calculators (Python modules)
        calculators = self._load_calculators(plugin_path, manifest)

        plugin = SpecialtyPlugin(
            name=name,
            version=manifest["metadata"]["version"],
            display_name=manifest["metadata"]["displayName"],
            manifest=manifest,
            schema_extensions=manifest["spec"].get("schema", {}),
            event_types=manifest["spec"].get("event_types", []),
            workflows=manifest["spec"].get("workflows", {}),
            ui_config=manifest["spec"].get("ui", {}),
            calculators=calculators,
            validations=manifest["spec"].get("validations", [])
        )

        self._plugins[name] = plugin
        return plugin

    def load_all(self) -> None:
        """Load all discovered plugins"""
        for name in self.discover_plugins():
            self.load_plugin(name)
        self._loaded = True

    def get_plugin(self, name: str) -> Optional[SpecialtyPlugin]:
        """Get a loaded plugin by name"""
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[SpecialtyPlugin]:
        """Get all loaded plugins"""
        return list(self._plugins.values())

    def get_schema_extensions(self, specialty: str) -> dict:
        """Get database schema extensions for a specialty"""
        plugin = self._plugins.get(specialty)
        if not plugin:
            return {}
        return plugin.schema_extensions

    def get_event_types(self, specialty: str) -> List[dict]:
        """Get clinical event types for a specialty"""
        plugin = self._plugins.get(specialty)
        if not plugin:
            return []
        return plugin.event_types

    def get_ui_config(self, specialty: str) -> dict:
        """Get UI configuration for a specialty"""
        plugin = self._plugins.get(specialty)
        if not plugin:
            return {}
        return plugin.ui_config

    def execute_calculator(
        self,
        specialty: str,
        calculator_id: str,
        inputs: dict
    ) -> any:
        """Execute a specialty-specific calculator"""
        plugin = self._plugins.get(specialty)
        if not plugin or calculator_id not in plugin.calculators:
            raise ValueError(f"Calculator {calculator_id} not found")

        return plugin.calculators[calculator_id](inputs)

    def _validate_manifest(self, manifest: dict) -> None:
        """Validate manifest against plugin schema"""
        # Implementation: JSON Schema validation
        pass

    def _load_calculators(self, plugin_path: Path, manifest: dict) -> dict:
        """Dynamically load calculator functions"""
        calculators = {}
        for calc in manifest["spec"].get("calculators", []):
            module_path = calc["implementation"]
            # Dynamic import and load
            # calculators[calc["id"]] = loaded_function
        return calculators


# Usage in FastAPI app startup
# app/main.py
from app.core.plugins.registry import PluginRegistry

plugin_registry = PluginRegistry(Path("plugins"))

@app.on_event("startup")
async def load_plugins():
    plugin_registry.load_all()
    logger.info(f"Loaded {len(plugin_registry.get_all_plugins())} specialty plugins")
```

#### Frontend Plugin Integration

```typescript
// frontend/src/lib/plugins/PluginContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';

interface SpecialtyConfig {
  name: string;
  displayName: string;
  patientHeader: {
    primaryFields: string[];
    secondaryFields: string[];
  };
  sidebarSections: SidebarSection[];
  eventCategories: EventCategory[];
  calculators: CalculatorConfig[];
}

interface PluginContextType {
  specialty: string | null;
  config: SpecialtyConfig | null;
  loading: boolean;
  setSpecialty: (specialty: string) => void;
}

const PluginContext = createContext<PluginContextType | null>(null);

export function PluginProvider({ children }: { children: React.ReactNode }) {
  const [specialty, setSpecialty] = useState<string | null>(null);
  const [config, setConfig] = useState<SpecialtyConfig | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (specialty) {
      setLoading(true);
      fetch(`/api/v1/specialties/${specialty}/config`)
        .then(res => res.json())
        .then(data => {
          setConfig(data);
          setLoading(false);
        });
    }
  }, [specialty]);

  return (
    <PluginContext.Provider value={{ specialty, config, loading, setSpecialty }}>
      {children}
    </PluginContext.Provider>
  );
}

export function usePlugin() {
  const context = useContext(PluginContext);
  if (!context) {
    throw new Error('usePlugin must be used within PluginProvider');
  }
  return context;
}

// Dynamic component loading for specialty-specific panels
// frontend/src/lib/plugins/DynamicPanel.tsx
import dynamic from 'next/dynamic';

const specialtyComponents: Record<string, Record<string, React.ComponentType>> = {
  cardiac: {
    RiskScorePanel: dynamic(() => import('@/components/specialties/cardiac/RiskScorePanel')),
    PerfusionPanel: dynamic(() => import('@/components/specialties/cardiac/PerfusionPanel')),
  },
  orthopedics: {
    MobilityPanel: dynamic(() => import('@/components/specialties/orthopedics/MobilityPanel')),
    ImplantPanel: dynamic(() => import('@/components/specialties/orthopedics/ImplantPanel')),
  },
};

export function DynamicPanel({
  specialty,
  componentName,
  props
}: {
  specialty: string;
  componentName: string;
  props: any
}) {
  const Component = specialtyComponents[specialty]?.[componentName];

  if (!Component) {
    return <div>Component not found: {specialty}/{componentName}</div>;
  }

  return <Component {...props} />;
}
```

---

### 2. Event Sourcing for Clinical Events

Event sourcing stores all state changes as immutable events, providing complete audit trail, temporal queries, and replay capability.

#### Event Store Schema

```sql
-- PostgreSQL schema for event store

-- Core event store table (append-only)
CREATE TABLE events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id       UUID NOT NULL,                    -- Aggregate ID (e.g., admission_id)
    stream_type     VARCHAR(100) NOT NULL,            -- e.g., 'Admission', 'FlightPlan'
    event_type      VARCHAR(200) NOT NULL,            -- e.g., 'LocationChanged'
    event_version   INTEGER NOT NULL,                 -- Version within stream
    tenant_id       UUID NOT NULL,                    -- Multi-tenant isolation

    -- Event payload
    data            JSONB NOT NULL,                   -- Event-specific data
    metadata        JSONB NOT NULL DEFAULT '{}',      -- Correlation IDs, user info, etc.

    -- Audit fields
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID NOT NULL,                    -- User who triggered event

    -- Ordering
    global_position BIGSERIAL NOT NULL,               -- Global ordering across all events

    -- Constraints
    CONSTRAINT unique_stream_version UNIQUE (stream_id, event_version)
);

-- Indexes for common query patterns
CREATE INDEX idx_events_stream ON events (stream_id, event_version);
CREATE INDEX idx_events_type ON events (event_type, created_at);
CREATE INDEX idx_events_tenant ON events (tenant_id, created_at);
CREATE INDEX idx_events_global_position ON events (global_position);
CREATE INDEX idx_events_created_at ON events (created_at);

-- GIN index for JSONB queries
CREATE INDEX idx_events_data ON events USING GIN (data);

-- Snapshots for performance (periodic state snapshots)
CREATE TABLE snapshots (
    snapshot_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id       UUID NOT NULL,
    stream_type     VARCHAR(100) NOT NULL,
    version         INTEGER NOT NULL,                 -- Event version at snapshot
    state           JSONB NOT NULL,                   -- Serialized aggregate state
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_stream_snapshot UNIQUE (stream_id, version)
);

-- Subscriptions (for projections and integrations)
CREATE TABLE subscriptions (
    subscription_id VARCHAR(200) PRIMARY KEY,
    last_position   BIGINT NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Event Types for Clinical Domain

```python
# app/domain/events/clinical_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

class EventBase:
    """Base class for all domain events"""
    event_type: str
    occurred_at: datetime
    caused_by: UUID  # User ID
    correlation_id: UUID  # For tracing related events

@dataclass
class PatientCreated(EventBase):
    event_type = "patient.created"
    patient_id: UUID
    mrn: str  # Encrypted
    first_name: str
    last_name: str
    date_of_birth: datetime
    gender: str

@dataclass
class AdmissionCreated(EventBase):
    event_type = "admission.created"
    admission_id: UUID
    patient_id: UUID
    specialty: str
    attending_id: UUID
    admit_date: datetime
    chief_complaint: str
    admission_type: str  # Elective, Emergency, Transfer

@dataclass
class LocationChanged(EventBase):
    event_type = "admission.location_changed"
    admission_id: UUID
    from_location: Optional[str]
    to_location: str
    from_bed: Optional[str]
    to_bed: Optional[str]
    effective_at: datetime
    reason: Optional[str]

@dataclass
class ProcedureScheduled(EventBase):
    event_type = "procedure.scheduled"
    procedure_id: UUID
    admission_id: UUID
    procedure_type: str
    scheduled_date: datetime
    scheduled_by: UUID
    estimated_duration_minutes: int
    specialty_data: dict  # Specialty-specific fields

@dataclass
class ProcedureCompleted(EventBase):
    event_type = "procedure.completed"
    procedure_id: UUID
    admission_id: UUID
    actual_start: datetime
    actual_end: datetime
    performed_by: List[UUID]
    outcome: str
    complications: List[str]
    specialty_data: dict

@dataclass
class ClinicalNoteAdded(EventBase):
    event_type = "note.added"
    note_id: UUID
    admission_id: UUID
    note_type: str  # Progress, Consult, Procedure, Discharge
    content_encrypted: str
    authored_by: UUID
    cosigned_by: Optional[UUID]

@dataclass
class MilestoneReached(EventBase):
    event_type = "flightplan.milestone_reached"
    flightplan_id: UUID
    admission_id: UUID
    milestone_id: str
    milestone_name: str
    reached_at: datetime
    verified_by: UUID

@dataclass
class DischargeInitiated(EventBase):
    event_type = "admission.discharge_initiated"
    admission_id: UUID
    planned_discharge_date: datetime
    disposition: str  # Home, SNF, Rehab, LTAC, Deceased
    initiated_by: UUID

@dataclass
class DischargeCompleted(EventBase):
    event_type = "admission.discharge_completed"
    admission_id: UUID
    actual_discharge_date: datetime
    disposition: str
    discharge_summary_id: UUID
    follow_up_appointments: List[dict]
```

#### Event Store Implementation

```python
# app/infrastructure/event_store.py
from typing import List, Optional, Type, TypeVar
from uuid import UUID
from datetime import datetime
import json

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events.base import EventBase
from app.models.event_store import EventModel, SnapshotModel

T = TypeVar('T', bound=EventBase)

class EventStore:
    """
    Append-only event store with optimistic concurrency control.
    """

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def append(
        self,
        stream_id: UUID,
        stream_type: str,
        events: List[EventBase],
        expected_version: Optional[int] = None
    ) -> int:
        """
        Append events to a stream with optimistic concurrency.

        Args:
            stream_id: The aggregate/stream ID
            stream_type: Type of aggregate (e.g., 'Admission')
            events: List of events to append
            expected_version: Expected current version (for concurrency check)

        Returns:
            New stream version after append

        Raises:
            ConcurrencyError: If expected_version doesn't match
        """
        # Get current version
        current_version = await self._get_current_version(stream_id)

        if expected_version is not None and current_version != expected_version:
            raise ConcurrencyError(
                f"Expected version {expected_version}, but found {current_version}"
            )

        # Append events
        new_version = current_version
        for event in events:
            new_version += 1
            event_model = EventModel(
                stream_id=stream_id,
                stream_type=stream_type,
                event_type=event.event_type,
                event_version=new_version,
                tenant_id=self.tenant_id,
                data=self._serialize_event(event),
                metadata={
                    "correlation_id": str(event.correlation_id),
                    "caused_by": str(event.caused_by),
                },
                created_by=event.caused_by,
            )
            self.session.add(event_model)

        await self.session.flush()
        return new_version

    async def load_stream(
        self,
        stream_id: UUID,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[EventBase]:
        """Load events for a stream, optionally within version range"""
        query = select(EventModel).where(
            and_(
                EventModel.stream_id == stream_id,
                EventModel.tenant_id == self.tenant_id,
                EventModel.event_version > from_version
            )
        ).order_by(EventModel.event_version)

        if to_version:
            query = query.where(EventModel.event_version <= to_version)

        result = await self.session.execute(query)
        event_models = result.scalars().all()

        return [self._deserialize_event(em) for em in event_models]

    async def load_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[EventBase]:
        """Load events by type across all streams (for projections)"""
        query = select(EventModel).where(
            and_(
                EventModel.event_type == event_type,
                EventModel.tenant_id == self.tenant_id
            )
        ).order_by(EventModel.global_position).limit(limit)

        if since:
            query = query.where(EventModel.created_at > since)

        result = await self.session.execute(query)
        return [self._deserialize_event(em) for em in result.scalars().all()]

    async def get_all_events_since(
        self,
        position: int,
        limit: int = 1000
    ) -> List[EventBase]:
        """Get all events since a global position (for subscriptions)"""
        query = select(EventModel).where(
            and_(
                EventModel.global_position > position,
                EventModel.tenant_id == self.tenant_id
            )
        ).order_by(EventModel.global_position).limit(limit)

        result = await self.session.execute(query)
        return [self._deserialize_event(em) for em in result.scalars().all()]

    async def save_snapshot(
        self,
        stream_id: UUID,
        stream_type: str,
        version: int,
        state: dict
    ) -> None:
        """Save aggregate snapshot for faster loading"""
        snapshot = SnapshotModel(
            stream_id=stream_id,
            stream_type=stream_type,
            version=version,
            state=state
        )
        self.session.add(snapshot)
        await self.session.flush()

    async def load_snapshot(
        self,
        stream_id: UUID
    ) -> Optional[tuple[int, dict]]:
        """Load latest snapshot for a stream"""
        query = select(SnapshotModel).where(
            SnapshotModel.stream_id == stream_id
        ).order_by(SnapshotModel.version.desc()).limit(1)

        result = await self.session.execute(query)
        snapshot = result.scalar_one_or_none()

        if snapshot:
            return (snapshot.version, snapshot.state)
        return None

    async def _get_current_version(self, stream_id: UUID) -> int:
        query = select(EventModel.event_version).where(
            and_(
                EventModel.stream_id == stream_id,
                EventModel.tenant_id == self.tenant_id
            )
        ).order_by(EventModel.event_version.desc()).limit(1)

        result = await self.session.execute(query)
        version = result.scalar_one_or_none()
        return version or 0

    def _serialize_event(self, event: EventBase) -> dict:
        """Serialize event to JSON-compatible dict"""
        # Implementation depends on your serialization strategy
        pass

    def _deserialize_event(self, model: EventModel) -> EventBase:
        """Deserialize event from storage"""
        # Implementation depends on your serialization strategy
        pass


class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails"""
    pass
```

#### Projections (Read Models)

```python
# app/infrastructure/projections/admission_projection.py
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.domain.events.clinical_events import (
    AdmissionCreated,
    LocationChanged,
    DischargeCompleted
)
from app.models.read_models import AdmissionReadModel

class AdmissionProjection:
    """
    Builds and maintains the admissions read model from events.
    This is the "current state" view optimized for queries.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def handle(self, event) -> None:
        """Route event to appropriate handler"""
        handlers = {
            "admission.created": self._handle_admission_created,
            "admission.location_changed": self._handle_location_changed,
            "admission.discharge_completed": self._handle_discharge_completed,
        }

        handler = handlers.get(event.event_type)
        if handler:
            await handler(event)

    async def _handle_admission_created(self, event: AdmissionCreated) -> None:
        """Create new admission read model"""
        admission = AdmissionReadModel(
            id=event.admission_id,
            patient_id=event.patient_id,
            specialty=event.specialty,
            attending_id=event.attending_id,
            admit_date=event.admit_date,
            chief_complaint=event.chief_complaint,
            status="Active",
            current_location=None,
            current_bed=None,
            los_days=0,
            created_at=event.occurred_at,
            updated_at=event.occurred_at,
        )
        self.session.add(admission)
        await self.session.flush()

    async def _handle_location_changed(self, event: LocationChanged) -> None:
        """Update current location in read model"""
        await self.session.execute(
            update(AdmissionReadModel)
            .where(AdmissionReadModel.id == event.admission_id)
            .values(
                current_location=event.to_location,
                current_bed=event.to_bed,
                updated_at=event.occurred_at,
            )
        )

    async def _handle_discharge_completed(self, event: DischargeCompleted) -> None:
        """Mark admission as discharged"""
        # Calculate LOS
        admission = await self.session.get(AdmissionReadModel, event.admission_id)
        los_days = (event.actual_discharge_date - admission.admit_date).days

        await self.session.execute(
            update(AdmissionReadModel)
            .where(AdmissionReadModel.id == event.admission_id)
            .values(
                status="Discharged",
                discharge_date=event.actual_discharge_date,
                disposition=event.disposition,
                los_days=los_days,
                updated_at=event.occurred_at,
            )
        )


# Projection runner (background worker)
# app/infrastructure/projections/runner.py
class ProjectionRunner:
    """
    Runs projections by subscribing to the event store.
    Maintains checkpoint for resumability.
    """

    def __init__(
        self,
        event_store: EventStore,
        projections: list,
        subscription_id: str
    ):
        self.event_store = event_store
        self.projections = projections
        self.subscription_id = subscription_id

    async def run(self) -> None:
        """Main projection loop"""
        position = await self._get_checkpoint()

        while True:
            events = await self.event_store.get_all_events_since(
                position=position,
                limit=100
            )

            if not events:
                await asyncio.sleep(1)  # Poll interval
                continue

            for event in events:
                for projection in self.projections:
                    await projection.handle(event)
                position = event.global_position

            await self._save_checkpoint(position)

    async def _get_checkpoint(self) -> int:
        # Load from subscriptions table
        pass

    async def _save_checkpoint(self, position: int) -> None:
        # Save to subscriptions table
        pass
```

#### Temporal Queries (Point-in-Time)

```python
# app/services/temporal_query.py
from datetime import datetime
from uuid import UUID
from typing import TypeVar, Type

from app.infrastructure.event_store import EventStore
from app.domain.aggregates.admission import Admission

T = TypeVar('T')

class TemporalQueryService:
    """
    Reconstruct aggregate state at any point in time.
    Useful for audits, debugging, and historical analysis.
    """

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def get_state_at(
        self,
        aggregate_type: Type[T],
        aggregate_id: UUID,
        as_of: datetime
    ) -> T:
        """
        Reconstruct aggregate state as it was at a specific point in time.

        Example:
            admission = await temporal.get_state_at(
                Admission,
                admission_id,
                datetime(2024, 6, 15, 10, 30)
            )
            # Returns the admission state as of June 15, 2024 at 10:30 AM
        """
        # Load all events up to the specified time
        events = await self.event_store.load_stream(aggregate_id)
        events_before = [e for e in events if e.occurred_at <= as_of]

        # Replay events to build state
        aggregate = aggregate_type()
        for event in events_before:
            aggregate.apply(event)

        return aggregate

    async def get_history(
        self,
        aggregate_id: UUID,
        from_date: datetime = None,
        to_date: datetime = None
    ) -> list:
        """
        Get complete history of an aggregate.
        Returns list of (timestamp, event_type, event_data) tuples.
        """
        events = await self.event_store.load_stream(aggregate_id)

        history = []
        for event in events:
            if from_date and event.occurred_at < from_date:
                continue
            if to_date and event.occurred_at > to_date:
                continue
            history.append({
                "timestamp": event.occurred_at,
                "event_type": event.event_type,
                "data": event.to_dict(),
                "user": event.caused_by
            })

        return history
```

---

### 3. Multi-Tenant Database Strategy

#### Tenant Isolation Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Multi-Tenancy Isolation Levels                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Option 1: SHARED DATABASE, SHARED SCHEMA (tenant_id column)                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Database: flightplan_prod                                           │    │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │    │
│  │ │ Table: patients                                                 │ │    │
│  │ │ ┌─────────┬─────────┬──────────┬────────────────────────────┐  │ │    │
│  │ │ │ id      │ tenant  │ mrn      │ name                       │  │ │    │
│  │ │ ├─────────┼─────────┼──────────┼────────────────────────────┤  │ │    │
│  │ │ │ uuid-1  │ hosp-a  │ ****     │ ****                       │  │ │    │
│  │ │ │ uuid-2  │ hosp-b  │ ****     │ ****                       │  │ │    │
│  │ │ │ uuid-3  │ hosp-a  │ ****     │ ****                       │  │ │    │
│  │ │ └─────────┴─────────┴──────────┴────────────────────────────┘  │ │    │
│  │ └─────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  Pros: Simple, cost-effective, easy migrations                              │
│  Cons: Noisy neighbor risk, careful RLS needed                              │
│                                                                              │
│  Option 2: SHARED DATABASE, SEPARATE SCHEMAS                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Database: flightplan_prod                                           │    │
│  │ ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │    │
│  │ │ Schema: hosp_a    │  │ Schema: hosp_b    │  │ Schema: hosp_c  │  │    │
│  │ │ • patients        │  │ • patients        │  │ • patients      │  │    │
│  │ │ • admissions      │  │ • admissions      │  │ • admissions    │  │    │
│  │ │ • events          │  │ • events          │  │ • events        │  │    │
│  │ └───────────────────┘  └───────────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  Pros: Better isolation, per-tenant backup/restore                          │
│  Cons: More complex migrations, connection management                       │
│                                                                              │
│  Option 3: SEPARATE DATABASES (Full isolation)                              │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐   │
│  │ DB: fp_hosp_a     │  │ DB: fp_hosp_b     │  │ DB: fp_hosp_c         │   │
│  │ • patients        │  │ • patients        │  │ • patients            │   │
│  │ • admissions      │  │ • admissions      │  │ • admissions          │   │
│  │ • events          │  │ • events          │  │ • events              │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────────┘   │
│  Pros: Complete isolation, independent scaling, compliance                  │
│  Cons: Higher cost, complex cross-tenant reporting                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

RECOMMENDATION: Start with Option 1 (shared schema with tenant_id + RLS)
                Plan migration path to Option 2/3 for enterprise customers
```

#### Row-Level Security Implementation (PostgreSQL)

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE admissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_notes ENABLE ROW LEVEL SECURITY;

-- Create a function to get current tenant from session
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', true)::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- RLS Policies: Users can only see their tenant's data
CREATE POLICY tenant_isolation_patients ON patients
    USING (tenant_id = current_tenant_id());

CREATE POLICY tenant_isolation_admissions ON admissions
    USING (tenant_id = current_tenant_id());

CREATE POLICY tenant_isolation_events ON events
    USING (tenant_id = current_tenant_id());

-- Separate policies for INSERT (need to set tenant_id)
CREATE POLICY tenant_insert_patients ON patients
    FOR INSERT
    WITH CHECK (tenant_id = current_tenant_id());

-- Super-admin bypass (for support/maintenance)
CREATE POLICY admin_bypass_patients ON patients
    USING (current_setting('app.is_super_admin', true)::boolean = true);
```

#### SQLAlchemy Multi-Tenant Session

```python
# app/core/database/tenant.py
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Context variable to hold current tenant
current_tenant: ContextVar[Optional[UUID]] = ContextVar('current_tenant', default=None)

class TenantAwareSession:
    """
    SQLAlchemy session that automatically applies tenant context.
    """

    def __init__(self, engine_url: str):
        self.engine = create_async_engine(engine_url)
        self.SessionFactory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Set up event listeners
        event.listen(self.engine.sync_engine, 'connect', self._on_connect)

    def _on_connect(self, dbapi_conn, connection_record):
        """Set up RLS on new connections"""
        pass  # Connection pool setup

    async def get_session(self, tenant_id: UUID) -> AsyncSession:
        """Get a session scoped to a specific tenant"""
        session = self.SessionFactory()

        # Set the tenant context for RLS
        await session.execute(
            f"SET app.current_tenant_id = '{tenant_id}'"
        )

        # Also set in context var for application use
        current_tenant.set(tenant_id)

        return session

    async def get_admin_session(self) -> AsyncSession:
        """Get a session with super-admin privileges (bypasses RLS)"""
        session = self.SessionFactory()
        await session.execute("SET app.is_super_admin = true")
        return session


# FastAPI dependency
# app/api/deps.py
from fastapi import Depends, Request
from app.core.database.tenant import TenantAwareSession, current_tenant

tenant_db = TenantAwareSession(settings.DATABASE_URL)

async def get_tenant_id(request: Request) -> UUID:
    """Extract tenant ID from JWT or header"""
    # From JWT claims
    tenant_id = request.state.user.tenant_id
    return tenant_id

async def get_db(
    tenant_id: UUID = Depends(get_tenant_id)
) -> AsyncSession:
    """Get tenant-scoped database session"""
    session = await tenant_db.get_session(tenant_id)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

#### Tenant Configuration Model

```python
# app/models/tenant.py
from sqlalchemy import Column, String, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Tenant(Base):
    """
    Tenant (hospital/health system) configuration.
    Stored in a shared 'system' schema, not tenant-scoped.
    """
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'system'}

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True)  # hosp-a.flightplan.io

    # Subscription/licensing
    plan = Column(String(50), default='standard')  # standard, enterprise
    is_active = Column(Boolean, default=True)

    # Feature flags per tenant
    features = Column(JSON, default={})
    # Example: {"cardiac_module": true, "ortho_module": false, "api_access": true}

    # Specialty configuration
    enabled_specialties = Column(JSON, default=[])
    # Example: ["cardiac", "orthopedics"]

    # Branding
    branding = Column(JSON, default={})
    # Example: {"logo_url": "...", "primary_color": "#1a56db"}

    # Integration settings
    integrations = Column(JSON, default={})
    # Example: {"ehr": {"type": "epic", "base_url": "..."}}

    # Audit
    created_at = Column(DateTime, server_default='now()')
    updated_at = Column(DateTime, onupdate='now()')


# Tenant resolution middleware
# app/middleware/tenant.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Resolves tenant from subdomain or header.
    """

    async def dispatch(self, request: Request, call_next):
        # Option 1: From subdomain
        host = request.headers.get('host', '')
        subdomain = host.split('.')[0] if '.' in host else None

        # Option 2: From header (for API clients)
        tenant_header = request.headers.get('X-Tenant-ID')

        # Option 3: From JWT claims (already authenticated)
        # tenant_id = request.state.user.tenant_id

        if subdomain:
            tenant = await self._get_tenant_by_subdomain(subdomain)
            request.state.tenant = tenant
        elif tenant_header:
            tenant = await self._get_tenant_by_id(tenant_header)
            request.state.tenant = tenant

        response = await call_next(request)
        return response
```

---

### 4. Frontend Design System

#### Component Library Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Design System Architecture                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    DESIGN TOKENS (Foundation)                        │    │
│  │  • Colors (brand, semantic, specialty-specific)                      │    │
│  │  • Typography (font families, sizes, weights)                        │    │
│  │  • Spacing (consistent spacing scale)                                │    │
│  │  • Shadows, borders, radii                                           │    │
│  │  • Motion (animation durations, easings)                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PRIMITIVE COMPONENTS (Atoms)                      │    │
│  │  Button, Input, Select, Checkbox, Badge, Avatar, Icon               │    │
│  │  • Fully accessible (WCAG 2.1 AA)                                    │    │
│  │  • Theme-aware (light/dark, specialty colors)                        │    │
│  │  • No business logic                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    COMPOSITE COMPONENTS (Molecules)                  │    │
│  │  Card, Modal, Dropdown, Table, Tabs, DataGrid                       │    │
│  │  • Composed from primitives                                          │    │
│  │  • Reusable patterns                                                 │    │
│  │  • Configuration-driven variants                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   CLINICAL COMPONENTS (Organisms)                    │    │
│  │  PatientHeader, Timeline, VitalSigns, MedicationList, WorkflowPanel │    │
│  │  • Domain-specific                                                   │    │
│  │  • Configurable via specialty plugins                                │    │
│  │  • Connected to data layer                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      PAGE TEMPLATES (Templates)                      │    │
│  │  PatientListPage, PatientDetailPage, DashboardPage                  │    │
│  │  • Layout patterns                                                   │    │
│  │  • Specialty-aware composition                                       │    │
│  │  • Responsive breakpoints                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Design Tokens

```typescript
// packages/design-system/tokens/tokens.ts

export const tokens = {
  // ═══════════════════════════════════════════════════════════════════════
  // COLORS
  // ═══════════════════════════════════════════════════════════════════════
  colors: {
    // Brand colors
    brand: {
      primary: '#1a56db',
      secondary: '#7c3aed',
      accent: '#0891b2',
    },

    // Semantic colors
    semantic: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },

    // Clinical status colors (consistent across specialties)
    clinical: {
      critical: '#dc2626',      // Critical/unstable patient
      guarded: '#f97316',       // Guarded condition
      stable: '#22c55e',        // Stable/good
      improving: '#06b6d4',     // Improving trajectory
      declining: '#f43f5e',     // Declining trajectory
    },

    // Specialty accent colors
    specialty: {
      cardiac: '#dc2626',       // Heart red
      orthopedics: '#0ea5e9',   // Bone blue
      oncology: '#8b5cf6',      // Purple
      neurosurgery: '#6366f1',  // Indigo
      transplant: '#10b981',    // Green
    },

    // Neutral palette
    neutral: {
      50: '#fafafa',
      100: '#f4f4f5',
      200: '#e4e4e7',
      300: '#d4d4d8',
      400: '#a1a1aa',
      500: '#71717a',
      600: '#52525b',
      700: '#3f3f46',
      800: '#27272a',
      900: '#18181b',
    },

    // Background/surface
    background: {
      primary: '#ffffff',
      secondary: '#f4f4f5',
      tertiary: '#e4e4e7',
    },

    // Dark mode variants
    dark: {
      background: {
        primary: '#18181b',
        secondary: '#27272a',
        tertiary: '#3f3f46',
      },
    },
  },

  // ═══════════════════════════════════════════════════════════════════════
  // TYPOGRAPHY
  // ═══════════════════════════════════════════════════════════════════════
  typography: {
    fontFamily: {
      sans: 'Inter, system-ui, sans-serif',
      mono: 'JetBrains Mono, monospace',
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem',// 30px
      '4xl': '2.25rem', // 36px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  // ═══════════════════════════════════════════════════════════════════════
  // SPACING
  // ═══════════════════════════════════════════════════════════════════════
  spacing: {
    0: '0',
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
    16: '4rem',     // 64px
    20: '5rem',     // 80px
  },

  // ═══════════════════════════════════════════════════════════════════════
  // BORDERS & SHADOWS
  // ═══════════════════════════════════════════════════════════════════════
  borders: {
    radius: {
      none: '0',
      sm: '0.25rem',
      md: '0.375rem',
      lg: '0.5rem',
      xl: '0.75rem',
      full: '9999px',
    },
    width: {
      thin: '1px',
      medium: '2px',
      thick: '4px',
    },
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
  },

  // ═══════════════════════════════════════════════════════════════════════
  // MOTION
  // ═══════════════════════════════════════════════════════════════════════
  motion: {
    duration: {
      instant: '0ms',
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
    },
    easing: {
      linear: 'linear',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },

  // ═══════════════════════════════════════════════════════════════════════
  // BREAKPOINTS
  // ═══════════════════════════════════════════════════════════════════════
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
};

// Tailwind CSS config extension
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: tokens.colors,
      fontFamily: tokens.typography.fontFamily,
      fontSize: tokens.typography.fontSize,
      spacing: tokens.spacing,
      borderRadius: tokens.borders.radius,
      boxShadow: tokens.shadows,
    },
  },
};
```

#### Clinical Component Examples

```typescript
// packages/design-system/components/clinical/PatientHeader.tsx
import React from 'react';
import { Badge } from '../primitives/Badge';
import { Avatar } from '../primitives/Avatar';
import { usePlugin } from '@/lib/plugins/PluginContext';
import { cn } from '@/lib/utils';

interface PatientHeaderProps {
  patient: {
    id: string;
    name: string;
    mrn: string;
    dateOfBirth: string;
    gender: string;
    photoUrl?: string;
  };
  admission: {
    id: string;
    status: 'active' | 'discharged';
    admitDate: string;
    location: string;
    attending: string;
  };
  // Specialty-specific fields loaded dynamically
  specialtyFields?: Record<string, any>;
  className?: string;
}

export function PatientHeader({
  patient,
  admission,
  specialtyFields,
  className,
}: PatientHeaderProps) {
  const { config, specialty } = usePlugin();

  // Get specialty-specific field configuration
  const primaryFields = config?.patientHeader?.primaryFields || ['name', 'mrn', 'age'];
  const secondaryFields = config?.patientHeader?.secondaryFields || [];

  const age = calculateAge(patient.dateOfBirth);

  // Map field names to values
  const fieldValues: Record<string, any> = {
    name: patient.name,
    mrn: patient.mrn,
    age: `${age}y`,
    gender: patient.gender,
    location: admission.location,
    attending: admission.attending,
    ...specialtyFields,
  };

  return (
    <header
      className={cn(
        'flex items-start gap-4 p-4 bg-white border-b',
        'dark:bg-neutral-900 dark:border-neutral-800',
        className
      )}
    >
      {/* Patient photo/avatar */}
      <Avatar
        src={patient.photoUrl}
        alt={patient.name}
        fallback={patient.name.charAt(0)}
        size="lg"
      />

      <div className="flex-1 min-w-0">
        {/* Primary info row */}
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-semibold text-neutral-900 dark:text-white truncate">
            {patient.name}
          </h1>
          <Badge variant={admission.status === 'active' ? 'success' : 'neutral'}>
            {admission.status}
          </Badge>
          {specialty && (
            <Badge
              variant="outline"
              style={{ borderColor: tokens.colors.specialty[specialty] }}
            >
              {config?.displayName}
            </Badge>
          )}
        </div>

        {/* Primary fields */}
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-neutral-600 dark:text-neutral-400">
          {primaryFields.map((field) => (
            <FieldDisplay
              key={field}
              field={field}
              value={fieldValues[field]}
              config={config?.fields?.[field]}
            />
          ))}
        </div>

        {/* Secondary fields (specialty-specific) */}
        {secondaryFields.length > 0 && (
          <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-sm">
            {secondaryFields.map((field) => (
              <FieldDisplay
                key={field}
                field={field}
                value={fieldValues[field]}
                config={config?.fields?.[field]}
                highlight
              />
            ))}
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm">
          Add Note
        </Button>
        <Button variant="outline" size="sm">
          View Chart
        </Button>
      </div>
    </header>
  );
}

function FieldDisplay({
  field,
  value,
  config,
  highlight = false
}: {
  field: string;
  value: any;
  config?: any;
  highlight?: boolean;
}) {
  const label = config?.label || formatFieldName(field);

  // Handle computed/formatted values
  let displayValue = value;
  if (config?.format) {
    displayValue = formatValue(value, config.format);
  }

  // Conditional styling (e.g., low ejection fraction)
  const isWarning = config?.warningThreshold && value < config.warningThreshold;

  return (
    <span className={cn(
      'inline-flex items-center gap-1',
      highlight && 'font-medium text-neutral-900 dark:text-white',
      isWarning && 'text-warning-600'
    )}>
      <span className="text-neutral-500">{label}:</span>
      <span>{displayValue ?? '—'}</span>
      {isWarning && <AlertIcon className="w-4 h-4" />}
    </span>
  );
}
```

```typescript
// packages/design-system/components/clinical/Timeline.tsx
import React, { useMemo } from 'react';
import { usePlugin } from '@/lib/plugins/PluginContext';
import { tokens } from '../../tokens';

interface TimelineEvent {
  id: string;
  type: string;
  category: string;
  timestamp: Date;
  title: string;
  description?: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  specialtyData?: Record<string, any>;
}

interface TimelineProps {
  events: TimelineEvent[];
  admitDate: Date;
  dischargeDate?: Date;
  projectedDischarge?: Date;
  // Trajectory points for the path
  trajectory?: Array<{ date: Date; location: string }>;
  onEventClick?: (event: TimelineEvent) => void;
}

export function Timeline({
  events,
  admitDate,
  dischargeDate,
  projectedDischarge,
  trajectory,
  onEventClick,
}: TimelineProps) {
  const { config, specialty } = usePlugin();

  // Get specialty-specific event categories and colors
  const eventCategories = useMemo(() => {
    const categories = config?.timeline?.eventCategories || [];
    return categories.reduce((acc, cat) => {
      acc[cat.id] = cat;
      return acc;
    }, {} as Record<string, any>);
  }, [config]);

  // Group events by date
  const eventsByDate = useMemo(() => {
    return events.reduce((acc, event) => {
      const dateKey = event.timestamp.toISOString().split('T')[0];
      if (!acc[dateKey]) acc[dateKey] = [];
      acc[dateKey].push(event);
      return acc;
    }, {} as Record<string, TimelineEvent[]>);
  }, [events]);

  // Calculate timeline bounds
  const timelineBounds = useMemo(() => {
    const end = dischargeDate || projectedDischarge || new Date();
    const totalDays = Math.ceil((end.getTime() - admitDate.getTime()) / (1000 * 60 * 60 * 24));
    return { start: admitDate, end, totalDays };
  }, [admitDate, dischargeDate, projectedDischarge]);

  return (
    <div className="relative w-full">
      {/* Timeline header with phases */}
      <TimelineHeader
        phases={config?.trajectory?.phases || []}
        bounds={timelineBounds}
      />

      {/* Main timeline area */}
      <div className="relative h-64 border rounded-lg bg-white dark:bg-neutral-900">
        {/* Grid lines */}
        <TimelineGrid bounds={timelineBounds} />

        {/* Trajectory path (stepped line showing location changes) */}
        {trajectory && (
          <TrajectoryPath
            points={trajectory}
            bounds={timelineBounds}
          />
        )}

        {/* Event markers */}
        <div className="absolute inset-0">
          {events.map((event) => (
            <EventMarker
              key={event.id}
              event={event}
              category={eventCategories[event.category]}
              bounds={timelineBounds}
              onClick={() => onEventClick?.(event)}
            />
          ))}
        </div>

        {/* Today indicator */}
        <TodayIndicator bounds={timelineBounds} />

        {/* Projected discharge indicator */}
        {projectedDischarge && !dischargeDate && (
          <ProjectedDischargeMarker
            date={projectedDischarge}
            bounds={timelineBounds}
          />
        )}
      </div>

      {/* Legend */}
      <TimelineLegend categories={Object.values(eventCategories)} />
    </div>
  );
}

function EventMarker({
  event,
  category,
  bounds,
  onClick
}: {
  event: TimelineEvent;
  category: any;
  bounds: any;
  onClick: () => void;
}) {
  // Calculate position based on timestamp
  const dayOffset = Math.floor(
    (event.timestamp.getTime() - bounds.start.getTime()) / (1000 * 60 * 60 * 24)
  );
  const leftPercent = (dayOffset / bounds.totalDays) * 100;

  const color = category?.color || tokens.colors.neutral[400];
  const Icon = category?.icon ? getIcon(category.icon) : CircleIcon;

  return (
    <button
      onClick={onClick}
      className={cn(
        'absolute transform -translate-x-1/2 -translate-y-1/2',
        'w-6 h-6 rounded-full flex items-center justify-center',
        'hover:scale-125 transition-transform cursor-pointer',
        'focus:outline-none focus:ring-2 focus:ring-offset-2'
      )}
      style={{
        left: `${leftPercent}%`,
        top: getEventYPosition(event.category),
        backgroundColor: color,
      }}
      title={event.title}
    >
      <Icon className="w-4 h-4 text-white" />
    </button>
  );
}
```

---

## Infrastructure & DevOps

### Kubernetes Architecture

```yaml
# infrastructure/k8s/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: flightplan
  labels:
    app.kubernetes.io/name: flightplan
---
# infrastructure/k8s/base/deployment-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flightplan-api
  namespace: flightplan
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flightplan-api
  template:
    metadata:
      labels:
        app: flightplan-api
    spec:
      containers:
        - name: api
          image: flightplan/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: flightplan-secrets
                  key: database-url
            - name: KAFKA_BROKERS
              value: "kafka.flightplan.svc.cluster.local:9092"
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
# infrastructure/k8s/base/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: flightplan-api-hpa
  namespace: flightplan
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: flightplan-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy FlightPlan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  API_IMAGE: ghcr.io/${{ github.repository }}/api
  FRONTEND_IMAGE: ghcr.io/${{ github.repository }}/frontend

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --tb=short

      - name: Run type checks
        run: |
          cd backend
          pip install mypy
          mypy app/

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.API_IMAGE }}:${{ github.sha }}
            ${{ env.API_IMAGE }}:latest

      - name: Build and push Frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.FRONTEND_IMAGE }}:${{ github.sha }}
            ${{ env.FRONTEND_IMAGE }}:latest

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Deploy to staging
        run: |
          kubectl set image deployment/flightplan-api \
            api=${{ env.API_IMAGE }}:${{ github.sha }} \
            -n flightplan-staging
          kubectl set image deployment/flightplan-frontend \
            frontend=${{ env.FRONTEND_IMAGE }}:${{ github.sha }} \
            -n flightplan-staging
          kubectl rollout status deployment/flightplan-api -n flightplan-staging
          kubectl rollout status deployment/flightplan-frontend -n flightplan-staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        run: |
          # Similar to staging, with production kubeconfig
          echo "Deploying to production..."
```

---

## Migration Strategy

### Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Migration Phases                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 0: Foundation (Current → +2 months)                                  │
│  ════════════════════════════════════════                                   │
│  □ Complete v3 rebuild (current work)                                       │
│  □ Achieve feature parity with legacy for cardiac specialty                 │
│  □ Production deployment of v3 for pilot site                               │
│  □ Legacy runs in parallel                                                  │
│                                                                              │
│  PHASE 1: Core Platform (+2 → +6 months)                                    │
│  ═════════════════════════════════════════                                  │
│  □ Implement event sourcing infrastructure                                  │
│  □ Build plugin system foundation                                           │
│  □ Extract cardiac-specific logic into first plugin                         │
│  □ Add multi-tenant support (single hospital initially)                     │
│  □ Build design system / component library                                  │
│                                                                              │
│  PHASE 2: Enterprise Features (+6 → +10 months)                             │
│  ═══════════════════════════════════════════════                            │
│  □ SSO integration (Azure AD, SAML)                                         │
│  □ Full audit trail from event store                                        │
│  □ Second specialty plugin (orthopedics)                                    │
│  □ EHR integration framework (HL7 FHIR)                                     │
│  □ Multi-tenant production deployment                                       │
│                                                                              │
│  PHASE 3: Scale & Expand (+10 → +18 months)                                 │
│  ════════════════════════════════════════════                               │
│  □ Additional specialty plugins                                             │
│  □ Reporting & analytics platform                                           │
│  □ Mobile companion app                                                     │
│  □ Customer self-service configuration                                      │
│  □ Marketplace for community plugins                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1 Detailed Tasks

#### 1.1 Event Sourcing Infrastructure

| Task | Description | Dependencies |
|------|-------------|--------------|
| Design event schema | Define core domain events, event store tables | None |
| Implement EventStore class | Append, load, snapshot operations | Schema |
| Build projection framework | Base classes, subscription management | EventStore |
| Migrate Admission to event-sourced | First aggregate migration | Projection framework |
| Add event replay capability | Rebuild read models from events | Projections |
| Performance testing | Ensure acceptable latency at scale | All above |

#### 1.2 Plugin System Foundation

| Task | Description | Dependencies |
|------|-------------|--------------|
| Define plugin manifest schema | YAML structure for specialty config | None |
| Build PluginRegistry | Discovery, loading, lifecycle | Manifest schema |
| Implement schema extensions | Dynamic JSONB fields per specialty | PluginRegistry |
| Create cardiac plugin | Extract existing cardiac logic | Extensions |
| Build frontend plugin context | React context for specialty config | Cardiac plugin |
| Dynamic component loading | Next.js dynamic imports for specialty UIs | Frontend context |

#### 1.3 Multi-Tenant Foundation

| Task | Description | Dependencies |
|------|-------------|--------------|
| Add tenant_id to all tables | Database schema update | None |
| Implement RLS policies | PostgreSQL row-level security | Schema update |
| Build TenantMiddleware | Tenant resolution from subdomain/header | RLS |
| Create tenant admin UI | Tenant CRUD, configuration | Middleware |
| Tenant-scoped testing | Ensure complete isolation | All above |

### Data Migration Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Data Migration Approach                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LEGACY DATABASE (SQL Server)          NEW DATABASE (PostgreSQL)            │
│  ┌─────────────────────────┐          ┌─────────────────────────┐           │
│  │ • patients              │          │ • patients              │           │
│  │ • admissions            │          │ • admissions            │           │
│  │ • clinical_events       │   ───►   │ • events (event store)  │           │
│  │ • locations             │          │ • projections           │           │
│  │ • procedures            │          │ • specialty_data (JSONB)│           │
│  └─────────────────────────┘          └─────────────────────────┘           │
│                                                                              │
│  Migration Script Flow:                                                      │
│  ─────────────────────────                                                  │
│  1. Export legacy data to staging tables                                    │
│  2. Transform to new schema (normalize, add UUIDs, encrypt PHI)             │
│  3. Generate synthetic events for existing state                            │
│  4. Load into event store                                                   │
│  5. Build projections (read models)                                         │
│  6. Validate: compare legacy queries vs new projections                     │
│  7. Run parallel for N days, compare results                                │
│  8. Cutover                                                                 │
│                                                                              │
│  Key Considerations:                                                         │
│  ───────────────────                                                        │
│  • PHI encryption with new keys                                             │
│  • MRN → UUID mapping table (encrypted)                                     │
│  • Preserve audit timestamps                                                │
│  • Handle legacy data quality issues                                        │
│  • Rollback plan if issues discovered                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Event sourcing complexity delays timeline | Medium | High | Start with hybrid: events for new data, existing CRUD for legacy |
| Plugin system over-engineered | Medium | Medium | Build minimum viable plugin for cardiac first, iterate |
| Multi-tenant RLS bugs expose PHI | Low | Critical | Extensive security testing, penetration testing, tenant isolation QA |
| Performance regression from event sourcing | Medium | High | Snapshots, CQRS with optimized read models, caching |
| Legacy migration data quality issues | High | Medium | Data profiling before migration, validation scripts, manual review |
| Team skill gaps (Kafka, event sourcing) | Medium | Medium | Training, start with simpler event bus (NATS), hire/consult |
| Scope creep from "enterprise" features | High | High | Strict phase gates, MVP for each phase, defer nice-to-haves |

---

## Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| TBD | PostgreSQL over SQL Server | Better JSONB support, RLS, open source, lower cost | SQL Server (legacy compatibility), MySQL |
| TBD | Event sourcing for clinical events | Audit trail, temporal queries, HIPAA compliance | Traditional CRUD with audit tables |
| TBD | Kafka for event bus | Industry standard, proven at scale, rich ecosystem | NATS (simpler), RabbitMQ, Redis Streams |
| TBD | Plugin architecture for specialties | Separation of concerns, independent deployment | Feature flags, monolithic with conditionals |
| TBD | Next.js for frontend | SSR, API routes, great DX, industry adoption | Remix, plain React SPA |
| TBD | Kubernetes for orchestration | Horizontal scaling, cloud-agnostic, industry standard | ECS, Cloud Run, VMs |

---

## Appendix

### A. Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Frontend | Next.js | 14.x | React framework with SSR |
| Frontend | TypeScript | 5.x | Type safety |
| Frontend | Tailwind CSS | 3.x | Styling |
| Frontend | shadcn/ui | latest | Component primitives |
| Backend | Python | 3.12 | Primary language |
| Backend | FastAPI | 0.109+ | API framework |
| Backend | SQLAlchemy | 2.0 | ORM |
| Backend | Pydantic | 2.x | Validation |
| Database | PostgreSQL | 16 | Primary datastore |
| Database | Redis | 7.x | Caching, sessions |
| Messaging | Kafka | 3.x | Event streaming |
| Search | Elasticsearch | 8.x | Full-text search |
| Auth | Keycloak | 23.x | Identity management |
| Infrastructure | Kubernetes | 1.29+ | Orchestration |
| Infrastructure | Terraform | 1.7+ | IaC |
| CI/CD | GitHub Actions | - | Automation |
| Monitoring | Prometheus + Grafana | - | Observability |

### B. File Structure (Target)

```
flightplan-enterprise/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database/
│   │   │       ├── session.py
│   │   │       └── tenant.py
│   │   ├── domain/
│   │   │   ├── events/
│   │   │   ├── aggregates/
│   │   │   └── services/
│   │   ├── infrastructure/
│   │   │   ├── event_store/
│   │   │   ├── projections/
│   │   │   └── integrations/
│   │   ├── models/
│   │   └── schemas/
│   ├── plugins/
│   │   ├── cardiac/
│   │   │   ├── manifest.yaml
│   │   │   ├── schema/
│   │   │   ├── workflows/
│   │   │   └── calculators/
│   │   └── orthopedics/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── primitives/
│   │   │   ├── clinical/
│   │   │   └── specialties/
│   │   ├── lib/
│   │   │   ├── plugins/
│   │   │   └── hooks/
│   │   └── types/
│   └── __tests__/
├── packages/
│   └── design-system/
│       ├── tokens/
│       └── components/
├── infrastructure/
│   ├── terraform/
│   ├── k8s/
│   └── docker/
├── docs/
└── scripts/
```

---

*Document Version: 1.0.0*
*Last Updated: 2025-01-01*
*Author: Architecture Team*
