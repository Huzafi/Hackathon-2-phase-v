# Database Migration Guide

**Feature**: 005-advanced-features-kafka-dapr  
**Date**: 2026-02-23  
**Version**: 1.0.0

---

## Overview

This guide explains how to run database migrations for the advanced task management features including:
- Event-driven architecture (EventLog table)
- Due dates and priorities for tasks
- Tags and task-tag relationships

---

## Migration Files

Located in `backend/migrations/`:

1. **001_add_event_driven_architecture.sql**
   - Creates `event_log` table for audit trail and event sourcing
   - Indexes for efficient querying
   - Used by: Phase 2 (Foundational)

2. **002_add_advanced_task_features.sql**
   - Extends `todos` table with `due_date` and `priority` columns
   - Creates `tags` table for user-defined tags
   - Creates `task_tags` junction table for many-to-many relationships
   - Used by: Phase 3 (User Story 1)

---

## Prerequisites

- PostgreSQL 16+ database running
- Database user with CREATE TABLE permissions
- Python 3.11+ with dependencies installed
- Database connection string in `.env` file

---

## Migration Methods

### Method 1: Using the Migration Script (Recommended)

```bash
# Navigate to backend directory
cd backend

# Run all pending migrations
python migrate.py

# Check migration status
python migrate.py status
```

**What it does**:
- Creates `migration_log` table to track applied migrations
- Runs migrations in order (001, 002, ...)
- Skips already-applied migrations
- Logs success/failure

**Expected output**:
```
2026-02-23 10:00:00 - INFO - Starting database migrations...
2026-02-23 10:00:01 - INFO - Found 2 migration files
2026-02-23 10:00:01 - INFO - Running 2 pending migrations...
2026-02-23 10:00:02 - INFO - ✓ Applied migration: 001_add_event_driven_architecture.sql
2026-02-23 10:00:03 - INFO - ✓ Applied migration: 002_add_advanced_task_features.sql
2026-02-23 10:00:03 - INFO - ✓ Successfully applied 2/2 migrations
```

### Method 2: Manual SQL Execution

```bash
# Connect to PostgreSQL
psql -h localhost -U todouser -d tododb

# Run migrations in order
\i /path/to/backend/migrations/001_add_event_driven_architecture.sql
\i /path/to/backend/migrations/002_add_advanced_task_features.sql

# Verify tables created
\dt

# Check table structure
\d event_log
\d tags
\d task_tags
\d todos
```

### Method 3: Using Docker

```bash
# Run migrations in Docker container
docker-compose exec backend python migrate.py

# Or manually with psql
docker-compose exec postgres psql -U todouser -d tododb -f /app/migrations/001_add_event_driven_architecture.sql
docker-compose exec postgres psql -U todouser -d tododb -f /app/migrations/002_add_advanced_task_features.sql
```

---

## Migration Details

### Migration 001: Event-Driven Architecture

**Tables Created**:
- `event_log` - Append-only event store

**Columns**:
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER NOT NULL REFERENCES users(id)
event_type      VARCHAR(50) NOT NULL
payload         JSONB NOT NULL
timestamp       TIMESTAMP NOT NULL DEFAULT NOW()
processed       BOOLEAN NOT NULL DEFAULT FALSE
correlation_id  VARCHAR(36)
metadata        JSONB
```

**Indexes Created**:
- `idx_event_log_user_id` - Filter by user
- `idx_event_log_event_type` - Filter by event type
- `idx_event_log_timestamp` - Time-based queries
- `idx_event_log_correlation` - Distributed tracing
- `idx_event_log_processed` - Retry queue processing

**Event Types**:
- `task.*` - task.created, task.updated, task.completed, task.deleted
- `tag.*` - tag.created, tag.updated, tag.deleted
- `reminder.*` - reminder.set, reminder.delivered, reminder.deleted
- `recurrence.*` - recurrence.set, recurrence.removed, recurrence.generated
- `search.*` - search.performed

---

### Migration 002: Advanced Task Features

**Tables Created**:
1. `tags` - User-defined tags
2. `task_tags` - Junction table for task-tag relationships

**Tables Modified**:
1. `todos` - Added due_date and priority columns

**New Columns in `todos`**:
```sql
due_date    TIMESTAMP NULL
priority    VARCHAR(20) NOT NULL DEFAULT 'medium'
```

**Tags Table**:
```sql
id          SERIAL PRIMARY KEY
user_id     INTEGER NOT NULL REFERENCES users(id)
name        VARCHAR(50) NOT NULL
color       VARCHAR(7) NOT NULL DEFAULT '#3B82F6'
created_at  TIMESTAMP NOT NULL DEFAULT NOW()
```

**TaskTags Table**:
```sql
task_id     INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE
tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE
created_at  TIMESTAMP NOT NULL DEFAULT NOW()
PRIMARY KEY (task_id, tag_id)
```

**Indexes Created**:
- `idx_todos_due_date` - Filter/sort by due date
- `idx_todos_priority` - Filter by priority
- `idx_tags_user_id` - Filter by user
- `idx_tags_user_name` - Unique constraint (case-insensitive)
- `idx_task_tags_task_id` - Find tags for task
- `idx_task_tags_tag_id` - Find tasks with tag

**Constraints**:
- Priority must be 'high', 'medium', or 'low'
- Tag name must be alphanumeric + spaces + hyphens
- Tag color must be 6-digit hex code (#RRGGBB)
- Tag name unique per user (case-insensitive)

---

## Verification

After running migrations, verify the schema:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('event_log', 'tags', 'task_tags', 'todos');

-- Check columns in todos
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'todos'
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'todos'
   OR tablename = 'tags'
   OR tablename = 'task_tags'
   OR tablename = 'event_log';

-- Check constraints
SELECT conname, contype, conkey
FROM pg_constraint
WHERE conrelid = 'todos'::regclass;
```

---

## Rollback

**⚠️ WARNING**: Rollback will delete data. Use with caution.

### Rollback Migration 002

```sql
-- Drop junction table
DROP TABLE IF EXISTS task_tags CASCADE;

-- Drop tags table
DROP TABLE IF EXISTS tags CASCADE;

-- Remove columns from todos
ALTER TABLE todos DROP COLUMN IF EXISTS due_date;
ALTER TABLE todos DROP COLUMN IF EXISTS priority;

-- Drop indexes
DROP INDEX IF EXISTS idx_todos_due_date;
DROP INDEX IF EXISTS idx_todos_priority;
```

### Rollback Migration 001

```sql
-- Drop event_log table
DROP TABLE IF EXISTS event_log CASCADE;
```

### Rollback via Script

```bash
# Not implemented yet - manual rollback required
# See SQL commands above
```

---

## Troubleshooting

### Migration Fails

**Error**: `relation "todos" does not exist`

**Solution**: Run base migrations first (users table must exist).

```bash
# Ensure base tables exist
python -c "from src.core.database import create_db_and_tables; create_db_and_tables()"
```

**Error**: `permission denied for table ...`

**Solution**: Grant permissions to database user.

```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO todouser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO todouser;
```

**Error**: `duplicate key value violates unique constraint`

**Solution**: Migration already applied. Check status.

```bash
python migrate.py status
```

### Data Loss Concerns

**Migrations are safe**:
- Migration 001: Creates new table (no data loss)
- Migration 002: Adds nullable columns (no data loss)
- Existing data preserved

**Backup before migrating**:
```bash
# Backup database
pg_dump -h localhost -U todouser tododb > backup_$(date +%Y%m%d).sql

# Restore if needed
psql -h localhost -U todouser -d tododb < backup_20260223.sql
```

---

## Next Steps

After migrations complete:

1. **Verify schema**: Run verification queries above
2. **Test API**: Create tasks with due dates, priorities, tags
3. **Test events**: Check event_log table for new events
4. **Monitor**: Watch for migration-related errors in logs

---

## Migration History

| Version | Date | Description | Status |
|---------|------|-------------|--------|
| 001 | 2026-02-23 | Event-driven architecture | ✅ Created |
| 002 | 2026-02-23 | Advanced task features | ✅ Created |

---

## Support

For issues:
1. Check migration logs: `python migrate.py status`
2. Review SQL files in `backend/migrations/`
3. Check PostgreSQL logs: `docker-compose logs postgres`
4. Verify database connection: `psql -h localhost -U todouser -d tododb`
