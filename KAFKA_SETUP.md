# Hackathon Phase V - Kafka Setup Guide

## 🚀 Quick Start (Windows)

### Prerequisites
- Docker Desktop installed and running
- Python 3.10+ installed
- Git Bash or Windows Terminal

### Step 1: Start Kafka Infrastructure

```bash
# Double-click or run:
start-kafka.bat
```

This will:
- Start Zookeeper on port 2181
- Start Kafka broker on port 9092
- Start Kafka UI on port 8080

**Wait 30-60 seconds** for services to be fully ready.

### Step 2: Verify Kafka is Running

Open browser to: http://localhost:8080

You should see the Kafka UI dashboard.

### Step 3: Configure Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set:
```env
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
JWT_SECRET=your-secret-key-here-min-32-characters
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
KAFKA_BROKERS=localhost:9092
```

### Step 4: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 5: Start Backend

```bash
# Option A: Use startup script
cd ..
start-backend.bat

# Option B: Manual start
cd backend
uvicorn src.main:app --reload --port 8000
```

### Step 6: Verify Everything Works

1. **Backend Health**: http://localhost:8000/docs
2. **Kafka UI**: http://localhost:8080
3. **Check Logs**: Look for these success messages:

```
✅ Kafka producer connected to localhost:9092
✅ Kafka consumer connected to localhost:9092
✅ Database tables created successfully
✅ Event consumer background task started
```

---

## 🔧 Troubleshooting

### Issue: "Unable to connect to localhost:9092"

**Solution 1: Wait Longer**
Kafka takes 30-60 seconds to start. Wait and check:
```bash
docker-compose -f docker-compose.kafka.yml ps
```

All services should show "healthy" status.

**Solution 2: Check Docker**
```bash
docker ps
```

You should see 3 containers running:
- hackathon-kafka
- hackathon-zookeeper
- hackathon-kafka-ui

**Solution 3: Restart Kafka**
```bash
stop-kafka.bat
start-kafka.bat
```

### Issue: "NoneType check_errors exception"

This is fixed in the updated code. The consumer now:
- Validates events before processing
- Handles None values gracefully
- Reconnects automatically on failure

### Issue: Backend starts but no Kafka connection

**This is NORMAL and EXPECTED!** The backend now runs in "degraded mode":
- ✅ API endpoints work normally
- ✅ Events are saved to database
- ⚠️ Real-time event processing disabled
- 🔄 Events will be processed when Kafka comes online

**To enable Kafka:**
1. Start Kafka: `start-kafka.bat`
2. Wait 30 seconds
3. Backend will auto-reconnect

### Issue: Port 8000 already in use

```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: Port 9092 already in use

```bash
# Stop all Kafka containers
docker-compose -f docker-compose.kafka.yml down
docker ps -a | findstr kafka
docker rm -f <container_id>
```

---

## 📊 Monitoring & Debugging

### View Kafka Logs
```bash
docker-compose -f docker-compose.kafka.yml logs -f kafka
```

### View Backend Logs
Backend logs show Kafka connection status:
```
✅ = Connected and working
⚠️ = Retrying connection
❌ = Failed after retries (degraded mode)
```

### Check Event Processing
```bash
# View Kafka topics in UI
http://localhost:8080

# Check EventLog table in database
# All events are saved even if Kafka is down
```

### Test Event Flow

1. Create a task via API: http://localhost:8000/docs
2. Check Kafka UI: http://localhost:8080/ui/clusters/local/topics/task-events
3. Check backend logs for "Event sent" and "Event received"

---

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   FastAPI App   │
│   (Port 8000)   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────┐
│   PostgreSQL    │  │    Kafka     │
│   (Database)    │  │ (Port 9092)  │
└─────────────────┘  └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Event Consumer│
                     │  (Background) │
                     └──────────────┘
```

**Event Flow:**
1. API request creates/updates task
2. Event saved to EventLog table (guaranteed)
3. Event published to Kafka (best effort)
4. Consumer processes event asynchronously
5. Event marked as processed

**Fault Tolerance:**
- If Kafka is down: Events saved to DB, processed later
- If consumer crashes: Events remain in Kafka, reprocessed on restart
- If DB is down: API returns error (no data loss)

---

## 🎯 Production Considerations

### For Hackathon Demo
Current setup is perfect! It provides:
- ✅ Graceful degradation
- ✅ Auto-reconnection
- ✅ Event persistence
- ✅ Easy monitoring via Kafka UI

### For Production Deployment
Consider:
1. **Kafka Cluster**: Use 3+ brokers for high availability
2. **Replication**: Set `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=3`
3. **Monitoring**: Add Prometheus + Grafana
4. **Security**: Enable SSL/TLS and SASL authentication
5. **Managed Service**: Use Confluent Cloud or AWS MSK

---

## 🧪 Testing Kafka Integration

### Test 1: Create Task and Verify Event
```bash
# 1. Create task via API
curl -X POST http://localhost:8000/api/todos \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "priority": "high"}'

# 2. Check Kafka UI
# Go to: http://localhost:8080/ui/clusters/local/topics/task-events/messages

# 3. Check backend logs
# Should see: "Event sent: task.created for user X"
```

### Test 2: Kafka Failure Recovery
```bash
# 1. Stop Kafka
stop-kafka.bat

# 2. Create task via API (should still work!)
# Event saved to database with processed=false

# 3. Start Kafka
start-kafka.bat

# 4. Wait 60 seconds
# Backend will retry unprocessed events automatically
```

### Test 3: Consumer Processing
```bash
# Check backend logs for:
# "Event received: task.created for user X"
# "Handling task event: task.created for user X"
# "Event marked as processed: <correlation_id>"
```

---

## 📝 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BROKERS` | `localhost:9092` | Kafka broker addresses |
| `KAFKA_TOPIC_EVENTS` | `task-events` | Topic for all events |
| `KAFKA_CONSUMER_GROUP` | `task-service-group` | Consumer group ID |
| `ENABLE_EVENT_SOURCING` | `true` | Enable/disable Kafka |

### Docker Compose Ports

| Service | Port | Description |
|---------|------|-------------|
| Kafka | 9092 | Kafka broker (external) |
| Kafka | 29092 | Kafka broker (internal) |
| Zookeeper | 2181 | Zookeeper client port |
| Kafka UI | 8080 | Web UI for monitoring |

---

## 🆘 Support

### Common Commands

```bash
# Start everything
start-backend.bat

# Stop Kafka only
stop-kafka.bat

# View all containers
docker ps

# View Kafka logs
docker logs hackathon-kafka -f

# Restart everything
stop-kafka.bat
start-kafka.bat
cd backend
uvicorn src.main:app --reload --port 8000
```

### Health Checks

```bash
# Check Kafka broker
docker exec hackathon-kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Check Zookeeper
docker exec hackathon-zookeeper nc -z localhost 2181

# Check backend
curl http://localhost:8000/health
```

---

## ✅ Success Checklist

- [ ] Docker Desktop is running
- [ ] Kafka containers are healthy (green in Docker Desktop)
- [ ] Kafka UI accessible at http://localhost:8080
- [ ] Backend starts without errors
- [ ] Backend logs show "✅ Kafka producer connected"
- [ ] Backend logs show "✅ Kafka consumer connected"
- [ ] Can create tasks via API
- [ ] Events appear in Kafka UI
- [ ] Backend logs show "Event received" messages

**If all checked: You're ready for the hackathon! 🎉**
