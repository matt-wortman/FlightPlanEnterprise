# FlightPlan Enterprise - Quick Start Guide

**Get running in 5 minutes**

This guide gets you from zero to a working local development environment as quickly as possible.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.12+** installed (`python --version`)
- [ ] **PostgreSQL 16** installed and running (or use SQLite for quick testing)
- [ ] **Git** installed
- [ ] **Code editor** (VS Code, PyCharm, etc.)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd FlightPlanEnterprise
```

## Step 2: Backend Setup (3 minutes)

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (this may take 1-2 minutes)
pip install -r requirements.txt
```

## Step 3: Database Setup (1 minute)

### Option A: SQLite (Fastest - No Setup)

```bash
# Create .env.local file
cat > .env.local << EOF
DATABASE_URL=sqlite+aiosqlite:///./flightplan_dev.db
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000000
PLUGINS_DIR=plugins
EOF

# Run migrations
alembic upgrade head
```

### Option B: PostgreSQL (Recommended for Real Development)

```bash
# Create database (assumes PostgreSQL is running)
createdb flightplan_dev

# Create .env.local file
cat > .env.local << EOF
DATABASE_URL=postgresql+asyncpg://localhost/flightplan_dev
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000000
PLUGINS_DIR=plugins
EOF

# Run migrations
alembic upgrade head
```

## Step 4: Start the Server (30 seconds)

```bash
# From backend/ directory
uvicorn app.main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 5: Verify It Works

Open your browser and visit:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see the interactive API documentation (Swagger UI).

## Quick Test: Create an Admission

### Using the API Docs (Easy)

1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/admissions`
3. Click "Try it out"
4. Replace the request body with:

```json
{
  "admission_id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "223e4567-e89b-12d3-a456-426614174000",
  "specialty": "cardiac",
  "attending_id": "323e4567-e89b-12d3-a456-426614174000",
  "admit_date": "2026-01-02T10:00:00Z",
  "chief_complaint": "Chest pain",
  "admission_type": "emergency",
  "created_by": "423e4567-e89b-12d3-a456-426614174000"
}
```

5. Click "Execute"
6. You should get a `200` response with `{"new_version": 1}`

### Using curl (Command Line)

```bash
curl -X POST http://localhost:8000/api/v1/admissions \
  -H "Content-Type: application/json" \
  -d '{
    "admission_id": "123e4567-e89b-12d3-a456-426614174000",
    "patient_id": "223e4567-e89b-12d3-a456-426614174000",
    "specialty": "cardiac",
    "attending_id": "323e4567-e89b-12d3-a456-426614174000",
    "admit_date": "2026-01-02T10:00:00Z",
    "chief_complaint": "Chest pain",
    "admission_type": "emergency",
    "created_by": "423e4567-e89b-12d3-a456-426614174000"
  }'
```

## Optional: Seed Synthetic Data (Recommended for UI Work)

If you want a small, **fully synthetic** dataset (no legacy data), run:

```bash
# From backend/ directory with .env.local configured
source .venv/bin/activate
python scripts/seed_fake_data.py --patients 25
```

This will create about 20–30 synthetic patients with admissions, locations, timeline events, and attachments.

To create multiple admissions per patient:

```bash
python scripts/seed_fake_data.py --patients 20 --admissions-per-patient 2
```

## Running Tests

```bash
# From backend/ directory
pytest

# Expected output: All tests should pass
# ===== X passed in Y.XXs =====
```

## What's Next?

Now that you have a working environment, here's what to explore:

### For New Developers
1. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development workflow and coding standards
2. **[backend/README.md](backend/README.md)** - Detailed backend documentation
3. **[docs/API.md](docs/API.md)** - Complete API reference

### Understand the Domain
1. **[legacy-reference/core/FpCodes.py](legacy-reference/core/FpCodes.py)** - Domain vocabulary and enums
2. **[docs/domain/FLIGHTPLAN_REFACTOR_REPORT_FOR_CLINICIANS.md](docs/domain/FLIGHTPLAN_REFACTOR_REPORT_FOR_CLINICIANS.md)** - What the app does (non-technical)

### Architecture & Design
1. **[docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md](docs/architecture/ENTERPRISE_ARCHITECTURE_PLAN.md)** - Full enterprise vision
2. **[docs/architecture/TECHNICAL_ARCHITECTURE.md](docs/architecture/TECHNICAL_ARCHITECTURE.md)** - Current implementation details

## Common Issues

### "Command not found: python"

Try `python3` instead of `python`:
```bash
python3 -m venv .venv
```

### "ModuleNotFoundError"

Make sure your virtual environment is activated:
```bash
source .venv/bin/activate  # You should see (.venv) in your prompt
```

### "Database connection failed"

**For PostgreSQL:**
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT version();"

# If not running, start it (macOS with Homebrew):
brew services start postgresql

# Linux:
sudo systemctl start postgresql
```

**For SQLite:** No setup needed - just make sure your `.env.local` has the SQLite URL.

### Port 8000 already in use

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Migrations fail

```bash
# Reset and reapply migrations
alembic downgrade base
alembic upgrade head

# If that doesn't work, drop and recreate database
# PostgreSQL:
dropdb flightplan_dev && createdb flightplan_dev && alembic upgrade head

# SQLite:
rm flightplan_dev.db && alembic upgrade head
```

## Development Tools

### Recommended VS Code Extensions

- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **REST Client** or **Thunder Client** - Test APIs
- **SQLite Viewer** - View SQLite databases
- **PostgreSQL** - Manage PostgreSQL

### Type Checking

```bash
# Run mypy for type checking
mypy app/
```

### View Database

**SQLite:**
```bash
# Use sqlite3 command
sqlite3 flightplan_dev.db
# Then run SQL: SELECT * FROM events;
```

**PostgreSQL:**
```bash
# Use psql
psql flightplan_dev
# Then run SQL: SELECT * FROM events;
```

## Quick Reference Commands

```bash
# Start server
uvicorn app.main:app --reload

# Run tests
pytest

# Type check
mypy app/

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration status
alembic current

# View available API endpoints
# Visit: http://localhost:8000/docs
```

## Project Structure Overview

```
FlightPlanEnterprise/
├── backend/              # ← You're here (FastAPI app)
│   ├── app/
│   │   ├── api/routes/   # API endpoints
│   │   ├── core/         # Config, database
│   │   ├── infrastructure/ # Event store
│   │   ├── models/       # Database models
│   │   └── projections/  # Read model builders
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   └── .env.local        # Your local config (not committed)
│
├── docs/                 # Documentation
└── legacy-reference/     # Old codebase (reference only)
```

## Need Help?

- **Documentation**: Check [README.md](README.md) for comprehensive overview
- **API Questions**: See [docs/API.md](docs/API.md)
- **Database Questions**: See [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md)
- **Testing Questions**: See [docs/TESTING.md](docs/TESTING.md)

---

**Congratulations! You're ready to start developing.** 🎉

Next step: Read [CONTRIBUTING.md](CONTRIBUTING.md) to understand the development workflow.
