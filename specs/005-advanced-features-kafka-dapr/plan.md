# Implementation Plan: Advanced Task Management with Event-Driven Architecture

**Branch**: `005-advanced-features-kafka-dapr` | **Date**: 2026-02-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification for advanced task management with Kafka and Dapr

## Summary

Implement advanced task management capabilities including recurring tasks, due dates, reminders, priorities, tags, search, filter, and sort functionality. Introduce event-driven architecture using Apache Kafka for reliable message processing and Dapr for distributed application runtime capabilities. The implementation extends the existing FastAPI backend and Next.js frontend while maintaining backward compatibility with existing task operations.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.7+ (frontend), Next.js 15+
**Primary Dependencies**: FastAPI 0.115.6, SQLModel 0.0.22, Kafka (confluent-kafka or aiokafka), Dapr Python SDK, Next.js 15+, React 19
**Storage**: PostgreSQL 16 (existing), Kafka topics for events, Dapr state store for reminders
**Testing**: pytest 8.3.4, pytest-asyncio 0.24.0, httpx 0.28.1 (backend), Jest/React Testing Library (frontend)
**Target Platform**: Docker/Kubernetes deployment (Minikube for local, production-ready for cloud)
**Performance Goals**: 100 concurrent task operations/second, search results <1s for 10k tasks, filter/sort <500ms
**Constraints**: Backward compatible with existing API, sub-second latency for user operations, event ordering per user
**Scale/Scope**: 10,000 tasks per user, 100 concurrent users, existing codebase with 4 prior specs implemented

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is a template with placeholders. Using project-established principles from existing specs:

1. **Spec-Driven Development**: All features follow spec → plan → tasks → implement workflow ✅
2. **Test-First Implementation**: Tests written before implementation code ✅
3. **Backward Compatibility**: Existing APIs remain functional (additive changes only) ✅
4. **Environment Variable Security**: All secrets in environment variables, never hardcoded ✅
5. **Docker-First Deployment**: All changes must work in Docker/Kubernetes environment ✅
6. **User Data Isolation**: Multi-user support with strict data isolation ✅

**Gates Passed**: All established project principles respected.

## Project Structure

### Documentation (this feature)

```text
specs/005-advanced-features-kafka-dapr/
├── plan.md              # This file
├── research.md          # Phase 0 output (Kafka, Dapr, search patterns)
├── data-model.md        # Phase 1 output (Task extensions, new entities)
├── quickstart.md        # Phase 1 output (setup instructions)
├── contracts/           # Phase 1 output (API schemas)
│   ├── tasks-api.yaml   # Extended task endpoints
│   ├── search-api.yaml  # Search and filter endpoints
│   └── events-api.yaml  # Event-driven architecture contracts
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── todo.py              # Extended with due_date, priority, tags
│   │   ├── tag.py               # NEW: Tag entity
│   │   ├── reminder.py          # NEW: Reminder entity
│   │   ├── recurrence.py        # NEW: RecurrenceRule entity
│   │   └── event_log.py         # NEW: EventLog entity for event sourcing
│   ├── schemas/
│   │   ├── todo.py              # Extended schemas
│   │   ├── tag.py               # NEW: Tag schemas
│   │   ├── reminder.py          # NEW: Reminder schemas
│   │   ├── recurrence.py        # NEW: Recurrence schemas
│   │   └── search.py            # NEW: Search/filter request schemas
│   ├── api/
│   │   ├── todos.py             # Extended with new endpoints
│   │   ├── tags.py              # NEW: Tag management endpoints
│   │   ├── reminders.py         # NEW: Reminder endpoints
│   │   ├── search.py            # NEW: Search and filter endpoints
│   │   └── events.py            # NEW: Event streaming endpoints (optional)
│   ├── services/
│   │   ├── event_producer.py    # NEW: Kafka event producer
│   │   ├── event_consumer.py    # NEW: Kafka event consumer
│   │   ├── reminder_service.py  # NEW: Reminder scheduling/delivery
│   │   ├── recurrence_service.py# NEW: Recurring task generation
│   │   └── search_service.py    # NEW: Search and filter logic
│   ├── core/
│   │   ├── kafka.py             # NEW: Kafka client configuration
│   │   └── dapr.py              # NEW: Dapr client configuration
│   └── main.py                  # Extended with new routers
└── tests/
    ├── test_tags.py
    ├── test_reminders.py
    ├── test_recurrence.py
    ├── test_search.py
    └── test_events.py

frontend/
├── app/
│   └── (protected)/
│       └── tasks/
│           └── page.tsx         # Extended with filters, search, sort
├── components/
│   ├── tasks/
│   │   ├── TaskForm.tsx         # Extended with due date, priority, tags
│   │   ├── TaskItem.tsx         # Extended with visual indicators
│   │   ├── TaskFilters.tsx      # NEW: Filter controls
│   │   ├── TaskSearch.tsx       # NEW: Search input
│   │   ├── TaskSort.tsx         # NEW: Sort controls
│   │   ├── RecurrenceSettings.tsx # NEW: Recurrence configuration
│   │   └── ReminderSettings.tsx # NEW: Reminder configuration
│   └── ui/
│       ├── PriorityBadge.tsx    # NEW: Priority indicator
│       ├── DueDateBadge.tsx     # NEW: Due date indicator
│       └── TagList.tsx          # NEW: Tag display
├── lib/
│   └── api/
│       ├── tasks.ts             # Extended API calls
│       ├── tags.ts              # NEW: Tag API
│       ├── reminders.ts         # NEW: Reminder API
│       └── search.ts            # NEW: Search API
└── types/
    └── entities.ts              # Extended with new entities
```

**Structure Decision**: Single project with backend/frontend separation (Option 2). Existing structure preserved, new files added for advanced features. Event-driven architecture implemented in backend services layer.

## Complexity Tracking

> **Justification for Event-Driven Architecture (Kafka + Dapr)**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Kafka message broker | Reliability guarantee (FR-027, FR-028, FR-029) requires durable event queue with ordering | Direct database triggers insufficient for high concurrency, no retry mechanism, couples components tightly |
| Dapr runtime | Simplifies state management, pub/sub abstraction, provides built-in resilience patterns | Custom implementation would require more code, harder to maintain, reinvents distributed systems patterns |
| Event sourcing pattern | Enables audit trail, replay capability, temporal queries | Simple CRUD cannot support "no data loss" requirement during component failures |
| 4 new entities (Tag, Reminder, RecurrenceRule, EventLog) | Required by functional requirements (FR-007 through FR-014, FR-026 through FR-029) | Cannot implement recurring tasks, reminders without dedicated entities |

**Complexity Assessment**: Justified by measurable outcomes (SC-007: 100 concurrent ops/sec, SC-008: 30s recovery, SC-006: 100% recurring task generation). Simpler alternatives cannot meet reliability requirements.

---

## Phase 0: Research & Technology Selection

### Research Topics Identified

1. **Kafka Integration Patterns**
   - Task: Research Kafka integration patterns for FastAPI applications
   - Focus: Async producers/consumers, topic partitioning for user isolation, exactly-once semantics

2. **Dapr State Management**
   - Task: Research Dapr state store configuration for reminder scheduling
   - Focus: Actor model for reminders, timer APIs, state isolation per user

3. **Search Implementation Strategies**
   - Task: Research full-text search patterns in PostgreSQL vs external search engines
   - Focus: PostgreSQL tsvector/tsquery for 10k tasks, indexing strategies, performance benchmarks

4. **Recurrence Rule Calculation**
   - Task: Research recurrence rule libraries and algorithms
   - Focus: Python libraries (dateutil, rrule), edge case handling (month-end dates, leap years)

5. **Event Sourcing Best Practices**
   - Task: Research event sourcing patterns for task management
   - Focus: Event schema design, versioning, snapshot strategies, replay mechanisms

### Research Output Location

All research findings documented in: `research.md`

---

## Phase 1: Design & Contracts

### Data Model Extensions

**Location**: `data-model.md`

**Entities to Design**:
1. **Task Extensions**: due_date (datetime, nullable), priority (enum: high/medium/low), tags (many-to-many)
2. **Tag**: id, user_id, name (unique per user), color (hex), created_at
3. **Reminder**: id, task_id, trigger_time (datetime), delivered (boolean), created_at
4. **RecurrenceRule**: id, task_id, pattern (enum: daily/weekly/monthly/custom), interval (int), end_date (nullable), last_generated (datetime)
5. **EventLog**: id, user_id, event_type (enum), payload (JSON), timestamp, processed (boolean), correlation_id

**Relationships**:
- User → Tags (one-to-many)
- User → Tasks (one-to-many, existing)
- Task → Tags (many-to-many via junction table)
- Task → Reminders (one-to-many)
- Task → RecurrenceRule (one-to-one)
- User → EventLog (one-to-many)

### API Contracts

**Location**: `contracts/`

**New Endpoints**:

**Tags API** (`/api/tags`):
- `GET /api/tags` - List all user's tags
- `POST /api/tags` - Create new tag
- `PUT /api/tags/{id}` - Update tag
- `DELETE /api/tags/{id}` - Delete tag

**Reminders API** (`/api/reminders`):
- `POST /api/reminders` - Create reminder for task
- `GET /api/reminders?task_id={id}` - List reminders for task
- `DELETE /api/reminders/{id}` - Delete reminder

**Search API** (`/api/tasks/search`):
- `GET /api/tasks/search?q={keyword}&priority={level}&status={status}&tags={tags}&due_date={range}` - Search with filters

**Recurrence API** (`/api/tasks/{id}/recurrence`):
- `POST /api/tasks/{id}/recurrence` - Set recurrence rule
- `GET /api/tasks/{id}/recurrence` - Get recurrence rule
- `DELETE /api/tasks/{id}/recurrence` - Remove recurrence

**Extended Tasks API**:
- `POST /api/tasks` - Extended to accept due_date, priority, tag_ids, recurrence
- `PUT /api/tasks/{id}` - Extended to accept all new fields
- `PATCH /api/tasks/{id}` - Extended for partial updates

### Quick Start Guide

**Location**: `quickstart.md`

**Contents**:
1. Prerequisites (Kafka, Dapr installation for local development)
2. Docker Compose setup (Kafka + Zookeeper containers)
3. Dapr initialization commands
4. Environment variables configuration
5. Database migration steps
6. Running the application locally
7. Testing the features

### Agent Context Update

**Action**: Run `.specify/scripts/bash/update-agent-context.sh qwen`

**New Technologies to Document**:
- Apache Kafka (message broker, event streaming)
- Dapr (distributed application runtime, state management, pub/sub)
- Event sourcing pattern
- PostgreSQL full-text search (tsvector/tsquery)
- Recurrence rule patterns (RRULE)

---

## Phase 2: Task Breakdown

**Next Command**: `/sp.tasks`

**Task Categories**:
1. Database models and migrations
2. Kafka event producer/consumer implementation
3. Dapr state store integration
4. Tag management API and UI
5. Reminder scheduling and delivery
6. Recurring task generation logic
7. Search and filter implementation
8. Sort functionality
9. Frontend UI components
10. Integration tests
11. Performance testing

---

## Constitution Re-Check (Post-Design)

After Phase 1 design completion, verify:

- [ ] All new code follows existing project structure
- [ ] All secrets (Kafka brokers, Dapr configuration) in environment variables
- [ ] All new endpoints require JWT authentication
- [ ] All database queries filter by user_id
- [ ] Docker Compose updated with Kafka/Zookeeper services
- [ ] Helm chart updated for Kubernetes deployment
- [ ] Tests written for all new functionality
- [ ] API contracts documented in OpenAPI format

---

## Success Metrics Alignment

| Success Criteria | Technical Metric | Measurement Method |
|-----------------|------------------|-------------------|
| SC-001: Create task <15s | API response time <200ms | Load testing with k6 |
| SC-003: Reminders <5s latency | Reminder delivery time | Dapr timer accuracy monitoring |
| SC-004: Search <1s for 10k tasks | Query execution time | PostgreSQL query logs |
| SC-005: Filter/sort <500ms | API response time | Load testing |
| SC-007: 100 concurrent ops/sec | Throughput | Kafka consumer lag monitoring |
| SC-008: 30s recovery | Component restart time | Chaos engineering tests |

---

## Risk Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| Kafka adds operational complexity | High | Use Docker Compose for local, managed Kafka (Confluent Cloud) for production |
| Dapr learning curve | Medium | Extensive documentation in quickstart.md, use Dapr's local development mode |
| Event ordering complexity | High | Partition Kafka topics by user_id, ensure single consumer per partition |
| Database migration downtime | Medium | Use Alembic for zero-downtime migrations, backward-compatible schema changes |
| Search performance degradation | Medium | Implement PostgreSQL full-text search indexes, monitor query plans |

---

## Next Steps

1. **Phase 0**: Complete research.md with Kafka, Dapr, search patterns
2. **Phase 1**: Create data-model.md, API contracts, quickstart.md
3. **Phase 1**: Update agent context with new technologies
4. **Phase 2**: Run `/sp.tasks` to generate implementation tasks
5. **Implementation**: Execute tasks with test-first approach
6. **Verification**: Validate against success criteria
