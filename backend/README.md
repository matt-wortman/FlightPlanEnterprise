# FlightPlan Enterprise Backend

**Last Updated:** January 2, 2026

Event-sourced, multi-tenant FastAPI backend for the FlightPlan Enterprise clinical care platform.

## Architecture

This backend implements:
- **Event Sourcing** - All state changes captured as immutable events
- **CQRS** - Command/Query Responsibility Segregation with read model projections
- **Multi-Tenancy** - Hospital/organization-level data isolation
- **Plugin System** - Specialty-specific clinical workflows (cardiac, orthopedic, etc.)

## Prerequisites

- **Python 3.12+** - Required for modern async features
- **PostgreSQL 16** - Production database (or SQLite for development/testing)
- **pip** - Python package manager

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env.local

# Edit .env.local with your database URL
# For PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:pass@localhost/flightplan_dev
# For SQLite (dev): DATABASE_URL=sqlite+aiosqlite:///./flightplan_dev.db

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

**API Server:** http://localhost:8000
**API Documentation:** http://localhost:8000/docs
**Health Check:** http://localhost:8000/health

## Dependencies

Current package versions from `requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| **fastapi** | 0.127.0 | Modern async web framework |
| **uvicorn[standard]** | 0.40.0 | ASGI server with WebSocket support |
| **sqlalchemy** | 2.0.45 | ORM with async support |
| **asyncpg** | 0.31.0 | PostgreSQL async driver |
| **aiosqlite** | 0.22.1 | SQLite async driver (dev/test) |
| **alembic** | 1.17.2 | Database migration tool |
| **pydantic** | 2.12.5 | Data validation and settings |
| **pydantic-settings** | 2.12.0 | Environment variable management |
| **python-dotenv** | 1.2.1 | .env file loading |
| **pyyaml** | 6.0.3 | YAML parsing (for plugin manifests) |
| **pytest** | 9.0.2 | Testing framework |
| **pytest-asyncio** | 1.3.0 | Async test support |
| **httpx** | 0.28.1 | HTTP client for testing API |
| **mypy** | 1.19.1 | Static type checker |
| **types-PyYAML** | 6.0.12.20250915 | Type stubs for PyYAML |

## Environment Configuration

Create `.env.local` in the `backend/` directory:

```bash
# Database Configuration
# PostgreSQL (production/staging):
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/flightplan_dev

# SQLite (local development):
# DATABASE_URL=sqlite+aiosqlite:///./flightplan_dev.db

# Tenant Configuration
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000000

# Plugin Configuration
PLUGINS_DIR=plugins

# Optional: Override for testing
# TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/flightplan_test
```

## Database Migrations

Alembic manages all schema changes. **Never manually modify the database schema.**

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to specific revision
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# View current migration status
alembic current

# View migration history
alembic history
```

### Current Migrations

1. **001_event_store** - Core event sourcing tables (events, snapshots, subscriptions)
2. **002_read_models_and_tenants** - Read models and tenant management

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (for manual edits)
alembic revision -m "description of changes"

# ALWAYS review auto-generated migrations before applying!
```

## Running the Application

### Development Server

```bash
# Standard development server (auto-reload on code changes)
uvicorn app.main:app --reload

# Specify custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# With increased log verbosity
uvicorn app.main:app --reload --log-level debug
```

### Production Server

```bash
# Single worker (not recommended for production)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Multiple workers (recommended)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn (production-ready)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Running Projections

Projections build read models from events. In production, run as a separate service:

```bash
# Development mode
python -m app.projections.run

# Production (with supervisord, systemd, or Docker)
# See deployment documentation
```

## API Endpoints

### Health & Status

- `GET /health` - Health check endpoint

### Commands (Write Operations)

- `POST /api/v1/admissions` - Create new admission
- `POST /api/v1/admissions/{id}/location` - Change patient location
- `POST /api/v1/clinical-events` - Record clinical event

### Queries (Read Operations)

- `GET /api/v1/patients` - List patients (with pagination)
- `GET /api/v1/patients/{id}` - Get patient details
- `GET /api/v1/admissions` - List admissions (optionally filter by patient)
- `GET /api/v1/flightplans/{id}` - Get flight plan details
- `GET /api/v1/admissions/{id}/timeline` - Get admission timeline
- `GET /api/v1/admissions/{id}/trajectory` - Get patient location trajectory

### Events (Low-level)

- `POST /api/v1/events` - Append events directly to event store

### Plugins

- `GET /api/v1/specialties` - List available specialties
- `GET /api/v1/specialties/{name}/config` - Get specialty configuration

See [/docs/API.md](/docs/API.md) for complete API documentation.

## Testing

### Run All Tests

```bash
# Run all tests (uses SQLite in-memory by default)
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/
# Open htmlcov/index.html in browser
```

### Run Specific Tests

```bash
# Single test file
pytest tests/test_event_store.py

# Single test function
pytest tests/test_event_store.py::test_append_events

# Tests matching pattern
pytest -k "event_store"
```

### Test with PostgreSQL

By default, tests use SQLite in-memory databases for speed. To test with PostgreSQL:

```bash
# Set environment variable
TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/flightplan_test pytest

# Or create .env.test
echo "TEST_DATABASE_URL=postgresql+asyncpg://localhost/flightplan_test" > .env.test
pytest
```

### Test Files

- `test_api.py` - API endpoint integration tests
- `test_event_store.py` - Event sourcing infrastructure tests
- `test_projections.py` - Read model projection tests
- `test_plugins.py` - Plugin system tests
- `test_lifespan.py` - Application lifecycle tests

See [/docs/TESTING.md](/docs/TESTING.md) for comprehensive testing documentation.

## Type Checking

This project uses **mypy** for static type analysis. Type checking is **required** before committing code.

```bash
# Type check entire app
mypy app/

# Strict mode (recommended)
mypy app/ --strict

# Check specific file
mypy app/infrastructure/event_store.py

# Ignore warnings (not recommended)
mypy app/ --no-warn-unused-ignores
```

**Best Practice:** Run `mypy` after every 20 lines of code you write.

## Code Formatting & Linting

```bash
# Format code with black (if configured)
black app/ tests/

# Check code style with flake8 (if configured)
flake8 app/ tests/

# Sort imports with isort (if configured)
isort app/ tests/
```

## Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   │   ├── 001_event_store.py
│   │   └── 002_read_models_and_tenants.py
│   └── env.py                  # Alembic configuration
│
├── app/
│   ├── api/                    # API layer
│   │   └── routes/             # API route handlers
│   │       ├── commands.py     # Write operations
│   │       ├── events.py       # Event store access
│   │       ├── health.py       # Health check
│   │       ├── plugins.py      # Plugin management
│   │       └── read_models.py  # Query operations
│   │
│   ├── core/                   # Core infrastructure
│   │   ├── config.py           # Application settings
│   │   ├── database.py         # Database session management
│   │   └── tenant.py           # Multi-tenancy support
│   │
│   ├── infrastructure/         # Event sourcing infrastructure
│   │   ├── event_store.py      # Event store implementation
│   │   └── plugins.py          # Plugin loader
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── events.py           # Event store tables
│   │   ├── read_models.py      # Read model tables
│   │   ├── tenants.py          # Tenant management
│   │   └── types.py            # Custom column types (GUID)
│   │
│   ├── projections/            # Read model projections
│   │   ├── admission.py        # Admission read model builder
│   │   ├── base.py             # Base projection class
│   │   ├── patient.py          # Patient read model builder
│   │   ├── run.py              # Projection runner (subscription)
│   │   └── timeline.py         # Timeline/trajectory builders
│   │
│   └── main.py                 # FastAPI application entry point
│
├── docs/                       # Backend-specific documentation
│   └── event_contracts_v1.md   # Event schema definitions
│
├── plugins/                    # Specialty plugins
│   └── cardiac/                # Cardiac surgery specialty
│       └── manifest.yaml       # Plugin configuration
│
├── tests/                      # Test suite
│   ├── test_api.py
│   ├── test_event_store.py
│   ├── test_lifespan.py
│   ├── test_plugins.py
│   └── test_projections.py
│
├── .env.example                # Example environment variables
├── .env.local                  # Local environment (not committed)
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Python project metadata
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Plugin System

Plugins enable specialty-specific workflows without modifying core code.

### Plugin Directory Structure

```
plugins/
└── cardiac/
    ├── manifest.yaml           # Plugin metadata
    ├── procedures.yaml         # Procedure definitions (optional)
    ├── risk_models.yaml        # Risk assessment models (optional)
    └── ui_config.yaml          # Frontend configuration (optional)
```

### Loading Plugins

Plugins are auto-discovered from `PLUGINS_DIR` (default: `plugins/`) at application startup.

```python
# Plugins are loaded via app lifespan
# See app/main.py and app/infrastructure/plugins.py
```

### Creating a Plugin

See [/docs/PLUGIN_DEVELOPMENT.md](/docs/PLUGIN_DEVELOPMENT.md) for detailed plugin development guide.

## Troubleshooting

### Database Connection Issues

```bash
# Verify PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Check database exists
psql -U postgres -l | grep flightplan

# Create database if missing
createdb flightplan_dev
```

### Migration Errors

```bash
# Reset database (WARNING: destroys all data)
alembic downgrade base
alembic upgrade head

# Or drop and recreate database
dropdb flightplan_dev
createdb flightplan_dev
alembic upgrade head
```

### Import Errors

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Verify dependencies installed
pip list

# Reinstall if needed
pip install -r requirements.txt
```

### Type Errors

```bash
# Common mypy issues:
# - Missing type hints: Add return types and parameter types
# - Untyped imports: Install type stubs (types-*)
# - Async confusion: Use AsyncSession, not Session
```

## Development Workflow

1. **Create feature branch** - `git checkout -b feature/my-feature`
2. **Write tests first** - TDD approach preferred
3. **Implement feature** - Follow existing patterns
4. **Run type check** - `mypy app/` (after every 20 lines)
5. **Run tests** - `pytest -v`
6. **Update migrations** - `alembic revision --autogenerate -m "description"`
7. **Test migration** - `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
8. **Commit changes** - Follow conventional commit format
9. **Create PR** - See [/CONTRIBUTING.md](/CONTRIBUTING.md)

## Additional Resources

- **Event Contracts**: [docs/event_contracts_v1.md](docs/event_contracts_v1.md)
- **API Documentation**: [/docs/API.md](/docs/API.md)
- **Database Setup**: [/docs/DATABASE_SETUP.md](/docs/DATABASE_SETUP.md)
- **Testing Guide**: [/docs/TESTING.md](/docs/TESTING.md)
- **Plugin Development**: [/docs/PLUGIN_DEVELOPMENT.md](/docs/PLUGIN_DEVELOPMENT.md)
- **Architecture Overview**: [/docs/architecture/TECHNICAL_ARCHITECTURE.md](/docs/architecture/TECHNICAL_ARCHITECTURE.md)

## Security Notes

### PHI Compliance

This application handles **Protected Health Information (PHI)**. Critical security requirements:

- **Never log PHI** - No MRN, patient names, or identifying information in logs
- **Never expose PHI in URLs** - Use opaque UUIDs, not MRN or patient names
- **Encrypt PHI at rest** - All PHI fields must be encrypted in database
- **Use HTTPS in production** - TLS required for all API communication
- **Audit all access** - Event store provides complete audit trail

### Database Security

- Use **strong passwords** for database credentials
- **Never commit** `.env.local` or credentials to git
- Use **connection pooling** with appropriate limits
- Enable **row-level security** for tenant isolation in production

---

**For detailed architecture and design decisions**, see the main [/README.md](/README.md) and [/docs/architecture/](/docs/architecture/) directory.
