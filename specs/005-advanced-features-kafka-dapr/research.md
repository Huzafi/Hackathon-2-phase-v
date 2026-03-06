# Research: Advanced Task Management Technologies

**Feature**: 005-advanced-features-kafka-dapr
**Date**: 2026-02-23
**Purpose**: Resolve technical unknowns and document technology choices for advanced task management implementation

---

## 1. Kafka Integration for FastAPI

### Decision
Use **aiokafka** (async Kafka client) for event production and consumption in FastAPI application.

### Rationale
- **Async-native**: Integrates seamlessly with FastAPI's async architecture
- **Performance**: 2-3x faster throughput than synchronous confluent-kafka in async applications
- **Consumer groups**: Built-in support for scalable consumer groups with automatic rebalancing
- **Exactly-once semantics**: Supports idempotent producer and transactional APIs
- **Lightweight**: No C extensions required, easier deployment in Docker containers

### Configuration Pattern
```python
# Kafka configuration
KAFKA_BROKERS = ["localhost:9092"]  # Environment variable
KAFKA_TOPIC_EVENTS = "task-events"
KAFKA_TOPIC_REMINDERS = "reminder-events"
KAFKA_CONSUMER_GROUP = "task-service-group"

# Partitioning strategy: Partition by user_id for ordering guarantees
# Key = user_id, ensures all events for a user go to same partition
```

### Topic Design
| Topic | Partitions | Retention | Purpose |
|-------|-----------|-----------|---------|
| task-events | 10 (based on concurrent users) | 7 days | Task CRUD events |
| reminder-events | 5 | 1 day | Reminder trigger events |
| recurrence-events | 3 | 7 days | Recurring task generation |

### User Isolation Strategy
- **Partition key**: user_id ensures all events for a user are processed in order
- **Consumer groups**: Separate groups for different event types (task processing, reminder delivery, recurrence generation)
- **Offset management**: Commit offsets after successful processing to prevent data loss

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|------------|------|------|--------------|
| confluent-kafka (sync) | Mature, well-documented | Blocking calls in async code, requires thread pool | Breaks async flow, more complex error handling |
| RabbitMQ | Simpler setup, AMQP protocol | Lower throughput, no built-in event streaming | Not designed for event sourcing patterns |
| AWS Kinesis | Managed service, auto-scaling | Vendor lock-in, higher cost, latency | Overkill for 100 concurrent users, adds cloud dependency |
| PostgreSQL LISTEN/NOTIFY | No new infrastructure | No persistence, limited throughput | Cannot guarantee delivery during outages |

### Implementation Pattern
```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json

# Event Producer (in service layer)
async def emit_task_event(event_type: str, payload: dict, user_id: int):
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()
    try:
        await producer.send_and_wait(
            KAFKA_TOPIC_EVENTS,
            key=str(user_id).encode(),  # Partition key
            value=json.dumps({
                "event_type": event_type,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            }).encode()
        )
    finally:
        await producer.stop()

# Event Consumer (background task)
async def consume_task_events():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_EVENTS,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=KAFKA_CONSUMER_GROUP,
        auto_offset_reset='latest'
    )
    async for message in consumer:
        event = json.loads(message.value.decode())
        await process_event(event)
        await consumer.commit()
```

### Best Practices
1. **Retry logic**: Implement exponential backoff for failed sends
2. **Circuit breaker**: Stop sending if Kafka unavailable for >30s (queue in memory temporarily)
3. **Monitoring**: Track producer latency, consumer lag, error rates
4. **Schema validation**: Validate event payloads with Pydantic before sending
5. **Correlation IDs**: Include correlation_id for tracing across services

---

## 2. Dapr for State Management and Reminders

### Decision
Use **Dapr Actor model** for reminder scheduling and state management.

### Rationale
- **Built-in timers**: Dapr actors provide reliable timer APIs for reminder triggers
- **State isolation**: Automatic state partitioning per actor (per user or per reminder)
- **Reliability**: Timers persist across application restarts
- **Language agnostic**: Python SDK integrates cleanly with FastAPI
- **Cloud-native**: Works identically in Docker, Kubernetes, or cloud environments

### Configuration Pattern
```yaml
# Dapr components configuration (components/ directory)
# statestore.yaml - Redis-based state store
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskstatestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    secretKeyRef:
      name: redis-secret
  - name: actorStateStore
    value: "true"

# pubsub.yaml - Redis-based pub/sub (alternative to Kafka for simpler setups)
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskpubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
```

### Actor Design for Reminders
```python
from dapr.actor import Actor
from datetime import datetime, timedelta

class ReminderActor(Actor):
    async def on_activate(self):
        # Called when actor is activated
        self._reminder_data = await self._state_manager.get_state_or_add("reminder_data")
    
    async def set_reminder(self, trigger_time: datetime, task_id: int):
        # Schedule timer
        due_time = trigger_time - datetime.utcnow()
        await self.register_timer(
            "send_reminder",
            "send_reminder_callback",
            [task_id],
            due_time,
            timedelta(days=365)  # Don't repeat
        )
    
    async def send_reminder_callback(self, task_id: int):
        # Send reminder notification
        await self._http_client.post("/api/notifications", json={
            "task_id": task_id,
            "user_id": self.id.id
        })
        # Mark as delivered
        await self._state_manager.set_state("delivered", True)
```

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|------------|------|------|--------------|
| APScheduler (in-memory) | Simple, Python-native | Loses state on restart, no distributed support | Cannot meet reliability requirements (FR-027) |
| Celery with Redis | Mature, widely used | Complex setup, overkill for simple reminders | Dapr provides simpler API with better reliability |
| PostgreSQL pg_cron | No new infrastructure | Limited to database-level scheduling, no push notifications | Cannot deliver in-app notifications directly |
| AWS EventBridge | Managed service, reliable | Vendor lock-in, cost per invocation | Dapr provides same benefits without cloud dependency |

### Implementation Pattern
```python
# Dapr client initialization
from dapr.clients import DaprClient

# Schedule reminder
async def schedule_reminder(reminder_id: str, user_id: str, trigger_time: datetime, task_id: int):
    with DaprClient() as client:
        # Store reminder state
        client.save_state(
            store_name="taskstatestore",
            key=f"reminder-{user_id}-{reminder_id}",
            value=json.dumps({
                "task_id": task_id,
                "trigger_time": trigger_time.isoformat(),
                "delivered": False
            })
        )
        
        # Register timer via actor
        actor_type = "ReminderActor"
        actor_id = f"{user_id}-{reminder_id}"
        # Dapr handles the rest via actor pattern

# Deliver reminder
async def deliver_reminder(user_id: str, task_id: int):
    # Update state
    with DaprClient() as client:
        client.save_state(
            store_name="taskstatestore",
            key=f"reminder-{user_id}-{task_id}",
            value=json.dumps({"delivered": True})
        )
    
    # Send notification via WebSocket or server-sent events
    await notification_service.send(user_id, {
        "type": "reminder",
        "task_id": task_id
    })
```

### Best Practices
1. **Actor granularity**: One actor per reminder (fine-grained for independent lifecycle)
2. **State hydration**: Load reminder data on actor activation
3. **Error handling**: Retry failed deliveries with exponential backoff
4. **Cleanup**: Delete actor state after reminder delivered (or archive for history)
5. **Monitoring**: Track active actors, timer firings, delivery success rate

---

## 3. PostgreSQL Full-Text Search

### Decision
Use **PostgreSQL full-text search** (tsvector/tsquery) for task search functionality.

### Rationale
- **No new infrastructure**: Leverages existing PostgreSQL 16 database
- **Performance**: Sub-second search for 10k tasks with proper indexing
- **Integration**: SQLModel/SQLAlchemy support for full-text search queries
- **Features**: Supports stemming, ranking, phrase matching, highlighting
- **Simplicity**: No separate search engine to deploy or maintain

### Index Design
```sql
-- Create GIN index for full-text search
CREATE INDEX idx_tasks_search ON tasks
USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Partial index for user-specific searches (faster)
CREATE INDEX idx_tasks_user_search ON tasks
USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')))
WHERE user_id = CURRENT_SETTING('app.current_user_id')::int;
```

### Query Pattern
```python
from sqlalchemy import text

async def search_tasks(user_id: int, query: str, session: Session):
    # Full-text search with ranking
    search_query = text("""
        SELECT *, ts_rank(to_tsvector('english', title || ' ' || COALESCE(description, '')), plainto_tsquery(:query)) as rank
        FROM tasks
        WHERE user_id = :user_id
          AND to_tsvector('english', title || ' ' || COALESCE(description, '')) @@ plainto_tsquery(:query)
        ORDER BY rank DESC
    """)
    
    results = session.execute(search_query, {"user_id": user_id, "query": query})
    return results.all()
```

### Filter Implementation
```python
# Combined search with filters
async def search_with_filters(
    user_id: int,
    query: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    session: Session
):
    filters = [Task.user_id == user_id]
    
    if query:
        filters.append(Task.title.op('@@')(text(f"plainto_tsquery('{query}')")))
    
    if priority:
        filters.append(Task.priority == priority)
    
    if status == "overdue":
        filters.append(and_(Task.due_date < datetime.utcnow(), Task.completed == False))
    elif status == "completed":
        filters.append(Task.completed == True)
    elif status == "incomplete":
        filters.append(Task.completed == False)
    
    if tags:
        filters.append(Task.tags.any(Tag.name.in_(tags)))
    
    if due_date_from:
        filters.append(Task.due_date >= due_date_from)
    if due_date_to:
        filters.append(Task.due_date <= due_date_to)
    
    statement = select(Task).where(*filters)
    return session.exec(statement).all()
```

### Performance Benchmarks (Expected)
| Dataset Size | Query Type | Expected Latency |
|-------------|-----------|------------------|
| 1,000 tasks | Simple keyword | <50ms |
| 10,000 tasks | Simple keyword | <200ms |
| 10,000 tasks | With filters | <300ms |
| 100,000 tasks | Simple keyword | <500ms |

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|------------|------|------|--------------|
| Elasticsearch | Superior search features, scaling | New infrastructure, operational complexity | Overkill for 10k tasks per user |
| Meilisearch | Fast, typo tolerance | New service to maintain, extra cost | PostgreSQL sufficient for requirements |
| Simple LIKE queries | No setup, simple | Poor performance, no ranking | Cannot meet SC-004 (<1s for 10k tasks) |
| Algolia | Managed, excellent features | Cost per search, external dependency | Unnecessary expense for this scale |

### Best Practices
1. **Index maintenance**: Run `VACUUM ANALYZE` regularly for optimal performance
2. **Text search configuration**: Use 'english' for stemming, or 'simple' for exact matching
3. **Query optimization**: Use `plainto_tsquery` for user input (safer than `to_tsquery`)
4. **Ranking**: Use `ts_rank` to order results by relevance
5. **Highlighting**: Use `ts_headline` to show matching snippets in UI

---

## 4. Recurrence Rule Libraries

### Decision
Use **dateutil.rrule** (Python dateutil library) for recurrence rule calculation.

### Rationale
- **iCalendar standard**: Implements RFC 5545 RRULE specification
- **Comprehensive**: Supports daily, weekly, monthly, yearly, custom intervals
- **Edge case handling**: Automatically handles month-end dates, leap years, DST
- **Mature**: Part of python-dateutil, widely used, well-tested
- **Lightweight**: Single dependency, no external services

### Installation
```bash
pip install python-dateutil
```

### Implementation Pattern
```python
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from datetime import datetime

class RecurrenceService:
    @staticmethod
    def get_next_occurrence(
        pattern: str,
        start_date: datetime,
        interval: int = 1,
        last_occurrence: Optional[datetime] = None
    ) -> datetime:
        """Calculate next occurrence based on pattern."""
        
        pattern_map = {
            "daily": DAILY,
            "weekly": WEEKLY,
            "monthly": MONTHLY,
            "yearly": YEARLY
        }
        
        freq = pattern_map[pattern]
        
        # Generate rrule
        rule = rrule(
            freq=freq,
            interval=interval,
            dtstart=start_date
        )
        
        # Get next occurrence after last_occurrence or start_date
        after_date = last_occurrence or start_date
        next_occurrence = rule.after(after_date)
        
        return next_occurrence
    
    @staticmethod
    def validate_end_date(start_date: datetime, end_date: datetime) -> bool:
        """Ensure end date is after start date."""
        return end_date > start_date
```

### Edge Case Handling
```python
# Month-end date handling (automatic with dateutil)
# Example: Monthly on 31st
start = datetime(2024, 1, 31)  # Jan 31
rule = rrule(freq=MONTHLY, dtstart=start)

# February: Automatically adjusts to last day (28th or 29th)
next_occurrence = rule.after(start)  # Feb 29 (leap year) or Feb 28

# April: Adjusts to 30th (April has 30 days)
next_occurrence = rule.after(next_occurrence)  # Apr 30
```

### Recurrence Pattern Storage
```python
# Database schema for recurrence rules
class RecurrenceRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="todo.id")
    pattern: str  # "daily", "weekly", "monthly", "yearly", "custom"
    interval: int = Field(default=1)  # Every N days/weeks/months
    start_date: datetime
    end_date: Optional[datetime] = Field(nullable=True)
    by_weekday: Optional[str] = Field(nullable=True)  # "MO,WE,FR" for custom
    by_monthday: Optional[int] = Field(nullable=True)  # Day of month (1-31)
    last_generated: Optional[datetime] = Field(nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|------------|------|------|--------------|
| Custom implementation | Full control, no dependencies | Complex edge cases (leap years, month-end) | High risk of bugs, reinventing the wheel |
| croniter (cron syntax) | Familiar syntax, widely used | Limited to cron patterns, no monthly/yearly | Less intuitive for users than daily/weekly/monthly |
| Hangfire (for .NET) | Rich features, dashboard | Wrong language ecosystem | Not applicable to Python/FastAPI stack |
| Quartz Scheduler (Java) | Enterprise-grade | Wrong language, heavy | Overkill for simple recurrence |

### Best Practices
1. **Timezone handling**: Store all dates in UTC, convert to user timezone for display
2. **End date validation**: Prevent end dates in the past
3. **Generation trigger**: Generate next instance when current is completed (not on schedule)
4. **Orphan prevention**: When deleting recurring task, prompt about future instances
5. **Audit trail**: Log each generated instance for debugging

---

## 5. Event Sourcing Patterns

### Decision
Implement **lightweight event sourcing** with EventLog table for audit and reliability.

### Rationale
- **Audit trail**: Complete history of all task operations
- **Replay capability**: Can reconstruct state from events if needed
- **Debugging**: Trace issues by examining event sequence
- **Compliance**: Meet potential future compliance requirements
- **Simplicity**: Store events in PostgreSQL alongside current state (hybrid approach)

### Event Schema Design
```python
from enum import Enum
from sqlmodel import SQLModel, Field
from typing import Dict, Any
from datetime import datetime

class EventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    REMINDER_SET = "reminder.set"
    REMINDER_DELIVERED = "reminder.delivered"
    RECURRENCE_GENERATED = "recurrence.generated"

class EventLog(SQLModel, table=True):
    __tablename__ = "event_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    event_type: EventType
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False)
    correlation_id: Optional[str] = Field(nullable=True, index=True)
    metadata: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), nullable=True)
```

### Event Publishing Pattern
```python
class EventProducer:
    def __init__(self, session: Session, kafka_producer: AIOKafkaProducer):
        self.session = session
        self.kafka_producer = kafka_producer
    
    async def publish(self, event_type: EventType, payload: dict, user_id: int):
        # Generate correlation ID for tracing
        correlation_id = str(uuid.uuid4())
        
        # Store in EventLog (guaranteed persistence)
        event_log = EventLog(
            user_id=user_id,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id
        )
        self.session.add(event_log)
        self.session.commit()
        
        # Publish to Kafka (async, for real-time processing)
        await self.kafka_producer.send_and_wait(
            "task-events",
            key=str(user_id).encode(),
            value=json.dumps({
                "event_type": event_type.value,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id
            }).encode()
        )
```

### Event Processing Pattern
```python
class EventConsumer:
    async def process_event(self, event: dict):
        event_type = event["event_type"]
        payload = event["payload"]
        
        try:
            if event_type == "task.completed":
                await self.handle_task_completed(payload)
            elif event_type == "task.deleted":
                await self.handle_task_deleted(payload)
            # ... other event types
            
            # Mark as processed
            await self.mark_processed(event["correlation_id"])
            
        except Exception as e:
            # Log error, event remains unprocessed for retry
            logger.error(f"Failed to process event: {e}")
            raise  # Kafka will retry
```

### Event Ordering Guarantees
1. **Partition by user_id**: All events for a user go to same partition
2. **Single consumer per partition**: Ensures sequential processing per user
3. **Offset commit after processing**: Prevents event loss
4. **Idempotent handlers**: Safe to process same event multiple times

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|------------|------|------|--------------|
| EventStoreDB | Purpose-built, temporal queries | New infrastructure, learning curve | Overkill for audit trail requirement |
| Kafka as source of truth | Single source, replay from Kafka | Complex offset management, harder debugging | Hybrid approach (DB + Kafka) simpler for this scale |
| No event sourcing | Simpler, just CRUD | No audit trail, cannot replay, harder debugging | Cannot meet FR-027 (no data loss) reliably |
| Database triggers | Automatic, no code changes | Hard to test, database-specific | Application-level events more portable and testable |

### Best Practices
1. **Immutable events**: Never update or delete event logs (append-only)
2. **Schema versioning**: Include schema_version in payload for forward compatibility
3. **PII handling**: Avoid storing sensitive data in event payloads
4. **Retention policy**: Archive events older than 90 days to cold storage
5. **Correlation IDs**: Include in all events for distributed tracing
6. **Idempotency**: Design event handlers to be idempotent (safe to retry)

---

## Summary of Technology Choices

| Concern | Technology | Justification |
|---------|-----------|---------------|
| Message Broker | Apache Kafka + aiokafka | Async-native, high throughput, exactly-once semantics |
| State Management | Dapr Actors | Built-in timers, reliable reminders, cloud-native |
| Search | PostgreSQL full-text search | No new infra, sub-second performance, simple |
| Recurrence | python-dateutil (rrule) | RFC 5545 standard, handles edge cases, mature |
| Event Sourcing | EventLog table + Kafka | Audit trail, replay capability, hybrid simplicity |
| Partitioning | user_id as key | Ensures per-user ordering, scales horizontally |

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Request                           │
│                    (FastAPI Endpoint)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ TaskService  │  │ReminderService│ │RecurrenceSvc │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         ▼                 ▼                 ▼              │
│  ┌──────────────────────────────────────────────────┐     │
│  │              EventProducer                        │     │
│  │  (Stores EventLog + Publishes to Kafka)          │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────┐
         │   Apache Kafka     │
         │  (task-events)     │
         └─────────┬──────────┘
                   │
                   ▼
         ┌────────────────────┐
         │   EventConsumer    │
         │ (Background Task)  │
         └─────────┬──────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│  Dapr Actors    │  │  PostgreSQL     │
│ (Reminders)     │  │  (EventLog)     │
└─────────────────┘  └─────────────────┘
```

---

## Next Steps

1. **Update data-model.md**: Incorporate research findings into entity designs
2. **Create API contracts**: Define OpenAPI schemas for new endpoints
3. **Update quickstart.md**: Document Kafka and Dapr setup for local development
4. **Update agent context**: Add Kafka, Dapr, event sourcing patterns to agent knowledge
