# Database Setup Guide

**Last Updated:** 2026-01-02

Complete guide to database setup, migrations, and management for FlightPlan Enterprise.

---

## Table of Contents

- [Overview](#overview)
- [Database Requirements](#database-requirements)
- [PostgreSQL Installation](#postgresql-installation)
- [Development Database Setup](#development-database-setup)
- [Production Database Setup](#production-database-setup)
- [Database Migrations](#database-migrations)
- [Schema Overview](#schema-overview)
- [Database Operations](#database-operations)
- [Backup and Restore](#backup-and-restore)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

---

## Overview

FlightPlan Enterprise uses:
- **PostgreSQL 16+** for production (required for HIPAA compliance, performance, and multi-tenancy)
- **SQLite** for development/testing (optional, not recommended for production)

### Why PostgreSQL?

1. **HIPAA Compliance**: Robust encryption, audit logging, and access controls
2. **Performance**: Advanced indexing, query optimization, and connection pooling
3. **Multi-Tenancy**: Row-level security (RLS) for tenant isolation
4. **Event Sourcing**: JSONB support for efficient event storage
5. **Reliability**: ACID compliance, point-in-time recovery

---

## Database Requirements

### Minimum Requirements

| Environment | PostgreSQL Version | RAM | Storage | CPU |
|-------------|-------------------|-----|---------|-----|
| Development | 14+ | 4 GB | 20 GB | 2 cores |
| Staging | 16+ | 8 GB | 100 GB | 4 cores |
| Production | 16+ | 16 GB | 500 GB+ | 8 cores |

### Required Extensions

```sql
-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- JSONB operations (installed by default in PG 14+)
-- No extension needed - built-in

-- Full-text search (future)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Audit logging (future)
CREATE EXTENSION IF NOT EXISTS "pgaudit";
```

---

## PostgreSQL Installation

### macOS (Homebrew)

```bash
# Install PostgreSQL 16
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16

# Verify installation
psql --version
# Expected: psql (PostgreSQL) 16.x

# Create user and database
psql postgres
```

```sql
-- Create flightplan user
CREATE USER flightplan WITH PASSWORD 'your_secure_password';

-- Create development database
CREATE DATABASE flightplan_dev OWNER flightplan;

-- Create test database
CREATE DATABASE flightplan_test OWNER flightplan;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE flightplan_dev TO flightplan;
GRANT ALL PRIVILEGES ON DATABASE flightplan_test TO flightplan;

\q
```

### Linux (Ubuntu/Debian)

```bash
# Add PostgreSQL apt repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Import repository signing key
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Update package lists
sudo apt update

# Install PostgreSQL 16
sudo apt install postgresql-16 postgresql-contrib-16

# Verify installation
psql --version

# Switch to postgres user
sudo -u postgres psql
```

```sql
-- Create flightplan user
CREATE USER flightplan WITH PASSWORD 'your_secure_password';

-- Create databases
CREATE DATABASE flightplan_dev OWNER flightplan;
CREATE DATABASE flightplan_test OWNER flightplan;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE flightplan_dev TO flightplan;
GRANT ALL PRIVILEGES ON DATABASE flightplan_test TO flightplan;

\q
```

### Docker (Cross-platform)

```bash
# Create docker-compose.yml
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: flightplan_postgres
    environment:
      POSTGRES_USER: flightplan
      POSTGRES_PASSWORD: flightplan_dev_password
      POSTGRES_DB: flightplan_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flightplan"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
EOF

# Create initialization script
cat > init.sql <<EOF
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create test database
CREATE DATABASE flightplan_test OWNER flightplan;
EOF

# Start PostgreSQL
docker-compose up -d

# Verify it's running
docker-compose ps
docker-compose logs postgres
```

---

## Development Database Setup

### Quick Start (Recommended)

```bash
cd backend

# 1. Install PostgreSQL (see above)

# 2. Set environment variables
cat > .env <<EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://flightplan:your_secure_password@localhost:5432/flightplan_dev
TEST_DATABASE_URL=postgresql+asyncpg://flightplan:your_secure_password@localhost:5432/flightplan_test

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Tenant Configuration (dev mode)
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000001
EOF

# 3. Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Verify database
psql postgresql://flightplan:your_secure_password@localhost:5432/flightplan_dev -c "\dt"
```

Expected output:
```
                List of relations
 Schema |         Name          | Type  |   Owner
--------+-----------------------+-------+-----------
 public | alembic_version       | table | flightplan
 public | event_store           | table | flightplan
 public | read_model_admissions | table | flightplan
 public | read_model_flightplans| table | flightplan
 public | read_model_patients   | table | flightplan
 public | read_model_timeline   | table | flightplan
 public | read_model_trajectory | table | flightplan
 public | tenants               | table | flightplan
```

### Alternative: SQLite (Development Only)

```bash
cd backend

# Set environment variable
cat > .env <<EOF
# SQLite for quick local development
DATABASE_URL=sqlite+aiosqlite:///./flightplan_dev.db
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:

ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOF

# Run migrations
alembic upgrade head

# SQLite database file created at: ./flightplan_dev.db
ls -lh flightplan_dev.db
```

**⚠️ WARNING**: SQLite lacks features required for production:
- No row-level security (tenant isolation risk)
- Limited concurrency (write locks)
- No built-in encryption
- Not HIPAA compliant

---

## Production Database Setup

### Cloud Provider Setup

#### AWS RDS (Recommended)

```bash
# Create RDS PostgreSQL 16 instance via AWS Console or CLI
aws rds create-db-instance \
  --db-instance-identifier flightplan-prod \
  --db-instance-class db.r6g.2xlarge \
  --engine postgres \
  --engine-version 16.1 \
  --master-username flightplan_admin \
  --master-user-password SECURE_PASSWORD_HERE \
  --allocated-storage 500 \
  --storage-type gp3 \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:REGION:ACCOUNT:key/KEY_ID \
  --vpc-security-group-ids sg-XXXXX \
  --db-subnet-group-name flightplan-db-subnet \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --deletion-protection \
  --no-publicly-accessible

# Wait for instance to be available
aws rds wait db-instance-available --db-instance-identifier flightplan-prod

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier flightplan-prod \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

#### Azure Database for PostgreSQL

```bash
# Create using Azure CLI
az postgres flexible-server create \
  --resource-group flightplan-rg \
  --name flightplan-prod \
  --location eastus \
  --admin-user flightplan_admin \
  --admin-password SECURE_PASSWORD_HERE \
  --version 16 \
  --sku-name Standard_D4s_v3 \
  --tier GeneralPurpose \
  --storage-size 512 \
  --backup-retention 30 \
  --high-availability Enabled

# Configure firewall (restrict to application servers only)
az postgres flexible-server firewall-rule create \
  --resource-group flightplan-rg \
  --name flightplan-prod \
  --rule-name allow-app-servers \
  --start-ip-address 10.0.1.0 \
  --end-ip-address 10.0.1.255
```

### Production Environment Variables

```bash
# NEVER commit this file - use secret management
cat > .env.production <<EOF
# Production Database (encrypted connection required)
DATABASE_URL=postgresql+asyncpg://flightplan_app:PRODUCTION_PASSWORD@flightplan-prod.xxxxx.us-east-1.rds.amazonaws.com:5432/flightplan_prod?ssl=require

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# Security
SECRET_KEY=GENERATE_SECURE_KEY_HERE
ALLOWED_HOSTS=app.flightplan.example.com

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
EOF

# Set permissions
chmod 600 .env.production
```

### Initial Production Setup

```bash
# 1. Connect to production database
psql "$DATABASE_URL"
```

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgaudit";

-- Create application user (limited privileges)
CREATE USER flightplan_app WITH PASSWORD 'SECURE_APP_PASSWORD';

-- Grant minimal required permissions
GRANT CONNECT ON DATABASE flightplan_prod TO flightplan_app;
GRANT USAGE ON SCHEMA public TO flightplan_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO flightplan_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO flightplan_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO flightplan_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO flightplan_app;

\q
```

```bash
# 2. Run migrations
cd backend
source .venv/bin/activate
alembic upgrade head

# 3. Verify
psql "$DATABASE_URL" -c "SELECT tablename FROM pg_tables WHERE schemaname='public';"
```

---

## Database Migrations

FlightPlan uses **Alembic** for database schema versioning and migrations.

### Migration Workflow

```
[Code Changes] → [Generate Migration] → [Review Migration] → [Apply Migration]
      ↓                    ↓                     ↓                   ↓
   Update models     alembic revision     Edit .py file      alembic upgrade
```

### Common Migration Commands

```bash
cd backend
source .venv/bin/activate

# Check current migration version
alembic current

# View migration history
alembic history

# Upgrade to latest version
alembic upgrade head

# Upgrade one version at a time
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001

# Show SQL without executing (dry run)
alembic upgrade head --sql

# Stamp database with version (without running migrations)
alembic stamp head
```

### Creating New Migrations

#### Auto-generate Migration (Recommended)

```bash
# 1. Update models in app/models/
# Example: Add new field to Patient model

# 2. Generate migration from model changes
alembic revision --autogenerate -m "add patient phone number field"

# 3. Review generated migration file
cat backend/alembic/versions/003_add_patient_phone.py

# 4. Edit if needed (auto-generate isn't perfect)
# - Add data migrations
# - Add custom indexes
# - Add constraints

# 5. Test migration on development database
alembic upgrade head

# 6. Verify changes
psql $DATABASE_URL -c "\d+ patients"

# 7. Test rollback
alembic downgrade -1
alembic upgrade head
```

#### Manual Migration

```bash
# Create empty migration
alembic revision -m "add custom index on event_store"

# Edit the generated file
nano backend/alembic/versions/003_custom_index.py
```

Example migration:
```python
"""add custom index on event_store

Revision ID: 003
Revises: 002
Create Date: 2026-01-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create composite index for common queries
    op.create_index(
        'idx_event_store_tenant_stream',
        'event_store',
        ['tenant_id', 'stream_id', 'event_version'],
        unique=False,
        postgresql_using='btree'
    )

    # Create JSONB GIN index for event data searches
    op.create_index(
        'idx_event_store_data_gin',
        'event_store',
        ['data'],
        unique=False,
        postgresql_using='gin'
    )


def downgrade() -> None:
    op.drop_index('idx_event_store_data_gin', table_name='event_store')
    op.drop_index('idx_event_store_tenant_stream', table_name='event_store')
```

### Migration Best Practices

#### ✅ DO's

1. **Review auto-generated migrations** - they're not always correct
2. **Test migrations on copy of production data** before production deploy
3. **Write reversible migrations** - always implement `downgrade()`
4. **Use transactions** - migrations are wrapped in transactions by default
5. **Add indexes concurrently** in production (PostgreSQL):
   ```python
   op.create_index('idx_name', 'table', ['column'], postgresql_concurrently=True)
   ```
6. **Split large migrations** into smaller, deployable chunks
7. **Document breaking changes** in migration docstring
8. **Test rollback** - ensure `downgrade()` works

#### ❌ DON'Ts

1. **Don't edit applied migrations** - create new migration instead
2. **Don't delete migration files** from version control
3. **Don't skip migrations** - apply them in order
4. **Don't run migrations manually** (use Alembic)
5. **Don't add NOT NULL without default** in one step (causes downtime)
6. **Don't drop columns immediately** - deprecate first, drop later

### Zero-Downtime Migration Pattern

For adding NOT NULL column:

```python
# Migration 1: Add column as nullable with default
def upgrade():
    op.add_column('patients', sa.Column('status', sa.String(50),
                  nullable=True, server_default='active'))

# Migration 2: Backfill data (if needed)
def upgrade():
    op.execute("UPDATE patients SET status = 'active' WHERE status IS NULL")

# Migration 3: Add NOT NULL constraint
def upgrade():
    op.alter_column('patients', 'status', nullable=False)
```

---

## Schema Overview

See [docs/data-model/CURRENT_SCHEMA.md](data-model/CURRENT_SCHEMA.md) for comprehensive schema documentation.

### Core Tables Summary

```sql
-- Event Store (source of truth)
event_store
  - id (BIGSERIAL PRIMARY KEY)
  - tenant_id (UUID, NOT NULL)
  - stream_id (UUID, NOT NULL)
  - stream_type (VARCHAR, NOT NULL)
  - event_version (INTEGER, NOT NULL)
  - event_type (VARCHAR, NOT NULL)
  - data (JSONB, NOT NULL)
  - metadata (JSONB, NOT NULL)
  - created_at (TIMESTAMP, NOT NULL)
  - created_by (UUID, NOT NULL)
  - UNIQUE (tenant_id, stream_id, event_version)

-- Multi-Tenancy
tenants
  - id (UUID PRIMARY KEY)
  - name (VARCHAR, NOT NULL)
  - created_at (TIMESTAMP, NOT NULL)

-- Read Models (projections from events)
read_model_patients (tenant_id, id, data JSONB, version, updated_at)
read_model_admissions (tenant_id, id, patient_id, data JSONB, version, updated_at)
read_model_flightplans (tenant_id, id, admission_id, data JSONB, version, updated_at)
read_model_timeline (tenant_id, id, admission_id, occurred_at, data JSONB)
read_model_trajectory (tenant_id, id, admission_id, effective_at, data JSONB)
```

### Key Indexes

```sql
-- Event store performance
CREATE INDEX idx_event_store_tenant_stream ON event_store(tenant_id, stream_id);
CREATE INDEX idx_event_store_global_order ON event_store(id);
CREATE INDEX idx_event_store_created_at ON event_store(created_at);
CREATE INDEX idx_event_store_data_gin ON event_store USING gin(data);

-- Read model lookups
CREATE INDEX idx_rm_admissions_patient ON read_model_admissions(tenant_id, patient_id);
CREATE INDEX idx_rm_timeline_admission ON read_model_timeline(tenant_id, admission_id, occurred_at);
```

---

## Database Operations

### Common Queries

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('flightplan_dev'));

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT
  pid,
  now() - query_start AS duration,
  query,
  state
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;

-- Kill long-running query
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid = 12345;

-- Vacuum and analyze
VACUUM ANALYZE event_store;

-- Reindex table
REINDEX TABLE event_store;
```

### Connection Pooling

Backend uses SQLAlchemy async connection pooling:

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_size=20,           # Max connections to maintain
    max_overflow=10,        # Max additional connections under load
    pool_timeout=30,        # Wait time for connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Verify connection before use
)
```

Recommended pool sizes:
- Development: `pool_size=5, max_overflow=5`
- Production: `pool_size=20, max_overflow=10`
- High traffic: `pool_size=50, max_overflow=20`

---

## Backup and Restore

### Development Backup

```bash
# Backup entire database
pg_dump -h localhost -U flightplan flightplan_dev > backup_dev_$(date +%Y%m%d).sql

# Backup schema only
pg_dump -h localhost -U flightplan --schema-only flightplan_dev > schema.sql

# Backup data only
pg_dump -h localhost -U flightplan --data-only flightplan_dev > data.sql

# Backup specific table
pg_dump -h localhost -U flightplan -t event_store flightplan_dev > events.sql
```

### Restore Development Database

```bash
# Drop and recreate database
dropdb -h localhost -U flightplan flightplan_dev
createdb -h localhost -U flightplan flightplan_dev

# Restore from backup
psql -h localhost -U flightplan flightplan_dev < backup_dev_20260102.sql

# Or use pg_restore for custom format
pg_restore -h localhost -U flightplan -d flightplan_dev backup.dump
```

### Production Backup (AWS RDS)

```bash
# Automated backups are enabled by default

# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier flightplan-prod \
  --db-snapshot-identifier flightplan-manual-$(date +%Y%m%d-%H%M)

# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier flightplan-prod

# Restore from snapshot (creates new instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier flightplan-restored \
  --db-snapshot-identifier flightplan-manual-20260102-1200
```

### Point-in-Time Recovery (PITR)

```bash
# Restore to specific time (AWS RDS)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier flightplan-prod \
  --target-db-instance-identifier flightplan-pitr-20260102 \
  --restore-time 2026-01-02T10:30:00Z
```

---

## Performance Tuning

### PostgreSQL Configuration

Edit `postgresql.conf` for production:

```conf
# Memory Settings
shared_buffers = 4GB                 # 25% of system RAM
effective_cache_size = 12GB          # 75% of system RAM
maintenance_work_mem = 1GB
work_mem = 16MB

# Connection Settings
max_connections = 200
superuser_reserved_connections = 3

# WAL Settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

# Query Planning
random_page_cost = 1.1               # SSD storage
effective_io_concurrency = 200       # SSD storage
default_statistics_target = 100

# Logging
log_min_duration_statement = 1000    # Log queries > 1 second
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

### Query Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM read_model_admissions
WHERE tenant_id = '...' AND patient_id = '...';

-- Create covering index
CREATE INDEX idx_admissions_covering ON read_model_admissions(
  tenant_id, patient_id
) INCLUDE (data, version, updated_at);

-- Partial index for active admissions
CREATE INDEX idx_active_admissions ON read_model_admissions(tenant_id, patient_id)
WHERE (data->>'status') = 'active';
```

### Monitoring Queries

```sql
-- Table bloat
SELECT
  schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_live_tup, n_dead_tup,
  round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- Index usage
SELECT
  schemaname, tablename, indexname,
  idx_scan, idx_tup_read, idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Cache hit ratio (should be > 99%)
SELECT
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 AS cache_hit_ratio
FROM pg_statio_user_tables;
```

---

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql "postgresql://user:pass@host:5432/dbname"

# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-16-main.log  # Linux
tail -f /usr/local/var/log/postgres.log             # macOS (Homebrew)
```

### Migration Issues

```bash
# Check current version
alembic current

# Fix "alembic_version" table corruption
psql $DATABASE_URL
```
```sql
SELECT * FROM alembic_version;
-- If wrong version:
UPDATE alembic_version SET version_num = '002';
-- Or stamp it:
```
```bash
alembic stamp 002
```

### Performance Issues

```sql
-- Check for missing indexes
SELECT
  schemaname, tablename,
  seq_scan, seq_tup_read,
  idx_scan, idx_tup_fetch,
  seq_tup_read / seq_scan AS avg_seq_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Check for table bloat
SELECT
  schemaname || '.' || tablename AS table,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_dead_tup,
  round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- Fix bloat
VACUUM FULL event_store;  -- WARNING: Takes exclusive lock!
```

### Common Errors

**Error:** `relation "tablename" does not exist`
```bash
# Solution: Run migrations
alembic upgrade head
```

**Error:** `database "flightplan_dev" does not exist`
```bash
# Solution: Create database
createdb -U flightplan flightplan_dev
```

**Error:** `password authentication failed for user "flightplan"`
```bash
# Solution: Reset password
psql postgres
```
```sql
ALTER USER flightplan WITH PASSWORD 'new_password';
```

**Error:** `too many clients already`
```sql
-- Solution: Increase max_connections or kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '10 minutes';
```

---

## Quick Reference

### Essential Commands

```bash
# Database operations
createdb flightplan_dev                  # Create database
dropdb flightplan_dev                    # Delete database
psql flightplan_dev                      # Connect to database

# Migrations
alembic upgrade head                     # Apply all migrations
alembic downgrade -1                     # Rollback one migration
alembic current                          # Show current version
alembic history                          # Show migration history

# Backup/Restore
pg_dump flightplan_dev > backup.sql      # Backup database
psql flightplan_dev < backup.sql         # Restore database

# Monitoring
psql -c "SELECT count(*) FROM pg_stat_activity"  # Active connections
psql -c "\dt+"                           # List tables with sizes
```

### Connection Strings

```bash
# Development (PostgreSQL)
postgresql+asyncpg://user:pass@localhost:5432/flightplan_dev

# Development (SQLite)
sqlite+aiosqlite:///./flightplan_dev.db

# Production (with SSL)
postgresql+asyncpg://user:pass@host:5432/db?ssl=require

# Test (in-memory)
sqlite+aiosqlite:///:memory:
```

---

**Related Documentation:**
- [CURRENT_SCHEMA.md](data-model/CURRENT_SCHEMA.md) - Complete schema documentation
- [TESTING.md](TESTING.md) - Database testing strategies
- [backend/README.md](../backend/README.md) - Backend setup guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow

**PostgreSQL Resources:**
- [Official Documentation](https://www.postgresql.org/docs/16/)
- [Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
