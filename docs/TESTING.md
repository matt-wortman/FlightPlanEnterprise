# Testing Guide

**Last Updated:** 2026-01-02

Comprehensive testing strategy and guide for FlightPlan Enterprise.

---

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Pyramid](#test-pyramid)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Organization](#test-organization)
- [Testing Patterns](#testing-patterns)
- [CI/CD Integration](#cicd-integration)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)

---

## Testing Philosophy

### Core Principles

1. **Evidence-Based Development**: Follow the Three-Evidence Rule from CLAUDE.md
   - Contextual Evidence: Find 3 similar implementations before coding
   - Type Evidence: Run type-check after every 20 lines of code
   - Execution Evidence: Prove code works with actual test execution

2. **Test-First Mindset**: Write tests before or alongside implementation
   - Define expected behavior through tests
   - Use tests as executable specifications
   - Ensure all PHI-handling code is thoroughly tested

3. **Comprehensive Coverage**: Target 80%+ coverage for business logic
   - 100% coverage for PHI-handling code (HIPAA compliance requirement)
   - 100% coverage for event validation and business rules
   - Focus on critical paths and edge cases

4. **Fast Feedback**: Tests should be quick and reliable
   - Unit tests: < 1 second per test
   - Integration tests: < 5 seconds per test
   - Full test suite: < 2 minutes

### Testing Levels

| Level | Scope | Speed | Isolation | Example |
|-------|-------|-------|-----------|---------|
| Unit | Single function/class | Very Fast | High | Test EventStore.append() |
| Integration | Multiple components | Fast | Medium | Test API endpoint + EventStore |
| System | Full application | Slow | Low | Test full admission workflow |
| E2E | Browser + Backend | Very Slow | None | Test UI through patient journey |

---

## Test Pyramid

```
         /\
        /E2E\        <- 10% (Critical user journeys)
       /------\
      / System \     <- 20% (Key workflows)
     /----------\
    / Integration\   <- 30% (Component interactions)
   /--------------\
  /     Unit      \  <- 40% (Business logic, validation)
 /----------------\
```

### Distribution Strategy

- **40% Unit Tests**: Pure functions, domain logic, validators
- **30% Integration Tests**: API endpoints, event store, projections
- **20% System Tests**: Multi-component workflows
- **10% E2E Tests**: Critical paths only (admission, flightplan creation)

---

## Running Tests

### Backend (Python/pytest)

#### Quick Start
```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_event_store.py

# Run specific test
pytest tests/test_event_store.py::test_append_and_load_stream

# Run tests matching pattern
pytest -k "event_store"

# Run in verbose mode
pytest -v

# Run in parallel (faster)
pytest -n auto
```

#### Test Database Configuration

Tests use in-memory SQLite by default. For PostgreSQL testing:

```bash
# Set environment variable for PostgreSQL
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/flightplan_test"

# Run tests
pytest

# Run with specific database
TEST_DATABASE_URL="postgresql+asyncpg://..." pytest
```

#### Coverage Requirements

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

### Frontend (Jest/React Testing Library)

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- PatientList.test.tsx

# Run in watch mode
npm test -- --watch

# Update snapshots
npm test -- -u
```

### Type Checking (Mandatory Before Commit)

```bash
# Backend - Python type checking
cd backend
mypy app/ --strict

# Frontend - TypeScript type checking
cd frontend
npm run type-check
# or
npx tsc --noEmit
```

---

## Writing Tests

### Backend Test Structure

#### Basic Test Template

```python
import uuid
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.infrastructure.event_store import EventStore, EventToAppend

@pytest.mark.asyncio
async def test_feature_name():
    """Test description explaining what and why."""
    # Arrange
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()

    # Act
    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)
        result = await store.some_operation()
        await session.commit()

    # Assert
    assert result.expected_property == expected_value

    # Cleanup
    await engine.dispose()

def _create_test_engine():
    """Create test database engine (in-memory SQLite or PostgreSQL)."""
    url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_async_engine(url, future=True)
```

#### Testing API Endpoints

```python
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_session

@pytest.mark.asyncio
async def test_api_endpoint():
    """Test API endpoint with dependency override."""
    # Setup test database
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Override database dependency
    async def _override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    # Test API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/admissions", json={
            "admission_id": str(uuid.uuid4()),
            "patient_id": str(uuid.uuid4()),
            "specialty": "cardiac_surgery",
            "attending_id": str(uuid.uuid4()),
            "admit_date": "2025-01-01T10:00:00Z",
            "created_by": str(uuid.uuid4()),
        })

    # Cleanup
    app.dependency_overrides.clear()
    await engine.dispose()

    # Assert
    assert response.status_code == 200
    assert response.json()["new_version"] == 1
```

#### Testing Event Store

```python
@pytest.mark.asyncio
async def test_event_store_concurrency():
    """Test optimistic concurrency control."""
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()
    stream_id = uuid.uuid4()

    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)

        # First event succeeds
        await store.append(
            stream_id=stream_id,
            stream_type="Admission",
            events=[EventToAppend(
                event_type="admission.created",
                data={},
                metadata={},
                created_by=uuid.uuid4(),
            )],
        )
        await session.commit()

        # Second append with wrong expected version should fail
        with pytest.raises(ConcurrencyError):
            await store.append(
                stream_id=stream_id,
                stream_type="Admission",
                events=[EventToAppend(
                    event_type="admission.updated",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                )],
                expected_version=0,  # Wrong! Stream is at version 1
            )

    await engine.dispose()
```

#### Testing Projections

```python
from app.projections.admission_projection import AdmissionProjection
from app.models.read_models import AdmissionReadModel

@pytest.mark.asyncio
async def test_admission_projection():
    """Test that events correctly update read model."""
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()
    admission_id = uuid.uuid4()

    async with async_session() as session:
        projection = AdmissionProjection(session=session)

        # Project admission.created event
        event = {
            "tenant_id": str(tenant_id),
            "stream_id": str(admission_id),
            "event_type": "admission.created",
            "data": {
                "patient_id": str(uuid.uuid4()),
                "specialty": "cardiac_surgery",
                "admit_date": "2025-01-01T10:00:00Z",
            },
            "event_version": 1,
        }

        await projection.project(event)
        await session.commit()

        # Verify read model created
        result = await session.execute(
            select(AdmissionReadModel).where(
                AdmissionReadModel.id == admission_id
            )
        )
        read_model = result.scalar_one()
        assert read_model.data["specialty"] == "cardiac_surgery"

    await engine.dispose()
```

### Frontend Test Structure

#### Component Testing

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PatientList } from './PatientList';

describe('PatientList', () => {
  it('renders patient list correctly', async () => {
    const mockPatients = [
      { id: '123', name: 'John Doe', mrn: 'MRN001' },
    ];

    render(<PatientList patients={mockPatients} />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('handles patient selection', async () => {
    const onSelect = jest.fn();
    const mockPatients = [
      { id: '123', name: 'John Doe', mrn: 'MRN001' },
    ];

    render(<PatientList patients={mockPatients} onSelect={onSelect} />);

    fireEvent.click(screen.getByText('John Doe'));

    expect(onSelect).toHaveBeenCalledWith('123');
  });
});
```

---

## Test Organization

### Directory Structure

```
backend/tests/
├── test_api.py                  # API endpoint integration tests
├── test_commands_api.py         # Command endpoint tests
├── test_event_store.py          # Event store unit tests
├── test_event_store_extended.py # Additional event store tests
├── test_projections.py          # Projection tests
├── test_projections_extended.py # Extended projection tests
├── test_read_models_api.py      # Read model API tests
├── test_plugins.py              # Plugin system tests
├── test_lifespan.py             # Application lifecycle tests
└── test_runner.py               # Test utilities

frontend/__tests__/
├── components/
│   ├── PatientList.test.tsx
│   └── FlightPlanTimeline.test.tsx
├── hooks/
│   └── useAdmission.test.ts
└── utils/
    └── dateFormatters.test.ts
```

### Naming Conventions

- **Test files**: `test_<module>.py` or `<Component>.test.tsx`
- **Test functions**: `test_<action>_<expected_result>`
- **Fixtures**: `_create_<resource>()` or `<resource>_fixture()`

Examples:
```python
# Good
def test_append_events_succeeds_with_valid_data():
def test_load_stream_returns_empty_list_for_new_stream():
def test_concurrency_check_raises_error_on_version_mismatch():

# Bad
def test_1():
def test_events():
def test_stuff():
```

---

## Testing Patterns

### Pattern 1: Arrange-Act-Assert (AAA)

```python
async def test_feature():
    # Arrange - Setup test data and dependencies
    engine = _create_test_engine()
    # ... setup code

    # Act - Perform the operation being tested
    result = await some_operation()

    # Assert - Verify expected outcome
    assert result == expected

    # Cleanup (optional fourth step)
    await engine.dispose()
```

### Pattern 2: Given-When-Then (BDD Style)

```python
async def test_admission_location_change():
    """
    Given an admission with location ICU
    When location is changed to Floor
    Then trajectory shows movement from ICU to Floor
    """
    # Given
    admission = await create_admission(location="ICU")

    # When
    await change_location(admission.id, to_location="Floor")

    # Then
    trajectory = await get_trajectory(admission.id)
    assert trajectory[-1].location == "Floor"
```

### Pattern 3: Parameterized Tests

```python
import pytest

@pytest.mark.parametrize("specialty,expected_plugin", [
    ("cardiac_surgery", "CardiacSurgeryPlugin"),
    ("neurosurgery", "NeurosurgeryPlugin"),
    ("orthopedics", "OrthopedicsPlugin"),
])
async def test_plugin_loading(specialty, expected_plugin):
    plugin = plugin_registry.get_plugin(specialty)
    assert plugin.__class__.__name__ == expected_plugin
```

### Pattern 4: Fixtures for Reusable Setup

```python
import pytest

@pytest.fixture
async def test_engine():
    """Create and cleanup test database engine."""
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def event_store(test_engine):
    """Create EventStore with test session."""
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield EventStore(session=session, tenant_id=uuid.uuid4())

async def test_with_fixtures(event_store):
    """Test using fixtures."""
    result = await event_store.append(...)
    assert result > 0
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Type check
        run: |
          cd backend
          mypy app/ --strict

      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/postgres
        run: |
          cd backend
          pytest --cov=app --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Type check
        run: |
          cd frontend
          npm run type-check

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
```

---

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between
import uuid

class FlightPlanUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup test tenant and auth."""
        self.tenant_id = str(uuid.uuid4())
        self.headers = {
            "X-Tenant-ID": self.tenant_id,
        }

    @task(3)
    def create_admission(self):
        """Create admission (most common operation)."""
        self.client.post(
            "/api/v1/admissions",
            json={
                "admission_id": str(uuid.uuid4()),
                "patient_id": str(uuid.uuid4()),
                "specialty": "cardiac_surgery",
                "attending_id": str(uuid.uuid4()),
                "admit_date": "2025-01-01T10:00:00Z",
                "created_by": str(uuid.uuid4()),
            },
            headers=self.headers,
        )

    @task(1)
    def list_admissions(self):
        """List admissions (less frequent)."""
        self.client.get(
            "/api/v1/admissions",
            headers=self.headers,
        )
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

### Database Performance Testing

```python
@pytest.mark.performance
async def test_event_store_bulk_performance():
    """Verify event store can handle 1000 events/second."""
    import time

    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_id = uuid.uuid4()

    start = time.time()

    async with async_session() as session:
        store = EventStore(session=session, tenant_id=tenant_id)

        for i in range(1000):
            await store.append(
                stream_id=uuid.uuid4(),
                stream_type="Admission",
                events=[EventToAppend(
                    event_type="admission.created",
                    data={},
                    metadata={},
                    created_by=uuid.uuid4(),
                )],
            )

        await session.commit()

    elapsed = time.time() - start
    events_per_second = 1000 / elapsed

    assert events_per_second > 1000, f"Too slow: {events_per_second:.0f} events/sec"

    await engine.dispose()
```

---

## Security Testing

### PHI Security Tests (CRITICAL)

```python
@pytest.mark.security
async def test_mrn_not_in_urls():
    """CRITICAL: Verify MRN never appears in URL paths."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create patient with MRN
        patient_id = uuid.uuid4()
        mrn = "MRN12345"

        # Get patient endpoint should use UUID, not MRN
        response = await client.get(f"/api/v1/patients/{patient_id}")

        # Verify URL does not contain MRN
        assert mrn not in str(response.url)
        assert "MRN" not in str(response.url)

@pytest.mark.security
async def test_phi_encryption_at_rest():
    """Verify PHI is encrypted in database."""
    # TODO: Implement when encryption is added
    pass

@pytest.mark.security
async def test_tenant_isolation():
    """Verify tenant A cannot access tenant B's data."""
    engine = _create_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    admission_id = uuid.uuid4()

    # Create admission for tenant A
    async with async_session() as session:
        store_a = EventStore(session=session, tenant_id=tenant_a)
        await store_a.append(
            stream_id=admission_id,
            stream_type="Admission",
            events=[EventToAppend(
                event_type="admission.created",
                data={"secret": "tenant_a_data"},
                metadata={},
                created_by=uuid.uuid4(),
            )],
        )
        await session.commit()

    # Verify tenant B cannot see it
    async with async_session() as session:
        store_b = EventStore(session=session, tenant_id=tenant_b)
        events = await store_b.load_stream(admission_id)
        assert len(events) == 0, "Tenant isolation violated!"

    await engine.dispose()
```

---

## Best Practices

### DO's ✅

- **Write tests first or alongside code** (TDD/BDD)
- **Test one thing per test** (single responsibility)
- **Use descriptive test names** that explain what and why
- **Follow AAA pattern** (Arrange-Act-Assert)
- **Clean up resources** (dispose engines, clear overrides)
- **Use fixtures** for common setup
- **Test edge cases** (null, empty, boundary values)
- **Test error conditions** (concurrency, validation failures)
- **Mock external services** (APIs, third-party integrations)
- **Run type-check** before committing

### DON'Ts ❌

- **Don't test implementation details** (test behavior, not internals)
- **Don't use hard-coded IDs** (use uuid.uuid4())
- **Don't skip cleanup** (causes test pollution)
- **Don't test third-party code** (trust their tests)
- **Don't use production data** in tests
- **Don't share state** between tests
- **Don't use time.sleep()** (use proper async waits)
- **Don't ignore failing tests** (fix or remove)

### PHI Security Testing Rules

1. **NEVER** use real patient data in tests
2. **ALWAYS** verify MRN doesn't appear in URLs
3. **ALWAYS** test tenant isolation
4. **ALWAYS** verify access control
5. **ALWAYS** test encryption for PHI fields (when implemented)

---

## Troubleshooting

### Common Issues

#### Tests Fail with "Database locked"
```bash
# Solution: Use StaticPool for SQLite
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    poolclass=StaticPool,  # This fixes it
)
```

#### Tests Hang Indefinitely
```bash
# Solution: Ensure all async resources are cleaned up
await engine.dispose()
app.dependency_overrides.clear()
```

#### Import Errors
```bash
# Solution: Ensure PYTHONPATH includes app directory
cd backend
PYTHONPATH=. pytest
```

#### Type Check Failures
```bash
# Solution: Run mypy to see exact issues
mypy app/ --strict
```

---

## Summary

### Quick Reference

```bash
# Backend - Full test workflow
cd backend
mypy app/ --strict                    # Type check (mandatory)
pytest --cov=app --cov-fail-under=80  # Tests with coverage
pytest -n auto                        # Parallel execution (faster)

# Frontend - Full test workflow
cd frontend
npm run type-check                    # Type check (mandatory)
npm test -- --coverage                # Tests with coverage

# Both - Pre-commit checklist
mypy app/ --strict && pytest --cov=app --cov-fail-under=80
npm run type-check && npm test -- --coverage
```

### Coverage Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| PHI Handling | 100% | HIPAA compliance requirement |
| Event Validation | 100% | Business-critical |
| Business Logic | 90% | Core functionality |
| API Endpoints | 80% | Integration coverage |
| UI Components | 70% | User-facing quality |

---

**Related Documentation:**
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Database configuration for tests
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow
- [API.md](API.md) - API endpoint specifications
- [backend/README.md](../backend/README.md) - Backend setup guide

**Remember:** No code ships without tests. No exceptions.
