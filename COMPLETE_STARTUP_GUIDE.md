# Complete Startup Guide - Kafka & Dapr Critical Stack

## Overview

Your project requires these services running together:

```
┌─────────────────────────────────────────────────────┐
│  Complete Todo ChatBot Stack                        │
├─────────────────────────────────────────────────────┤
│ ✅ PostgreSQL    (Database)                         │
│ ✅ Zookeeper     (Kafka coordination)               │
│ ✅ Kafka         (Event streaming) - CRITICAL       │
│ ✅ Backend       (FastAPI + Dapr) - CRITICAL        │
│ ✅ Frontend      (Next.js)                          │
│ ⚠️  Dapr Runtime (Distributed runtime) - Optional   │
│ ⚠️  Dapr Sidecar (For reminders/actors) - Optional  │
└─────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Windows
- Docker Desktop for Windows (with WSL2)
- WSL2 integration enabled
- Python 3.12+
- Node.js 18+

### Linux/Mac
- Docker & Docker Compose
- Python 3.12+
- Node.js 18+

---

## Step 1: Start All Services with Docker Compose

### Windows PowerShell/CMD

```batch
cd G:\Hackathon-2\phase-V

# Start all services
docker-compose up

# OR in background
docker-compose up -d
```

### Linux/Mac

```bash
cd /mnt/g/Hackathon-2/phase-V

# Start all services
docker-compose up

# OR in background
docker-compose up -d
```

### What Gets Started

```
✅ PostgreSQL     → localhost:5432
✅ Zookeeper      → localhost:2181
✅ Kafka          → localhost:9092
✅ Backend        → localhost:8000
✅ Frontend       → localhost:3000
```

**Wait 60-90 seconds** for all services to be ready.

---

## Step 2: Verify Services Are Running

### Check Docker Containers

```bash
docker ps
```

You should see:
- todo-postgres (PostgreSQL)
- todo-zookeeper (Zookeeper)
- todo-kafka (Kafka)
- todo-backend (Backend API)
- todo-frontend (Frontend)

### Check Backend Logs

```bash
docker logs todo-backend
```

Look for:
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Database tables created successfully
INFO: Kafka consumer connection successful  ← IMPORTANT
INFO: Application startup complete
```

### Check Kafka Connection

```bash
docker logs todo-kafka
```

Look for:
```
[KafkaServer id=1] started
Kafka cluster state changed to Leader
```

---

## Step 3: Enable Kafka in Backend

Your backend `.env` should have:

```env
KAFKA_BROKERS=kafka:29092
KAFKA_TOPIC_EVENTS=task-events
KAFKA_CONSUMER_GROUP=task-service-group
ENABLE_EVENT_SOURCING=true
```

This is already set in docker-compose.yml, so it should work automatically.

---

## Step 4: Test Everything

### Test Backend API

```bash
curl http://localhost:8000
# Should return: {"message":"Todo Backend API","status":"running"}
```

### Access Swagger UI

Open browser:
```
http://localhost:8000/docs
```

You should see all API endpoints documented.

### Test Kafka Connection

From backend container:

```bash
docker exec -it todo-backend python test_kafka.py
```

Expected output:
```
✅ Producer connected successfully
✅ Consumer connected successfully
✅ Test event sent successfully
```

### Access Frontend

Open browser:
```
http://localhost:3000
```

---

## Step 5: Enable Dapr (Optional but Recommended)

Dapr provides actor model for reminders. To enable:

### Install Dapr CLI

**Windows:**
```powershell
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"
```

**Linux/Mac:**
```bash
curl -s https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash
```

### Initialize Dapr

```bash
dapr init
```

### Run Backend with Dapr Sidecar

```bash
dapr run --app-id todo-backend --app-port 8000 -- python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

This will:
- Start Dapr sidecar on port 3500
- Enable actor model
- Enable reminder scheduling
- Enable state management

---

## Services Architecture

### Data Flow

```
Frontend (React)
    ↓ HTTP/REST
Backend (FastAPI)
    ↓ Event
Kafka (Event Stream)
    ↓ Subscribe
Event Consumer (background task)
    ↓ Process
Database (PostgreSQL)
    ↓ State
Dapr Actor (optional - reminders)
```

### What Each Service Does

**PostgreSQL**
- Stores all data
- Event log
- User sessions
- Task data

**Kafka**
- Event streaming
- Async processing
- Real-time updates
- Event sourcing

**Dapr**
- Actor model for reminders
- State management
- Service invocation
- Distributed patterns

**Backend**
- REST API
- Event consumer
- Dapr integration
- AI agent

**Frontend**
- User interface
- Chat with AI
- Real-time updates
- Task management

---

## Troubleshooting

### Issue: "Cannot connect to Docker"

**Windows:**
- Ensure Docker Desktop is running
- Check: Settings → Resources → WSL integration
- Restart Docker Desktop

**Linux/Mac:**
- Start Docker daemon: `sudo service docker start`
- Or use: `systemctl start docker`

### Issue: "Port 9092 already in use"

```bash
# Kill existing process
lsof -ti:9092 | xargs kill -9
# Then restart docker-compose
```

### Issue: "Kafka not connecting"

```bash
# Check Kafka logs
docker logs todo-kafka

# Restart Kafka
docker-compose restart kafka
```

### Issue: "PostgreSQL connection failed"

```bash
# Check database logs
docker logs todo-postgres

# Verify database is healthy
docker exec todo-postgres pg_isready
```

### Issue: "Backend not starting"

```bash
# Check backend logs
docker logs todo-backend -f

# Common fixes:
# 1. Ensure database is ready (wait 30 seconds)
# 2. Check environment variables in docker-compose.yml
# 3. Verify .env file in backend directory
```

---

## Development Workflow

### Local Development (Without Docker)

If you want to run backend locally while services are in Docker:

```bash
# Terminal 1: Start services in Docker
cd /mnt/g/Hackathon-2/phase-V
docker-compose up -d postgres kafka zookeeper

# Wait for services to start (30 seconds)

# Terminal 2: Run backend locally
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 3: Run frontend locally
cd frontend
npm run dev
```

Update backend `.env`:
```env
DATABASE_URL=postgresql://todouser:todopassword@localhost:5432/tododb
KAFKA_BROKERS=localhost:9092
```

### Docker Development (Recommended)

Just run:
```bash
docker-compose up
```

Everything is automatically configured.

---

## Monitoring & Debugging

### Watch Backend Logs

```bash
docker logs -f todo-backend
```

### Watch Kafka Events

```bash
docker exec -it todo-kafka bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic task-events --from-beginning
```

### Check Database

```bash
docker exec -it todo-postgres psql -U todouser -d tododb
```

Then in psql:
```sql
\dt  -- List tables
SELECT * FROM users;  -- View users
SELECT * FROM event_log;  -- View events
```

### Monitor Dapr (if running)

```bash
dapr dashboard
```

Opens: http://localhost:8080

---

## API Testing

### Create a Task

```bash
curl -X POST http://localhost:8000/api/todos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Test Task",
    "description": "Testing Kafka integration",
    "priority": "high"
  }'
```

### Watch Event in Kafka

```bash
docker exec -it todo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic task-events \
  --from-beginning
```

You should see the task.created event.

### Check Event Log

```bash
docker exec -it todo-postgres psql -U todouser -d tododb
SELECT * FROM event_log ORDER BY timestamp DESC;
```

---

## Deployment Commands

### Start All Services

```bash
docker-compose up -d
```

### Stop All Services

```bash
docker-compose down
```

### View Service Status

```bash
docker-compose ps
```

### View Service Logs

```bash
docker-compose logs -f
```

### Rebuild Containers

```bash
docker-compose up --build
```

### Clean Everything

```bash
docker-compose down -v
```

---

## Environment Configuration

Your `.env` files should have:

### backend/.env

```env
DATABASE_URL=postgresql://todouser:todopassword@postgres:5432/tododb
JWT_SECRET=Kf9sP3xR7L2Qm8ZB6D0NwA1E5JH4CYaV
OPENAI_API_KEY=your-key-here
KAFKA_BROKERS=kafka:29092
ENABLE_EVENT_SOURCING=true
```

### docker-compose.yml (already configured)

- PostgreSQL: localhost:5432
- Zookeeper: localhost:2181
- Kafka: localhost:9092
- Backend: localhost:8000
- Frontend: localhost:3000

---

## Success Indicators

✅ **You know everything is working when:**

1. `docker ps` shows 5 containers running
2. Backend logs show: "Application startup complete"
3. Kafka logs show: "Kafka cluster state changed to Leader"
4. Database is healthy: "pg_isready" succeeds
5. http://localhost:8000/docs loads
6. http://localhost:3000 loads frontend
7. Kafka test creates an event
8. Event appears in event_log table

---

## Performance Tips

### Kafka is Slow to Start

- First start takes 60-90 seconds
- Subsequent starts are faster
- Be patient on first run

### Database Takes Time

- Initial table creation: 10-20 seconds
- Subsequent runs: 2-5 seconds

### Frontend Build Takes Time

- First build: 2-3 minutes
- Subsequent builds: 30-60 seconds

### Total Initial Setup Time

**~5-10 minutes** for complete first startup.

---

## Next Steps

1. ✅ Run `docker-compose up`
2. ✅ Wait for all services to be ready
3. ✅ Access http://localhost:8000/docs
4. ✅ Test API endpoints
5. ✅ Create a task and watch Kafka event
6. ✅ Access http://localhost:3000 for frontend
7. ✅ Enable Dapr if needed for advanced features

---

## Support

If services won't start:

1. Check docker-compose.yml for configuration
2. View logs: `docker-compose logs -f service-name`
3. Rebuild: `docker-compose up --build`
4. Clean and restart: `docker-compose down -v && docker-compose up`

Your complete stack is configured and ready! 🚀
