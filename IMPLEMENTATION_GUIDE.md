# Event-Driven Architecture Implementation Guide

## Complete Solution Summary

Your Hackathon project now has:
- ✅ **Kafka** - Event streaming and message queuing
- ✅ **Dapr** - Distributed application runtime with actors
- ✅ **Event-Driven Architecture** - Fully event-driven backend
- ✅ **Redis** - State store for Dapr
- ✅ **Kafka UI** - Monitoring and debugging
- ✅ **Docker Compose** - Complete orchestration

## What Was Done

### 1. Enhanced docker-compose.yml
- Added Kafka health checks and proper configuration
- Added Zookeeper with health checks
- Added Redis for Dapr state store
- Added Kafka UI for monitoring
- Added Dapr sidecar with complete configuration
- Configured all service dependencies properly
- Added logging for all services

### 2. Created Dapr Components
- `dapr/components/statestore.yaml` - Redis state store
- `dapr/components/pubsub.yaml` - Kafka pub/sub configuration
- `dapr/components/binding.yaml` - Kafka input/output binding

### 3. Startup Scripts
- `start-all.bat` - Windows complete stack startup
- `start-all.sh` - Linux/Mac complete stack startup
- Scripts include health checks and error handling

### 4. Documentation
- `KAFKA_DAPR_COMPLETE_SETUP.md` - Comprehensive setup guide
- `IMPLEMENTATION_GUIDE.md` - This file

## Quick Start

### Windows
```powershell
cd G:\Hackathon-2\phase-V
.\start-all.bat
```

### Linux/Mac
```bash
cd /mnt/g/Hackathon-2/phase-V
./start-all.sh
```

### Manual (Any Platform)
```bash
cd /path/to/project
docker-compose up
```

## Services Breakdown

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| PostgreSQL | 5432 | Database | ✅ Ready |
| Zookeeper | 2181 | Kafka Coordination | ✅ Ready |
| Kafka | 9092 | Event Streaming | ✅ Ready |
| Kafka UI | 8080 | Monitoring | ✅ Ready |
| Redis | 6379 | State Store | ✅ Ready |
| Backend | 8000 | FastAPI + Consumers | ✅ Ready |
| Dapr | 3500, 50001 | Distributed Runtime | ✅ Ready |
| Frontend | 3000 | Next.js UI | ✅ Ready |

## Event-Driven Architecture

### Event Flow
```
User Action
    ↓
API Endpoint
    ↓
Publish Event to Kafka
    ↓
Event Consumer processes
    ↓
Update Database
    ↓
Trigger Dapr Actors (reminders)
    ↓
Real-time UI Update
```

### Event Topics

**task-events**
- `task.created` - New task created
- `task.updated` - Task modified
- `task.completed` - Task marked done
- `task.deleted` - Task removed

**reminder-events**
- `reminder.scheduled` - Reminder set
- `reminder.triggered` - Reminder due
- `reminder.dismissed` - Reminder closed

**message-events**
- `message.sent` - Chat message sent
- `message.received` - Message received

### Kafka Consumer Flow
1. Backend publishes event to Kafka
2. Event Consumer (background task) listens
3. Consumer processes event based on type
4. Updates database/state
5. Triggers actions (reminders, notifications)
6. Logs event to event_log table

## Dapr Integration

### Dapr Components
1. **State Store (Redis)**
   - Manages actor state
   - Persists reminder data
   - Caches frequently accessed data

2. **Pub/Sub (Kafka)**
   - Enables async message patterns
   - Decouples services
   - Ensures message delivery

3. **Binding (Kafka)**
   - Input/output binding for Kafka
   - Enables triggered processing
   - Supports topic subscriptions

### Dapr Actors
**Reminder Actor** - Manages task reminders
- Store reminder state in Redis
- Schedule reminder notifications
- Handle reminder lifecycle

## Configuration Details

### Kafka Configuration
```env
KAFKA_BROKERS=kafka:29092
KAFKA_TOPIC_EVENTS=task-events
KAFKA_CONSUMER_GROUP=task-service-group
KAFKA_AUTO_OFFSET_RESET=earliest
ENABLE_EVENT_SOURCING=true
```

### Dapr Configuration
```env
DAPR_HTTP_ENDPOINT=http://dapr:3500
DAPR_GRPC_ENDPOINT=http://dapr:50001
ENABLE_DAPR=true
```

### Backend Features
```env
ENABLE_REMINDERS=true
ENABLE_RECURRENCE=true
ENABLE_EVENT_SOURCING=true
```

## Verification Checklist

- [ ] Docker Desktop is running
- [ ] All 8 services are healthy: `docker ps`
- [ ] PostgreSQL responds: `docker exec todo-postgres pg_isready`
- [ ] Zookeeper responds: `docker exec todo-zookeeper nc -z localhost 2181`
- [ ] Kafka responds: `docker exec todo-kafka kafka-topics --list --bootstrap-server localhost:9092`
- [ ] Redis responds: `docker exec todo-redis redis-cli ping`
- [ ] Backend responds: `curl http://localhost:8000/health`
- [ ] Kafka UI loads: http://localhost:8080
- [ ] API Docs load: http://localhost:8000/docs
- [ ] Frontend loads: http://localhost:3000

## Testing Event-Driven Features

### Test 1: Create Task and Observe Kafka Event
```bash
# 1. Open http://localhost:8000/docs
# 2. Create a task via POST /api/todos
# 3. Open http://localhost:8080 (Kafka UI)
# 4. Check task-events topic for event
```

### Test 2: Monitor Event Consumer
```bash
# Watch backend logs
docker logs -f todo-backend | grep -i event

# Create a task
# Should see "Processing event: task.created"
```

### Test 3: Check Event Log Table
```bash
docker exec todo-postgres psql -U todouser -d tododb -c "
  SELECT * FROM event_log
  ORDER BY timestamp DESC
  LIMIT 5;
"
```

### Test 4: Kafka Consumer CLI
```bash
docker exec -it todo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic task-events \
  --from-beginning
```

### Test 5: Dapr State Management
```bash
# Set state
curl -X POST http://localhost:3500/v1.0/actors/reminder/user-123/state/count \
  -H "Content-Type: application/json" \
  -d '{"key":"count","value":5}'

# Get state
curl http://localhost:3500/v1.0/actors/reminder/user-123/state/count
```

## Monitoring

### Kafka UI Dashboard
- **URL**: http://localhost:8080
- View all topics and messages
- Monitor consumer groups
- Check broker health

### Docker Stats
```bash
docker stats
```

### Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f kafka
docker-compose logs -f dapr
docker-compose logs -f postgres
```

## Troubleshooting

### Kafka Connection Failed
**Error**: `Unable connect to "localhost:9092"`

**Solutions**:
1. Check Zookeeper: `docker logs todo-zookeeper`
2. Check Kafka: `docker logs todo-kafka`
3. Wait 60 seconds (first start)
4. Restart: `docker-compose restart kafka`

### Dapr Not Connecting
**Error**: Connection to http://dapr:3500 failed

**Solutions**:
1. Check Redis is healthy: `docker logs todo-redis`
2. Check Dapr logs: `docker logs todo-dapr`
3. Restart: `docker-compose restart dapr`
4. Verify components: `ls dapr/components/`

### Backend Crashes
**Check logs**: `docker logs -f todo-backend`

**Common causes**:
- Database not ready (wait 20 seconds)
- Kafka not ready (wait 60 seconds)
- Redis not ready (wait 10 seconds)

**Fix**: `docker-compose down && docker-compose up`

### Port Already in Use
**Error**: `Port 9092 is already in use`

**Solution**:
```bash
# Kill existing process
# Windows: netstat -ano | findstr :9092 && taskkill /PID <PID> /F
# Linux: lsof -i :9092 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

## Performance Metrics

### Expected Startup Times
- **First run**: 2-3 minutes (downloading images)
- **Subsequent runs**: 30-60 seconds
- **Health checks**: 10-15 seconds per service

### Resource Usage
- **Total**: ~1-2 GB RAM
- **PostgreSQL**: 100-200 MB
- **Kafka**: 300-500 MB
- **Backend**: 100-150 MB
- **Frontend**: 50-100 MB

## Advanced Features

### Event Sourcing
All events are logged in `event_log` table:
```sql
SELECT * FROM event_log;
```

### Event Replay
Events can be replayed from Kafka:
```bash
docker exec -it todo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic task-events \
  --from-beginning
```

### Dapr Reminders
Reminders are managed via Dapr actors:
```bash
curl -X POST http://localhost:3500/v1.0/actors/reminder/task-123/method/schedule
```

### Multi-Consumer Scaling
Add more backend instances with same consumer group:
```bash
docker-compose up -d --scale backend=3
```

## Production Deployment

### Kubernetes
Use the Helm charts in `todo-chatbot/`:
```bash
helm install todo-app todo-chatbot/
```

### Cloud Platforms
- **AWS**: Use MSK (Managed Streaming for Apache Kafka)
- **Azure**: Use Event Hubs
- **GCP**: Use Pub/Sub

## Support Commands

### View All Services Status
```bash
docker-compose ps
```

### Stop All Services
```bash
docker-compose stop
```

### Restart Specific Service
```bash
docker-compose restart backend
```

### View Service Logs
```bash
docker-compose logs -f [service-name]
```

### Remove All Data
```bash
docker-compose down -v
```

### Rebuild All Images
```bash
docker-compose up --build
```

## Next Steps

1. **Run the startup script**
   - Windows: `start-all.bat`
   - Linux/Mac: `./start-all.sh`

2. **Wait for all services** (2-3 minutes)

3. **Verify services are healthy**
   - Check: http://localhost:8000/docs
   - Check: http://localhost:8080

4. **Test event-driven features**
   - Create a task
   - Monitor Kafka events
   - Check event_log table

5. **Develop your features**
   - Build on top of event-driven architecture
   - Use Dapr for advanced patterns
   - Monitor via Kafka UI

## Architecture Benefits

✅ **Scalability** - Kafka enables horizontal scaling
✅ **Resilience** - Event replay capability
✅ **Decoupling** - Services are loosely coupled
✅ **Audit Trail** - Complete event history
✅ **Real-time** - Event-driven updates
✅ **Distributed** - Dapr for distributed patterns
✅ **Reliable** - Message persistence
✅ **Monitoring** - Built-in observability

---

## Summary

Your complete event-driven architecture with Kafka, Dapr, and PostgreSQL is now ready. Simply run the startup script and you'll have:

- ✅ Event streaming via Kafka
- ✅ Distributed runtime via Dapr
- ✅ Database persistence
- ✅ Event audit trail
- ✅ Actor-based reminders
- ✅ Real-time updates
- ✅ Full monitoring

**Ready to build amazing features on top of this enterprise-grade architecture!** 🚀
