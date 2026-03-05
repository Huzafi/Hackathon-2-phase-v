# Data Model: Advanced Task Management

**Feature**: 005-advanced-features-kafka-dapr
**Date**: 2026-02-23
**Version**: 1.0.0

---

## Overview

This document defines the extended data model for advanced task management features including due dates, priorities, tags, reminders, recurring tasks, and event sourcing. The design maintains backward compatibility with existing Task entity while adding new entities for enhanced functionality.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
│─────────────────│
│ id (PK)         │
│ email           │
│ hashed_password │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       ┌─────────────────┐
│      Task       │       │       Tag       │
│─────────────────│       │─────────────────│
│ id (PK)         │◄──────│ id (PK)         │
│ user_id (FK)    │       │ user_id (FK)    │
│ title           │       │ name            │
│ description     │       │ color           │
│ completed       │       │ created_at      │
│ due_date        │       └────────┬────────┘
│ priority        │                │
│ created_at      │                │ N:M
│ updated_at      │                │
└────────┬────────┘       ┌────────┴────────┐
         │                │   TaskTag       │
         │ 1:1            │─────────────────│
         ▼                │ task_id (FK,PK) │
┌─────────────────┐       │ tag_id (FK,PK)  │
│ RecurrenceRule  │       └─────────────────┘
│─────────────────│
│ id (PK)         │
│ task_id (FK,UK) │
│ pattern         │
│ interval        │
│ start_date      │
│ end_date        │
│ last_generated  │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│    Reminder     │
│─────────────────│
│ id (PK)         │
│ task_id (FK)    │
│ trigger_time    │
│ delivered       │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│    EventLog     │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ event_type      │
│ payload (JSON)  │
│ timestamp       │
│ processed       │
│ correlation_id  │
└─────────────────┘
```

---

## Entity Definitions

### Task (Extended)

**Purpose**: Represents a todo item with enhanced attributes for due dates, priorities, and tagging.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | int | PK, auto-increment | Unique identifier |
| user_id | int | FK → User.id, NOT NULL, INDEX | Owner of the task |
| title | str | NOT NULL, max 200 chars | Task title |
| description | str | NULL, max 1000 chars | Optional description |
| completed | bool | NOT NULL, default false | Completion status |
| due_date | datetime | NULL, INDEX | Due date and time (UTC) |
| priority | enum | NOT NULL, default 'medium' | high, medium, low |
| created_at | datetime | NOT NULL, default now | Creation timestamp (UTC) |
| updated_at | datetime | NOT NULL, default now | Last update timestamp (UTC) |

**Indexes**:
- `idx_tasks_user_id` (user_id) - Filter by user
- `idx_tasks_due_date` (due_date) - Sort/filter by due date
- `idx_tasks_priority` (priority) - Filter by priority
- `idx_tasks_completed` (completed) - Filter by status
- `idx_tasks_user_due` (user_id, due_date) - Combined filter

**Validation Rules**:
- V-001: title must be 1-200 characters
- V-002: description must be 0-1000 characters
- V-003: due_date cannot be in the past (if provided)
- V-004: priority must be one of: high, medium, low
- V-005: updated_at must be >= created_at

**State Transitions**:
```
created → (incomplete) → completed → (archived)
              ↑              ↓
              └── (toggle) ──┘
```

---

### Tag (New)

**Purpose**: User-defined labels for task categorization.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | int | PK, auto-increment | Unique identifier |
| user_id | int | FK → User.id, NOT NULL, INDEX | Owner of the tag |
| name | str | NOT NULL, max 50 chars, UNIQUE per user | Tag name |
| color | str | NOT NULL, default '#3B82F6', hex format | Display color |
| created_at | datetime | NOT NULL, default now | Creation timestamp |

**Indexes**:
- `idx_tags_user_id` (user_id) - Filter by user
- `idx_tags_user_name` (user_id, name) - Unique constraint per user

**Validation Rules**:
- V-006: name must be 1-50 characters, alphanumeric + hyphens + spaces
- V-007: name must be unique per user (case-insensitive)
- V-008: color must be valid 6-digit hex code (e.g., #FF5733)

**Constraints**:
- C-001: Tag names are case-insensitive unique per user (work = Work = WORK)
- C-002: Deleting a tag does not delete associated tasks (cascade to TaskTag junction)

---

### TaskTag (Junction Table)

**Purpose**: Many-to-many relationship between Tasks and Tags.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| task_id | int | FK → Task.id, PK | Task reference |
| tag_id | int | FK → Tag.id, PK | Tag reference |
| created_at | datetime | NOT NULL, default now | Association timestamp |

**Indexes**:
- `idx_tasktag_task_id` (task_id) - Find tags for task
- `idx_tasktag_tag_id` (tag_id) - Find tasks with tag

**Constraints**:
- C-003: Composite primary key (task_id, tag_id)
- C-004: Unique constraint prevents duplicate tag assignments
- C-005: Cascade delete when task is deleted
- C-006: Cascade delete when tag is deleted

---

### Reminder (New)

**Purpose**: Scheduled notifications for tasks.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | int | PK, auto-increment | Unique identifier |
| task_id | int | FK → Task.id, NOT NULL, INDEX | Associated task |
| trigger_time | datetime | NOT NULL, INDEX | When to send reminder (UTC) |
| delivered | bool | NOT NULL, default false | Delivery status |
| created_at | datetime | NOT NULL, default now | Creation timestamp |

**Indexes**:
- `idx_reminders_task_id` (task_id) - Find reminders for task
- `idx_reminders_trigger_time` (trigger_time) - Schedule queries
- `idx_reminders_pending` (trigger_time, delivered) - Pending reminders

**Validation Rules**:
- V-009: trigger_time cannot be in the past
- V-010: trigger_time must be before or equal to task due_date (if exists)
- V-011: A task can have multiple reminders (no uniqueness constraint)

**State Transitions**:
```
scheduled → triggered → delivered
```

**Constraints**:
- C-007: Deleting a task cascades to delete all associated reminders
- C-008: Reminders are not delivered if task is completed before trigger_time

---

### RecurrenceRule (New)

**Purpose**: Defines how and when a task repeats.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | int | PK, auto-increment | Unique identifier |
| task_id | int | FK → Task.id, NOT NULL, UNIQUE | Parent task |
| pattern | enum | NOT NULL | daily, weekly, monthly, yearly |
| interval | int | NOT NULL, default 1, min 1 | Repeat every N periods |
| start_date | date | NOT NULL | Recurrence start date |
| end_date | date | NULL, must be > start_date | Optional end date |
| by_weekday | str | NULL, format: "MO,WE,FR" | Specific weekdays (for weekly) |
| by_monthday | int | NULL, 1-31 | Specific day of month |
| last_generated | datetime | NULL | Last instance generation |
| created_at | datetime | NOT NULL, default now | Creation timestamp |

**Indexes**:
- `idx_recurrence_task_id` (task_id) - Find rule for task
- `idx_recurrence_pattern` (pattern) - Filter by pattern
- `idx_recurrence_last_generated` (last_generated) - Stale detection

**Validation Rules**:
- V-012: pattern must be one of: daily, weekly, monthly, yearly
- V-013: interval must be >= 1
- V-014: end_date must be > start_date (if provided)
- V-015: by_monthday must be 1-31 (if provided)
- V-016: by_weekday must be valid format (MO,TU,WE,TH,FR,SA,SU comma-separated)

**Constraints**:
- C-009: One-to-one relationship with Task (one rule per task)
- C-010: Deleting a recurring task prompts about future instances
- C-011: last_generated updated when next instance is created

---

### EventLog (New)

**Purpose**: Audit trail of all task operations for reliability and debugging.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | int | PK, auto-increment | Unique identifier |
| user_id | int | FK → User.id, NOT NULL, INDEX | Event owner |
| event_type | enum | NOT NULL, INDEX | Type of event |
| payload | JSON | NOT NULL | Event data |
| timestamp | datetime | NOT NULL, default now, INDEX | Event time (UTC) |
| processed | bool | NOT NULL, default false | Processing status |
| correlation_id | str | NULL, max 36 chars, INDEX, UUID | Tracing ID |
| metadata | JSON | NULL | Additional context |

**Event Types**:
```python
class EventType(Enum):
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    TAG_CREATED = "tag.created"
    TAG_UPDATED = "tag.updated"
    TAG_DELETED = "tag.deleted"
    REMINDER_SET = "reminder.set"
    REMINDER_DELIVERED = "reminder.delivered"
    REMINDER_DELETED = "reminder.deleted"
    RECURRENCE_SET = "recurrence.set"
    RECURRENCE_REMOVED = "recurrence.removed"
    RECURRENCE_GENERATED = "recurrence.generated"
```

**Payload Schema Examples**:
```json
// task.created
{
  "task_id": 123,
  "title": "Complete report",
  "due_date": "2026-02-28T23:59:59Z",
  "priority": "high"
}

// task.completed
{
  "task_id": 123,
  "completed_at": "2026-02-25T14:30:00Z"
}

// recurrence.generated
{
  "parent_task_id": 123,
  "new_task_id": 456,
  "recurrence_pattern": "weekly",
  "generated_at": "2026-02-25T00:00:00Z"
}
```

**Indexes**:
- `idx_eventlog_user_id` (user_id) - Filter by user
- `idx_eventlog_event_type` (event_type) - Filter by type
- `idx_eventlog_timestamp` (timestamp) - Time-based queries
- `idx_eventlog_correlation` (correlation_id) - Tracing
- `idx_eventlog_unprocessed` (processed, timestamp) - Retry queue

**Constraints**:
- C-012: EventLog is append-only (no updates or deletes except for processed flag)
- C-013: Retention policy: Archive events older than 90 days
- C-014: payload schema versioned for forward compatibility

---

## Relationships Summary

| Relationship | Type | Cascade Rules |
|-------------|------|---------------|
| User → Task | 1:N | Delete user → Delete all tasks |
| User → Tag | 1:N | Delete user → Delete all tags |
| Task → Tag | N:M | Delete task → Remove junction entries |
| Task → Reminder | 1:N | Delete task → Delete all reminders |
| Task → RecurrenceRule | 1:1 | Delete task → Delete rule (prompt for future instances) |
| User → EventLog | 1:N | Delete user → Archive all events |

---

## Database Migrations

### Migration Strategy

1. **Backward Compatibility**: All existing Task records remain valid
2. **Nullable Fields**: New fields (due_date, priority) are nullable with defaults
3. **Data Migration**: Existing tasks get default priority 'medium'
4. **Zero Downtime**: Use Alembic for online schema changes

### Migration Order

```sql
-- Step 1: Add new columns to Task (nullable, with defaults)
ALTER TABLE todo ADD COLUMN due_date TIMESTAMP NULL;
ALTER TABLE todo ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'medium';

-- Step 2: Create new tables
CREATE TABLE tag (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, name)
);

CREATE TABLE task_tag (
    task_id INTEGER NOT NULL REFERENCES todo(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (task_id, tag_id)
);

CREATE TABLE reminder (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES todo(id) ON DELETE CASCADE,
    trigger_time TIMESTAMP NOT NULL,
    delivered BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE recurrence_rule (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL UNIQUE REFERENCES todo(id) ON DELETE CASCADE,
    pattern VARCHAR(20) NOT NULL,
    interval INTEGER NOT NULL DEFAULT 1,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    by_weekday VARCHAR(50) NULL,
    by_monthday INTEGER NULL,
    last_generated TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    processed BOOLEAN NOT NULL DEFAULT false,
    correlation_id VARCHAR(36) NULL,
    metadata JSONB NULL
);

-- Step 3: Create indexes
CREATE INDEX idx_tasks_due_date ON todo(due_date);
CREATE INDEX idx_tasks_priority ON todo(priority);
CREATE INDEX idx_tags_user_id ON tag(user_id);
CREATE INDEX idx_reminders_task_id ON reminder(task_id);
CREATE INDEX idx_reminders_trigger_time ON reminder(trigger_time);
CREATE INDEX idx_recurrence_task_id ON recurrence_rule(task_id);
CREATE INDEX idx_eventlog_user_id ON event_log(user_id);
CREATE INDEX idx_eventlog_event_type ON event_log(event_type);
CREATE INDEX idx_eventlog_timestamp ON event_log(timestamp);
CREATE INDEX idx_eventlog_correlation ON event_log(correlation_id);
```

---

## SQLModel Definitions

### Task Model (Extended)

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

class PriorityEnum(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Task(SQLModel, table=True):
    __tablename__ = "todo"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    due_date: Optional[datetime] = Field(default=None, index=True)
    priority: PriorityEnum = Field(default=PriorityEnum.medium, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tags: List["Tag"] = Relationship(back_populates="tasks", link_model="TaskTag")
    reminders: List["Reminder"] = Relationship(back_populates="task")
    recurrence_rule: Optional["RecurrenceRule"] = Relationship(back_populates="task")
```

### Tag Model

```python
class Tag(SQLModel, table=True):
    __tablename__ = "tag"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=50)
    color: str = Field(default="#3B82F6", max_length=7)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tasks: List["Task"] = Relationship(back_populates="tags", link_model="TaskTag")
```

### TaskTag Junction Model

```python
class TaskTag(SQLModel, table=True):
    __tablename__ = "task_tag"
    
    task_id: int = Field(default=None, foreign_key="todo.id", primary_key=True)
    tag_id: int = Field(default=None, foreign_key="tag.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Reminder Model

```python
class Reminder(SQLModel, table=True):
    __tablename__ = "reminder"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="todo.id", index=True)
    trigger_time: datetime
    delivered: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    task: "Task" = Relationship(back_populates="reminders")
```

### RecurrenceRule Model

```python
from typing import Optional, List

class RecurrencePattern(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"

class RecurrenceRule(SQLModel, table=True):
    __tablename__ = "recurrence_rule"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(default=None, foreign_key="todo.id", unique=True)
    pattern: RecurrencePattern
    interval: int = Field(default=1, ge=1)
    start_date: datetime
    end_date: Optional[datetime] = Field(default=None)
    by_weekday: Optional[str] = Field(default=None, max_length=50)
    by_monthday: Optional[int] = Field(default=None, ge=1, le=31)
    last_generated: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    task: "Task" = Relationship(back_populates="recurrence_rule")
```

### EventLog Model

```python
from typing import Dict, Any, Optional

class EventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    TAG_CREATED = "tag.created"
    TAG_UPDATED = "tag.updated"
    TAG_DELETED = "tag.deleted"
    REMINDER_SET = "reminder.set"
    REMINDER_DELIVERED = "reminder.delivered"
    RECURRENCE_GENERATED = "recurrence.generated"

class EventLog(SQLModel, table=True):
    __tablename__ = "event_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    event_type: EventType
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    processed: bool = Field(default=False)
    correlation_id: Optional[str] = Field(default=None, max_length=36, index=True)
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
```

---

## Query Patterns

### Search Tasks with Filters

```python
from sqlalchemy import and_, or_, func, text

def search_tasks(
    user_id: int,
    query: Optional[str] = None,
    priority: Optional[PriorityEnum] = None,
    status: Optional[str] = None,
    tag_ids: Optional[List[int]] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    session: Session
) -> List[Task]:
    filters = [Task.user_id == user_id]
    
    # Full-text search
    if query:
        search_filter = text(
            "to_tsvector('english', title || ' ' || COALESCE(description, '')) @@ plainto_tsquery(:query)"
        )
        filters.append(search_filter)
    
    # Priority filter
    if priority:
        filters.append(Task.priority == priority)
    
    # Status filter
    if status == "overdue":
        filters.append(and_(Task.due_date < datetime.utcnow(), Task.completed == False))
    elif status == "completed":
        filters.append(Task.completed == True)
    elif status == "incomplete":
        filters.append(Task.completed == False)
    
    # Tag filter
    if tag_ids:
        filters.append(Task.tags.any(Tag.id.in_(tag_ids)))
    
    # Due date range
    if due_date_from:
        filters.append(Task.due_date >= due_date_from)
    if due_date_to:
        filters.append(Task.due_date <= due_date_to)
    
    statement = select(Task).where(*filters).order_by(Task.created_at.desc())
    return session.exec(statement).unique().all()
```

### Get Recurring Task Next Occurrence

```python
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY

def get_next_occurrence(rule: RecurrenceRule, after_date: datetime) -> datetime:
    pattern_map = {
        RecurrencePattern.daily: DAILY,
        RecurrencePattern.weekly: WEEKLY,
        RecurrencePattern.monthly: MONTHLY,
        RecurrencePattern.yearly: YEARLY,
    }
    
    freq = pattern_map[rule.pattern]
    rrule_obj = rrule(
        freq=freq,
        interval=rule.interval,
        dtstart=rule.start_date,
        until=rule.end_date,
        byweekday=rule.by_weekday.split(",") if rule.by_weekday else None,
        bymonthday=rule.by_monthday,
    )
    
    return rrule_obj.after(after_date)
```

### Get Pending Reminders

```python
def get_pending_reminders(session: Session, window_minutes: int = 5) -> List[Reminder]:
    """Get reminders due within the next N minutes."""
    now = datetime.utcnow()
    window_end = now + timedelta(minutes=window_minutes)
    
    statement = select(Reminder).where(
        and_(
            Reminder.trigger_time <= window_end,
            Reminder.trigger_time >= now,
            Reminder.delivered == False
        )
    )
    return session.exec(statement).all()
```

---

## Performance Considerations

### Indexing Strategy

1. **Composite Indexes**:
   - `(user_id, due_date)` - User's tasks sorted by due date
   - `(user_id, priority)` - User's tasks filtered by priority
   - `(user_id, completed, created_at)` - User's incomplete tasks

2. **Partial Indexes**:
   ```sql
   CREATE INDEX idx_tasks_overdue ON todo(due_date) 
   WHERE completed = false AND due_date < NOW();
   
   CREATE INDEX idx_reminders_pending ON reminder(trigger_time) 
   WHERE delivered = false;
   ```

3. **Full-Text Search Index**:
   ```sql
   CREATE INDEX idx_tasks_fts ON todo 
   USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')));
   ```

### Query Optimization

1. **Eager Loading**: Use `selectinload` for relationships to avoid N+1 queries
2. **Pagination**: Limit results to 100 tasks per page
3. **Caching**: Cache frequently accessed tags and recurrence rules
4. **Batch Operations**: Process reminders and recurrence in batches of 100

---

## Data Retention

| Entity | Retention Policy | Archive Strategy |
|--------|-----------------|------------------|
| Task | Indefinite (user-owned) | User can delete |
| Tag | Indefinite (user-owned) | Cascade delete with user |
| Reminder | Indefinite (delivered) | Archive after 90 days |
| RecurrenceRule | Indefinite (active) | Archive when end_date passed |
| EventLog | 90 days active | Archive to cold storage |

---

## Next Steps

1. **Create API Contracts**: Define OpenAPI schemas for new endpoints
2. **Generate Alembic Migrations**: Create migration files for schema changes
3. **Update SQLModel Definitions**: Implement models in `backend/src/models/`
4. **Create Service Layer**: Implement business logic for new entities
