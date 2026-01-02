# Contributing to FlightPlan Enterprise

**Last Updated:** 2026-01-02

Welcome to FlightPlan Enterprise! This guide covers our development workflow, coding standards, and contribution process.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Branch Naming Conventions](#branch-naming-conventions)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Code Review Guidelines](#code-review-guidelines)
- [Security and PHI Requirements](#security-and-phi-requirements)
- [Documentation Standards](#documentation-standards)

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.12+** installed
- **Node.js 20+** installed (for frontend)
- **PostgreSQL 16+** installed (recommended) or SQLite for quick testing
- **Git** configured with your name and email
- Read [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md)
- Reviewed [CLAUDE.md](CLAUDE.md) for AI-assisted development guidelines

### Initial Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/FlightPlanEnterprise.git
cd FlightPlanEnterprise

# 2. Set up backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 3. Set up frontend (when ready)
cd ../frontend
npm install

# 4. Configure environment
cd ../backend
cp .env.example .env
# Edit .env with your database credentials

# 5. Run migrations
alembic upgrade head

# 6. Verify setup
pytest
mypy app/ --strict
```

### Development Tools

Install recommended tools:

```bash
# Backend code quality tools
pip install black ruff mypy pytest pytest-asyncio pytest-cov

# Pre-commit hooks (recommended)
pip install pre-commit
pre-commit install
```

---

## Development Workflow

### The Three-Evidence Rule (MANDATORY)

**Before submitting ANY code**, you MUST provide three types of evidence:

#### 1. Contextual Evidence (BEFORE writing code)
```bash
# Find 3 similar implementations in the codebase
grep -r "similar_pattern" backend/app/
cat backend/app/path/to/existing/implementation.py

# NEVER assume data formats - always FIND them in existing code
# Check event contracts, domain models, existing tests
```

#### 2. Type Evidence (WHILE writing code)
```bash
# After EVERY 20 lines of code:
mypy app/ --strict

# Fix ALL type errors before continuing
# No exceptions - type safety is critical for healthcare software
```

#### 3. Execution Evidence (AFTER writing code)
```bash
# Before claiming "done" - PROVE it works:
pytest tests/test_your_feature.py -v
# Paste the successful test output in your PR
```

### Feature Development Process

```
1. Create Issue → 2. Create Branch → 3. Implement → 4. Test → 5. PR → 6. Review → 7. Merge
```

#### Step 1: Create or Assign Issue

- Check existing issues before creating new ones
- Use issue templates for bugs and features
- Add appropriate labels: `backend`, `frontend`, `bug`, `enhancement`, `documentation`
- Assign yourself to the issue

#### Step 2: Create Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch (see naming conventions below)
git checkout -b feature/admission-location-tracking

# Or for bugs:
git checkout -b fix/event-store-concurrency-issue
```

#### Step 3: Implement with TDD

```bash
# 1. Write failing test first
cat > tests/test_location_tracking.py <<EOF
def test_location_change_creates_trajectory_point():
    # Test code here
    assert False  # Intentionally fail first
EOF

# 2. Run test (should fail)
pytest tests/test_location_tracking.py::test_location_change_creates_trajectory_point

# 3. Implement feature
# Edit app/domain/location_tracking.py

# 4. Run test again (should pass)
pytest tests/test_location_tracking.py::test_location_change_creates_trajectory_point

# 5. Type check
mypy app/domain/location_tracking.py --strict

# 6. Run full test suite
pytest

# 7. Commit
git add tests/test_location_tracking.py app/domain/location_tracking.py
git commit -m "feat(domain): add location tracking with trajectory points

- Implement LocationTracker service
- Add trajectory point creation
- Track location history for admissions

Tests: test_location_change_creates_trajectory_point
Closes #123"
```

#### Step 4: Comprehensive Testing

```bash
# Run all tests
pytest

# Check coverage (must be ≥80%)
pytest --cov=app --cov-report=html --cov-fail-under=80

# Type check (must pass with zero errors)
mypy app/ --strict

# Lint check
ruff check app/
black --check app/

# Fix linting issues
ruff check --fix app/
black app/
```

#### Step 5: Create Pull Request

```bash
# Push branch
git push -u origin feature/admission-location-tracking

# Create PR via GitHub UI or CLI
gh pr create --title "feat: add admission location tracking" \
  --body "## Summary
- Implements location tracking for admissions
- Adds trajectory point projection
- Updates read models for location history

## Test Plan
- ✅ Unit tests: test_location_tracking.py
- ✅ Integration tests: test_location_api.py
- ✅ Type check: mypy passes
- ✅ Coverage: 95% (exceeds 80% requirement)

## Breaking Changes
None

## Related Issues
Closes #123

## Screenshots
N/A (backend feature)"
```

---

## Code Standards

### Python Style Guide (Backend)

We follow **PEP 8** with these specific rules:

#### Formatting

```python
# Use Black formatter (line length: 88)
black app/

# Use Ruff for linting
ruff check app/
```

#### Type Hints (Required)

```python
# ✅ GOOD: Full type annotations
from typing import Optional
from uuid import UUID

async def get_admission(
    admission_id: UUID,
    session: AsyncSession,
    tenant_id: UUID,
) -> Optional[dict[str, Any]]:
    """Get admission by ID with full type safety."""
    result = await session.execute(
        select(AdmissionReadModel).where(
            AdmissionReadModel.id == admission_id
        )
    )
    return result.scalar_one_or_none()

# ❌ BAD: No type hints
async def get_admission(admission_id, session, tenant_id):
    result = await session.execute(...)
    return result.scalar_one_or_none()
```

#### Docstrings (Required for Public APIs)

```python
# ✅ GOOD: Google-style docstrings
def append_events(
    stream_id: UUID,
    events: list[EventToAppend],
    expected_version: Optional[int] = None,
) -> int:
    """Append events to a stream with optimistic concurrency control.

    Args:
        stream_id: Unique identifier for the event stream
        events: List of events to append
        expected_version: Expected current version (for concurrency check)

    Returns:
        New version number after append

    Raises:
        ConcurrencyError: If expected_version doesn't match current version
        ValueError: If events list is empty
    """
    pass

# ❌ BAD: No docstring or inadequate docstring
def append_events(stream_id, events, expected_version=None):
    """Appends events."""  # Too vague
    pass
```

#### Naming Conventions

```python
# Classes: PascalCase
class EventStore:
class AdmissionReadModel:

# Functions/Methods: snake_case
def append_events():
async def get_admission():

# Constants: UPPER_SNAKE_CASE
MAX_EVENTS_PER_BATCH = 1000
DEFAULT_TENANT_ID = uuid.UUID("...")

# Private members: prefix with _
class EventStore:
    def _validate_version(self):
        pass

# Type variables: PascalCase with _T suffix
from typing import TypeVar
T = TypeVar('T')
ModelT = TypeVar('ModelT', bound=BaseModel)
```

#### Import Organization

```python
# 1. Standard library
import os
import uuid
from datetime import datetime
from typing import Any, Optional

# 2. Third-party
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local imports (absolute)
from app.core.database import get_session
from app.core.tenant import get_tenant_id
from app.infrastructure.event_store import EventStore
from app.models.read_models import AdmissionReadModel
```

### TypeScript Style Guide (Frontend)

```typescript
// Use strict TypeScript
// tsconfig.json: "strict": true

// ✅ GOOD: Explicit types
interface Patient {
  id: string;
  name: string;
  mrn: string;  // PHI - handle carefully
  dateOfBirth: Date;
}

async function getPatient(patientId: string): Promise<Patient | null> {
  const response = await fetch(`/api/v1/patients/${patientId}`);
  if (!response.ok) return null;
  return response.json() as Promise<Patient>;
}

// ❌ BAD: 'any' types
async function getPatient(patientId: any): Promise<any> {
  const response = await fetch(`/api/v1/patients/${patientId}`);
  return response.json();
}
```

### SQL Style Guide

```sql
-- Use uppercase for keywords
SELECT
  id,
  stream_id,
  event_type,
  data
FROM event_store
WHERE tenant_id = :tenant_id
  AND stream_id = :stream_id
ORDER BY event_version ASC;

-- Indent for readability
CREATE TABLE read_model_admissions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  data JSONB NOT NULL,
  version INTEGER NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

---

## Testing Requirements

### Coverage Requirements

| Component | Minimum Coverage | Target |
|-----------|-----------------|--------|
| PHI Handling Code | 100% | 100% |
| Event Validation | 100% | 100% |
| Domain Logic | 80% | 90% |
| API Endpoints | 80% | 85% |
| Infrastructure | 70% | 80% |

### Test Structure

```python
# tests/test_feature.py
import uuid
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.base import Base
from app.infrastructure.event_store import EventStore

# Use descriptive test names
@pytest.mark.asyncio
async def test_append_events_succeeds_with_valid_data():
    """Test that valid events are successfully appended to stream."""
    # Arrange
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()
    stream_id = uuid.uuid4()

    # Act
    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        new_version = await store.append(
            stream_id=stream_id,
            stream_type="Admission",
            events=[...],
        )
        await session.commit()

    # Assert
    assert new_version == 1

    # Cleanup
    await engine.dispose()

def _create_test_engine():
    """Helper function for test database setup."""
    # Implementation here
    pass
```

### Running Tests Before PR

```bash
# Backend tests (MANDATORY)
cd backend
mypy app/ --strict                           # Must pass with 0 errors
pytest --cov=app --cov-fail-under=80         # Must achieve 80%+ coverage
ruff check app/                              # Must pass linting
black --check app/                           # Must pass formatting

# Frontend tests (when applicable)
cd frontend
npm run type-check                           # Must pass
npm test -- --coverage                       # Check coverage
npm run lint                                 # Must pass
```

---

## Pull Request Process

### PR Checklist

Before submitting, verify:

- [ ] **Three-Evidence Rule** satisfied:
  - [ ] Contextual evidence: Found 3 similar implementations
  - [ ] Type evidence: `mypy app/ --strict` passes
  - [ ] Execution evidence: Tests run and pass
- [ ] **Tests** written and passing
- [ ] **Coverage** ≥80% for new code
- [ ] **Type hints** added to all functions
- [ ] **Docstrings** added to public APIs
- [ ] **Security** review: No PHI in logs/URLs
- [ ] **Documentation** updated (if needed)
- [ ] **CHANGELOG.md** updated (for user-facing changes)
- [ ] **No breaking changes** (or clearly documented)
- [ ] **Branch up-to-date** with main

### PR Title Format

Use conventional commits format:

```
<type>(<scope>): <description>

Examples:
feat(api): add admission location change endpoint
fix(event-store): resolve concurrency check bug
docs(readme): update setup instructions
test(projections): add trajectory projection tests
refactor(domain): simplify admission state machine
chore(deps): update SQLAlchemy to 2.0.25
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

Scopes:
- `api`: API endpoints
- `event-store`: Event store infrastructure
- `domain`: Domain logic
- `projections`: Read model projections
- `plugins`: Plugin system
- `ui`: Frontend components
- `db`: Database/migrations

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Bullet list of specific changes
- Added X feature
- Fixed Y bug
- Refactored Z component

## Test Plan
- [ ] Unit tests: list test files
- [ ] Integration tests: describe scenarios
- [ ] Manual testing: steps performed
- [ ] Coverage: X% (exceeds 80% requirement)

## Breaking Changes
List any breaking changes or "None"

## Migration Required
Yes/No - If yes, describe migration steps

## Security Considerations
- PHI handling reviewed: Yes/No
- Tenant isolation verified: Yes/No
- Access control checked: Yes/No

## Screenshots
Add screenshots for UI changes

## Related Issues
Closes #123
Fixes #456
Related to #789

## Checklist
- [ ] Tests pass
- [ ] Type check passes
- [ ] Coverage ≥80%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### PR Size Guidelines

- **Small** (preferred): < 200 lines changed
- **Medium**: 200-500 lines changed
- **Large** (split if possible): 500-1000 lines changed
- **Extra Large** (must justify): > 1000 lines changed

Large PRs should be split into smaller, reviewable chunks when possible.

---

## Branch Naming Conventions

### Format

```
<type>/<short-description>
```

### Types

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring
- `chore/` - Maintenance tasks

### Examples

```bash
# Good branch names
feature/admission-location-tracking
fix/event-store-concurrency-race-condition
docs/update-api-documentation
test/add-projection-integration-tests
refactor/simplify-event-validation
chore/update-dependencies

# Bad branch names
my-feature        # No type prefix
feature-123       # Not descriptive
fix_bug           # Use hyphens, not underscores
FEATURE/NEW       # Use lowercase
```

### Branch Lifecycle

```bash
# Create branch from main
git checkout main
git pull origin main
git checkout -b feature/my-feature

# Regular commits during development
git add .
git commit -m "feat: implement X"

# Keep branch up-to-date
git checkout main
git pull origin main
git checkout feature/my-feature
git rebase main  # or: git merge main

# Push to remote
git push -u origin feature/my-feature

# After PR merge, delete branch
git checkout main
git pull origin main
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Example

```
feat(api): add patient location history endpoint

Implement GET /api/v1/patients/{id}/location-history endpoint
that returns the patient's location trajectory across all admissions.

- Add LocationHistoryService
- Create location_history projection
- Add API route with pagination support

Tests: test_location_history_api.py
Closes #234
```

### Rules

1. **Subject line**:
   - Use imperative mood ("add" not "added")
   - No period at the end
   - Maximum 50 characters
   - Start with lowercase (after type/scope)

2. **Body** (optional but recommended):
   - Wrap at 72 characters
   - Explain WHAT and WHY, not HOW
   - Separate from subject with blank line

3. **Footer**:
   - Reference issues: `Closes #123`, `Fixes #456`
   - Note breaking changes: `BREAKING CHANGE: describe change`

### Commit Types

Same as PR types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Refactoring
- `chore`: Maintenance
- `perf`: Performance
- `ci`: CI/CD

---

## Code Review Guidelines

### For Authors

**Before Requesting Review:**

1. Self-review your code
2. Run all tests and checks
3. Add clear PR description
4. Link related issues
5. Tag appropriate reviewers

**During Review:**

1. Respond to all comments
2. Mark conversations as resolved when addressed
3. Push new commits (don't force-push during review)
4. Request re-review after changes

### For Reviewers

**What to Check:**

1. **Correctness**: Does code do what it claims?
2. **Tests**: Are there sufficient tests?
3. **Security**: Any PHI leaks or security issues?
4. **Performance**: Any obvious bottlenecks?
5. **Maintainability**: Is code readable and well-structured?
6. **Documentation**: Are changes documented?
7. **Type Safety**: Are types correct and complete?

**Review Etiquette:**

- Be respectful and constructive
- Explain WHY for requests
- Approve minor issues (use "nit:" prefix)
- Block on security/correctness issues
- Suggest alternatives, don't demand
- Acknowledge good code

**Comment Prefixes:**

- `nit:` - Minor issue, non-blocking
- `question:` - Asking for clarification
- `suggestion:` - Alternative approach
- `blocker:` - Must be fixed before merge
- `security:` - Security concern (always blocker)
- `phi:` - PHI handling issue (always blocker)

**Example Comments:**

```
✅ GOOD:
"nit: Consider extracting this logic into a helper function for reusability.
Not blocking, but would improve maintainability."

"blocker: This query doesn't filter by tenant_id, which violates tenant isolation.
Please add tenant_id to the WHERE clause."

"Great use of type hints here! Makes the code much clearer."

❌ BAD:
"This is wrong."  # Not specific or constructive

"Why didn't you do X?"  # Confrontational

"Change this."  # No explanation
```

### Approval Requirements

- **1 approval required** for most PRs
- **2 approvals required** for:
  - Database migrations
  - Security-related changes
  - Breaking changes
  - Infrastructure changes

---

## Security and PHI Requirements

### PHI Security Rules (CRITICAL)

**NEVER:**
- ❌ Expose MRN or patient names in URLs
- ❌ Log PHI to console or files
- ❌ Store PHI in browser localStorage
- ❌ Include PHI in error messages
- ❌ Commit PHI test data to repository

**ALWAYS:**
- ✅ Use UUIDs in URLs (not MRNs)
- ✅ Filter PHI from logs
- ✅ Encrypt PHI at rest (when implemented)
- ✅ Test tenant isolation
- ✅ Use generated test data only

### Security Checklist for PRs

- [ ] No PHI in URLs or query parameters
- [ ] No PHI in log statements
- [ ] Tenant isolation verified
- [ ] Access control checked
- [ ] SQL injection prevention (use parameterized queries)
- [ ] Input validation on all endpoints
- [ ] No secrets in code (use environment variables)

### Example: Secure vs Insecure

```python
# ❌ INSECURE: PHI in URL
@router.get("/patients/{mrn}")  # MRN is PHI!
async def get_patient_by_mrn(mrn: str):
    logger.info(f"Fetching patient: {mrn}")  # PHI in logs!
    pass

# ✅ SECURE: UUID in URL
@router.get("/patients/{patient_id}")
async def get_patient(patient_id: UUID):
    logger.info(f"Fetching patient: {patient_id}")  # UUID is safe
    # MRN can be in response body, but NOT in URL
    pass

# ❌ INSECURE: Missing tenant isolation
@router.get("/admissions/{admission_id}")
async def get_admission(admission_id: UUID, session: AsyncSession):
    result = await session.execute(
        select(AdmissionReadModel).where(
            AdmissionReadModel.id == admission_id
        )
        # Missing tenant_id filter!
    )
    return result.scalar_one_or_none()

# ✅ SECURE: Tenant isolation enforced
@router.get("/admissions/{admission_id}")
async def get_admission(
    admission_id: UUID,
    session: AsyncSession,
    tenant_id: UUID = Depends(get_tenant_id),
):
    result = await session.execute(
        select(AdmissionReadModel).where(
            AdmissionReadModel.tenant_id == tenant_id,  # Tenant isolation
            AdmissionReadModel.id == admission_id,
        )
    )
    return result.scalar_one_or_none()
```

---

## Documentation Standards

### When to Update Documentation

Update docs when:
- Adding new features
- Changing APIs
- Modifying setup process
- Adding dependencies
- Changing architecture

### Documentation Files

- **README.md**: Project overview, quick start
- **CONTRIBUTING.md**: This file (development workflow)
- **docs/API.md**: API endpoint documentation
- **docs/TESTING.md**: Testing guide
- **docs/DATABASE_SETUP.md**: Database setup
- **backend/docs/**: Backend-specific docs
- **CHANGELOG.md**: User-facing changes

### Code Documentation

```python
# Module docstring
"""Patient domain models and business logic.

This module contains the core patient entity and related value objects.
It implements the patient aggregate root for the domain model.
"""

# Class docstring
class Patient:
    """Patient aggregate root.

    Represents a patient in the FlightPlan system with demographics,
    identifiers, and admission history.

    Attributes:
        id: Unique patient identifier (UUID)
        mrn: Medical record number (PHI - handle carefully)
        name: Patient full name (PHI)
        date_of_birth: Patient DOB (PHI)
    """

# Function docstring
def calculate_age(date_of_birth: date) -> int:
    """Calculate patient age in years.

    Args:
        date_of_birth: Patient's date of birth

    Returns:
        Age in complete years

    Raises:
        ValueError: If date_of_birth is in the future
    """
```

---

## Quick Reference

### Pre-Commit Checklist

```bash
# Run before EVERY commit
cd backend

# 1. Type check (MANDATORY - must pass)
mypy app/ --strict

# 2. Run tests (MANDATORY - must pass)
pytest

# 3. Check coverage (MANDATORY - must be ≥80%)
pytest --cov=app --cov-fail-under=80

# 4. Lint check
ruff check app/

# 5. Format check
black --check app/

# If checks 4-5 fail, auto-fix:
ruff check --fix app/
black app/
```

### Common Commands

```bash
# Create feature branch
git checkout -b feature/my-feature

# Run tests with coverage
pytest --cov=app --cov-report=html

# Type check
mypy app/ --strict

# Format code
black app/
ruff check --fix app/

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Push branch
git push -u origin feature/my-feature

# Create PR
gh pr create
```

---

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an Issue with `bug` label
- **Feature Requests**: Create an Issue with `enhancement` label
- **Documentation Issues**: Create an Issue with `documentation` label
- **Security Issues**: Email security@flightplan.example.com (DO NOT create public issue)

---

**Thank you for contributing to FlightPlan Enterprise!**

Your contributions help improve patient care and clinical workflows.

---

**Related Documentation:**
- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [docs/TESTING.md](docs/TESTING.md) - Testing guide
- [docs/API.md](docs/API.md) - API documentation
- [CLAUDE.md](CLAUDE.md) - AI-assisted development guidelines
