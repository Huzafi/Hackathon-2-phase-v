# Kafka & Dapr Complete Setup Guide

## Overview

This guide provides complete setup for event-driven architecture with Kafka and Dapr integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Event-Driven Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Frontend (Next.js)                                             │
│       ↓ HTTP                                                    │
│  Backend (FastAPI)                                              │
│       ├─→ Kafka Producer (publish events)                       │
│       ├→ Event Consumer (subscribe to events)                   │
│       ├→ Database (PostgreSQL)                                  │
│       └→ Dapr Sidecar (actors, state management)                │
│                                                                 │
│  Event Flow:                                                    │
│  1. API request → Task created                                  │
│  2. Backend publishes to Kafka (task.created)                   │
│  3. Event Consumer processes event                              │
│  4. Updates database & triggers reminders                       │
│  5. Dapr Actor manages reminder state                           │
│  6. Real-time updates to frontend                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Services

### 1. PostgreSQL (Database)
- **Port**: 5432
- **Username**: todouser
- **Password**: todopassword
- **Database**: tododb
- **Purpose**: Data persistence

### 2. Zookeeper (Kafka Coordination)
- **Port**: 2181
- **Purpose**: Kafka cluster coordination
- **Status**: Must be healthy before Kafka starts

### 3. Kafka (Event Streaming)
- **Port**: 9092 (external), 29092 (internal)
- **Purpose**: Event streaming and message queuing
- **Topics**:
  - `task-events` (task operations)
  - `reminder-events` (reminder scheduling)
  - `message-events` (chat messages)

### 4. Kafka UI (Monitoring)
- **Port**: 8080
- **URL**: http://localhost:8080
- **Purpose**: Visual monitoring of Kafka topics and messages

### 5. Redis (State Store)
- **Port**: 6379
- **Purpose**: Dapr state persistence
- **Used by**: Dapr for actor state, caching

### 6. Backend (FastAPI)
- **Port**: 8000
- **Features**:
  - Kafka producer (publishes events)
  - Kafka consumer (processes events)
  - Dapr integration
  - REST API

### 7. Dapr Sidecar
- **HTTP Port**: 3500
- **gRPC Port**: 50001
- **Purpose**:
  - Actor model for reminders
  - State management (Redis backend)
  - Service invocation
  - Pub/Sub (Kafka)

### 8. Frontend (Next.js)
- **Port**: 3000
- **Purpose**: Web UI

## Quick Start

### Windows

1. **Ensure Docker Desktop is running**
   - Click Docker Desktop icon
   - Wait for it to start

2. **Navigate to project**
   ```powershell
   cd G:\Hackathon-2\phase-V
   ```

3. **Start all services**
   ```powershell
   docker-compose up
   ```

4. **Wait for startup** (2-3 minutes first time)
   ```
   Expected messages:
   ✓ postgres_1 | database system is ready to accept connections
   ✓ zookeeper_1 | Successfully registered ZooKeeper as a Dapr component
   ✓ kafka_1 | [KafkaServer id=1] started
   ✓ backend_1 | Application startup complete
   ```

5. **Access services**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Kafka UI: http://localhost:8080
   - Frontend: http://localhost:3000

### Linux/Mac

```bash
cd /mnt/g/Hackathon-2/phase-V
docker-compose up
```

## Verification

### Check All Services

```bash
docker ps
```

Should show 8 containers:
- todo-postgres
- todo-zookeeper
- todo-kafka
- todo-kafka-ui
- todo-redis
- todo-backend
- todo-dapr
- todo-frontend

### Check Service Health

```bash
# PostgreSQL
docker exec todo-postgres pg_isready -U todouser -d tododb

# Zookeeper
docker exec todo-zookeeper nc -z localhost 2181

# Kafka
docker exec todo-kafka kafka-topics --list --bootstrap-server localhost:9092

# Redis
docker exec todo-redis redis-cli ping

# Backend
curl http://localhost:8000/health

# Dapr
curl http://localhost:3500/v1.0/invoke/todo-backend/method/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f kafka
docker-compose logs -f dapr
```

## Event Flow Testing

### 1. Create a Task and Observe Event

**Step 1**: Get API docs
- Open http://localhost:8000/docs

**Step 2**: Create a task
```bash
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Testing Kafka event",
    "priority": "high"
  }'
```

**Step 3**: Check Kafka UI
- Open http://localhost:8080
- Look for `task-events` topic
- Should show `task.created` event

**Step 4**: Verify event was processed
```bash
docker exec todo-postgres psql -U todouser -d tododb -c "SELECT * FROM event_log ORDER BY timestamp DESC LIMIT 5;"
```

### 2. Monitor Kafka Events in Real-time

```bash
docker exec -it todo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic task-events \
  --from-beginning
```

### 3. Test Dapr Actor State

```bash
# Save state
curl -X POST http://localhost:3500/v1.0/actors/reminder/user-123/state/reminderCount \
  -H "Content-Type: application/json" \
  -d '{"key":"reminderCount","value":5}'

# Get state
curl http://localhost:3500/v1.0/actors/reminder/user-123/state/reminderCount
```

### 4. Test Dapr Pub/Sub

```bash
# Publish message
curl -X POST http://localhost:3500/v1.0/publish/pubsub/task-events \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "task.updated",
    "taskId": "123",
    "timestamp": "2026-03-05T00:00:00Z"
  }'
```

## Troubleshooting

### Issue: Kafka Won't Connect

**Symptoms**:
```
ERROR - Unable connect to "localhost:9092"
WARNING - Kafka consumer connection attempt 1/3 failed
```

**Solutions**:
1. Check Zookeeper is healthy:
   ```bash
   docker logs todo-zookeeper | grep "Started"
   ```

2. Check Kafka is healthy:
   ```bash
   docker logs todo-kafka | grep "Kafka cluster state changed to Leader"
   ```

3. Wait longer (Kafka takes 30-60 seconds to start)

4. Restart Kafka:
   ```bash
   docker-compose restart kafka
   sleep 30
   docker-compose restart backend
   ```

### Issue: Port Already in Use

```bash
# Find process on port
netstat -ano | findstr :9092
# or on Linux
lsof -i :9092

# Kill process
taskkill /PID <PID> /F  # Windows
kill <PID>             # Linux
```

### Issue: Dapr Not Connecting

**Check Dapr logs**:
```bash
docker logs todo-dapr
```

**Common issues**:
- Redis not ready
- Wrong endpoint configuration
- Components not found

**Fix**:
```bash
docker-compose restart redis
docker-compose restart dapr
```

### Issue: Backend Crashes on Startup

**Check logs**:
```bash
docker logs -f todo-backend
```

**Common causes**:
1. Database not ready (wait 20 seconds)
2. Kafka not ready (wait 60 seconds)
3. Redis not ready (wait 10 seconds)

**Fix**:
```bash
docker-compose down
docker-compose up --build
```

## Configuration Files

### docker-compose.yml
- Complete service definitions
- Health checks
- Environment variables
- Volumes and networks

### dapr/components/statestore.yaml
- Redis state store for Dapr
- Actor state persistence

### dapr/components/pubsub.yaml
- Kafka pub/sub for Dapr
- Event publishing and subscribing

### dapr/components/binding.yaml
- Kafka input/output binding
- Topic configuration

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://todouser:todopassword@postgres:5432/tododb?sslmode=disable

# Kafka
KAFKA_BROKERS=kafka:29092
KAFKA_TOPIC_EVENTS=task-events
KAFKA_CONSUMER_GROUP=task-service-group
ENABLE_EVENT_SOURCING=true

# Dapr
DAPR_HTTP_ENDPOINT=http://dapr:3500
DAPR_GRPC_ENDPOINT=http://dapr:50001
ENABLE_DAPR=true

# Features
ENABLE_REMINDERS=true
ENABLE_RECURRENCE=true
```

## Event Topics & Messages

### task-events Topic
```json
{
  "eventType": "task.created",
  "taskId": "uuid",
  "userId": "uuid",
  "data": {
    "title": "Task Title",
    "description": "Description",
    "priority": "high"
  },
  "timestamp": "2026-03-05T00:00:00Z"
}
```

### reminder-events Topic
```json
{
  "eventType": "reminder.scheduled",
  "reminderId": "uuid",
  "taskId": "uuid",
  "dueTime": "2026-03-05T10:00:00Z",
  "timestamp": "2026-03-05T00:00:00Z"
}
```

### message-events Topic
```json
{
  "eventType": "message.sent",
  "messageId": "uuid",
  "conversationId": "uuid",
  "userId": "uuid",
  "content": "Message content",
  "timestamp": "2026-03-05T00:00:00Z"
}
```

## Dapr Actors

### Reminder Actor
- **Actor Type**: `reminder`
- **Methods**:
  - `schedule` - Schedule a reminder
  - `cancel` - Cancel a reminder
  - `get_state` - Get reminder state

**Example**:
```bash
curl -X POST http://localhost:3500/v1.0/actors/reminder/reminder-123/method/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "task-123",
    "dueTime": "2026-03-05T10:00:00Z"
  }'
```

## Performance Tuning

### Kafka Optimization
```yaml
KAFKA_COMPRESSION_TYPE: gzip
KAFKA_LOG_RETENTION_HOURS: 168
KAFKA_LOG_RETENTION_BYTES: 1073741824
KAFKA_LOG_SEGMENT_BYTES: 1073741824
KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 3000
```

### Consumer Group
```env
KAFKA_CONSUMER_GROUP=task-service-group
KAFKA_AUTO_OFFSET_RESET=earliest
```

## Monitoring

### Kafka UI
- **URL**: http://localhost:8080
- **Features**:
  - Topic monitoring
  - Partition details
  - Message browsing
  - Consumer groups

### Docker Stats
```bash
docker stats
```

### Backend Metrics
```bash
curl http://localhost:8000/metrics
```

## Stopping Services

```bash
# Stop all services (keep data)
docker-compose stop

# Stop and remove (delete data)
docker-compose down

# Stop and clean volumes (complete reset)
docker-compose down -v
```

## Restarting Services

```bash
# Start all again
docker-compose up

# Restart specific service
docker-compose restart backend

# Full rebuild
docker-compose up --build
```

## Next Steps

1. ✅ Start docker-compose
2. ✅ Wait for all services to be healthy
3. ✅ Open http://localhost:8000/docs
4. ✅ Create a task and observe Kafka event
5. ✅ Check Kafka UI at http://localhost:8080
6. ✅ Monitor event processing
7. ✅ Test Dapr actor state
8. ✅ Build your event-driven features

## Support

For detailed logs:
```bash
docker-compose logs -f
```

For specific service:
```bash
docker-compose logs -f <service-name>
```

For real-time monitoring:
```bash
docker stats
```

---

**Your complete event-driven architecture is now configured and ready!** 🚀
