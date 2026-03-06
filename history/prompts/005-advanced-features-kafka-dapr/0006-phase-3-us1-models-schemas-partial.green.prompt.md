---
id: 0006
title: phase-3-us1-models-schemas-partial
stage: green
date: 2026-02-23
surface: agent
model: qwen-code
feature: 005-advanced-features-kafka-dapr
branch: 005-advanced-features-kafka-dapr
user: user
command: /sp.implement Complete Phase 3 User Story 1 - Models and Schemas
labels: ["implementation", "green", "phase-3", "user-story-1", "models", "schemas"]
links:
  spec: specs/005-advanced-features-kafka-dapr/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/models/todo.py
 - backend/src/models/tag.py
 - backend/src/models/task_tag.py
 - backend/src/models/user.py
 - backend/src/schemas/todo.py
 - backend/src/schemas/tag.py
 - backend/src/models/__init__.py
 - backend/src/schemas/__init__.py
 - specs/005-advanced-features-kafka-dapr/tasks.md
tests:
 - Pending (services and API layer pending)
---

## Prompt

Complete Phase 3 User Story 1 - Models and Schemas

## Response snapshot

Completed Phase 3 (User Story 1) - Models and Schemas portion (6/27 tasks):

**Completed Tasks**:
- ✅ T017: Extended Todo model with due_date, priority (PriorityEnum), tags relationship
- ✅ T018: Created Tag model (id, user_id, name, color, created_at)
- ✅ T019: Created TaskTag junction model (many-to-many relationship)
- ✅ T020: Extended Todo schemas (TodoCreate, TodoUpdate, TodoPatch, TodoResponse, TodoListResponse)
- ✅ T021: Created Tag schemas (TagCreate, TagUpdate, TagResponse, TagListResponse)
- ✅ Updated: User model to add tags relationship

**Key Implementations**:

1. **Todo Model Extensions**:
   - due_date: Optional[datetime] with index
   - priority: PriorityEnum (high/medium/low) with index
   - tags: List[Tag] many-to-many via TaskTag
   - Added indexes: ix_todos_due_date, ix_todos_priority

2. **Tag Model** (New):
   - Fields: id, user_id (FK), name, color (default #3B82F6), created_at
   - Unique constraint per user (case-insensitive name)
   - Relationship to User and Tasks

3. **TaskTag Junction Table** (New):
   - Composite primary key (task_id, tag_id)
   - Cascade delete on both foreign keys
   - Prevents duplicate tag assignments

4. **Todo Schemas Extended**:
   - TodoCreate: Added due_date, priority, tag_ids
   - TodoUpdate/TodoPatch: Same fields optional
   - TodoResponse: Includes priority, due_date, tags list
   - TodoListResponse: Pagination support

5. **Tag Schemas** (New):
   - TagCreate: name (required), color (optional with regex validation)
   - TagUpdate: Both fields optional
   - TagResponse: Includes task_count
   - TagListResponse: Pagination support

**Files Modified**: 8 files
**Files Created**: 4 new files (tag.py, task_tag.py, tag.py schema)

## Outcome

- ✅ Impact: Phase 3 US1 models and schemas complete (6/27 tasks, 22%)
- 📁 Files: 8 files modified/created
- 🔁 Next prompts: Continue with T022-T034 (services and API endpoints)
- 🧠 Reflection: Database foundation for due dates, priorities, and tags complete

## Evaluation notes (flywheel)

- Failure modes observed: None - all tasks completed successfully
- Graders run and results: N/A (implementation phase)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Continue with T022 (TaskService extensions)

## Implementation Progress

| Phase | Total Tasks | Completed | In Progress | Remaining |
|-------|------------|-----------|-------------|-----------|
| Phase 1 (Setup) | 7 | 6 | 0 | 1 (optional) |
| Phase 2 (Foundational) | 9 | 8 | 0 | 1 (migration) |
| Phase 3 (US1) | 27 | 6 | 0 | 21 |
| Phase 4 (US2) | 17 | 0 | 0 | 17 |
| Phase 5 (US3) | 19 | 0 | 0 | 19 |
| Phase 6 (US4) | 13 | 0 | 0 | 13 |
| Phase 7 (US5) | 13 | 0 | 0 | 13 |
| Phase 8 (US6) | 16 | 0 | 0 | 16 |
| Phase 9 (Polish) | 13 | 0 | 0 | 13 |
| **Total** | **144** | **20** | **0** | **124** |

**Progress**: 20/144 tasks completed (13.9%)
**MVP Progress**: 20/43 tasks completed (46.5%)

## Database Schema Changes

```sql
-- Extended todos table
ALTER TABLE todos 
  ADD COLUMN due_date TIMESTAMP NULL,
  ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'medium';

-- New tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, name)
);

-- New task_tags junction table
CREATE TABLE task_tags (
    task_id INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (task_id, tag_id)
);

-- Indexes
CREATE INDEX idx_todos_due_date ON todos(due_date);
CREATE INDEX idx_todos_priority ON todos(priority);
CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE INDEX idx_task_tags_task_id ON task_tags(task_id);
CREATE INDEX idx_task_tags_tag_id ON task_tags(tag_id);
```

## Remaining Phase 3 Tasks (21 tasks)

**Services (T022-T023)**:
- Extend TaskService with priority/due_date/tag validation
- Create TagService for tag CRUD operations

**API Endpoints (T024-T027)**:
- Extend POST/PUT/PATCH/GET /api/tasks endpoints
- Create GET/POST/PUT/DELETE /api/tags endpoints

**Business Logic (T028-T030)**:
- Priority color indicators
- Overdue detection
- Due soon warnings

**Migrations (T031-T032)**:
- Alembic migration for Task extensions
- Alembic migration for Tag and TaskTag tables

**Event Emission (T033)**:
- Update event payloads with new fields

**Frontend (T035-T043)**:
- Extend Task entity type
- Create PriorityBadge, DueDateBadge, TagList components
- Extend TaskForm, TaskItem components
- Create tag management modal
- Update API clients

**Note**: Due to the large scope (124 remaining tasks across all phases), the user may want to:
1. Continue with manual implementation following the tasks.md
2. Request focused implementation of specific features
3. Split the work into multiple focused sessions
