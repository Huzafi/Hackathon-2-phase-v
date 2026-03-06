# Windows Quick Start - Kafka & Dapr Full Stack

## Prerequisites Check

Before starting, verify you have:

```powershell
# Check Docker
docker --version
# Should output: Docker version 20.x.x or higher

# Check Docker Desktop is running
docker ps
# Should list containers without errors

# Check WSL2
wsl --list --verbose
# Should show WSL2 as the default distro
```

If Docker isn't working:
1. Open Docker Desktop
2. Go to Settings → Resources → WSL integration
3. Enable WSL2 integration
4. Restart Docker Desktop

---

## Step 1: Navigate to Project

```powershell
cd G:\Hackathon-2\phase-V
```

---

## Step 2: Start Complete Stack (ONE COMMAND)

```powershell
docker-compose up
```

**Wait 60-90 seconds** for everything to start.

You should see logs like:
```
Creating network "phase-v_todo-network" with driver "bridge"
Creating todo-postgres ... done
Creating todo-zookeeper ... done
Creating todo-kafka ... done
Creating todo-backend ... done
Creating todo-frontend ... done
```

---

## Step 3: Verify Services Running

Open new PowerShell window:

```powershell
docker ps
```

You should see 5 containers:
- todo-postgres
- todo-zookeeper
- todo-kafka
- todo-backend
- todo-frontend

---

## Step 4: Access Applications

### Backend API
```
http://localhost:8000
```

### Swagger Documentation
```
http://localhost:8000/docs
```

### Frontend
```
http://localhost:3000
```

### ReDoc
```
http://localhost:8000/redoc
```

---

## Step 5: Test Kafka Connection

Open new PowerShell window:

```powershell
cd G:\Hackathon-2\phase-V

# Run Kafka test
docker exec -it todo-backend python test_kafka.py
```

Expected output:
```
✅ Producer connected successfully
✅ Consumer connected successfully
✅ Test event sent successfully
```

---

## Step 6: Test API

### Create Task (Test Event Streaming)

```powershell
# First, get auth token (or use from frontend)
$body = @{
    email = "test@example.com"
    password = "testpassword"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/login" `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"} `
  -Body $body

$token = $response | ConvertFrom-Json | Select-Object -ExpandProperty access_token

# Create task
$task = @{
    title = "Test Kafka Integration"
    description = "Testing event streaming"
    priority = "high"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/todos" `
  -Method POST `
  -Headers @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
  } `
  -Body $task
```

Or use Swagger UI (easier):
1. Go to http://localhost:8000/docs
2. Click "Authorize" and login
3. Try /api/todos POST with sample data

---

## Step 7: Monitor Kafka Events

```powershell
# Watch Kafka events in real-time
docker exec -it todo-kafka kafka-console-consumer `
  --bootstrap-server localhost:9092 `
  --topic task-events `
  --from-beginning
```

Create a task via API and watch the event appear here!

---

## Step 8: Check Database

```powershell
# Connect to PostgreSQL
docker exec -it todo-postgres psql -U todouser -d tododb

# In psql, view events:
SELECT * FROM event_log ORDER BY timestamp DESC LIMIT 10;

# View tasks:
SELECT * FROM todo;

# Exit:
\q
```

---

## Stop Everything

When done developing:

```powershell
# Stop all services (keep data)
docker-compose stop

# Or stop and remove (delete data)
docker-compose down
```

---

## Restart Everything

```powershell
# Just restart from stopped state
docker-compose start

# Or full restart
docker-compose down
docker-compose up
```

---

## View Logs

### All Services
```powershell
docker-compose logs -f
```

### Specific Service
```powershell
# Backend
docker-compose logs -f backend

# Kafka
docker-compose logs -f kafka

# Database
docker-compose logs -f postgres

# Frontend
docker-compose logs -f frontend
```

---

## Troubleshooting

### Issue: "Docker command not found"
**Fix**: Start Docker Desktop

### Issue: "Port 8000 already in use"
**Fix**:
```powershell
# Find process on port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with actual number)
taskkill /PID <PID> /F

# Then restart
docker-compose up
```

### Issue: "Kafka won't connect"
**Fix**:
```powershell
# Restart Kafka
docker-compose restart kafka

# Wait 30 seconds then check logs
docker logs todo-kafka
```

### Issue: "PostgreSQL connection refused"
**Fix**:
```powershell
# Check database health
docker exec todo-postgres pg_isready

# If not ready, restart
docker-compose restart postgres

# Wait 20 seconds
```

### Issue: "Backend crashes on startup"
**Fix**:
```powershell
# Check backend logs
docker logs -f todo-backend

# Common causes:
# 1. Database not ready (wait longer)
# 2. Kafka not ready (restart kafka)
# 3. .env file issues

# Full restart
docker-compose down
docker-compose up --build
```

---

## Feature Checklist

After startup, verify these work:

- [ ] Backend API responds: http://localhost:8000
- [ ] Swagger UI loads: http://localhost:8000/docs
- [ ] Frontend loads: http://localhost:3000
- [ ] Create task appears in database
- [ ] Task event appears in Kafka topic
- [ ] Event appears in event_log table
- [ ] Can login with credentials
- [ ] Can create/edit/delete tasks
- [ ] Chat interface works
- [ ] AI agent responds

---

## Performance Notes

### First Startup (5-10 minutes)
- Docker pulls images (~2 GB)
- Containers initialize
- Databases create tables
- Services connect to each other

### Subsequent Startups (1-2 minutes)
- Containers already built
- Much faster startup

### Running Services (~100-200 MB RAM)
- PostgreSQL: 50-80 MB
- Kafka: 300-500 MB
- Backend: 50-100 MB
- Frontend: 30-50 MB
- Total: ~500-800 MB

---

## Development Workflow

### Option 1: Docker Development (RECOMMENDED)
```powershell
# Start everything in Docker
docker-compose up

# Access at:
# - http://localhost:8000 (backend)
# - http://localhost:3000 (frontend)

# View logs
docker-compose logs -f
```

### Option 2: Local Backend + Docker Services
```powershell
# Terminal 1: Start only services
docker-compose up postgres zookeeper kafka

# Terminal 2: Run backend locally
cd backend
.venv\Scripts\activate
uvicorn src.main:app --reload

# Terminal 3: Run frontend locally
cd frontend
npm run dev
```

### Option 3: Everything Local (No Docker)
```powershell
# Start Kafka locally (requires Kafka installed)
# This is more complex, use Option 1 instead
```

---

## Important Files

- `docker-compose.yml` - Complete stack configuration
- `backend/.env` - Backend configuration
- `frontend/.env.local` - Frontend configuration
- `COMPLETE_STARTUP_GUIDE.md` - Detailed documentation
- `KAFKA_CONNECTION_FIX.md` - Troubleshooting

---

## Next Steps

1. ✅ Run `docker-compose up`
2. ✅ Wait for services to start (60-90 seconds)
3. ✅ Open http://localhost:8000/docs
4. ✅ Test creating a task
5. ✅ Watch Kafka event appear
6. ✅ Check database for event_log entry
7. ✅ Start developing!

---

## One More Thing...

Keep Docker Desktop running in the background while developing.
All services will automatically restart if they crash.

You're all set! 🚀
