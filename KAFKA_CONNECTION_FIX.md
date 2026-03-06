# Kafka Connection Issue - Fix Guide

## Issue Summary

**Problem**: Kafka connection failing on localhost:9092
**Error**: `[Errno 10061] Connect call failed ('127.0.0.1', 9092)`
**Status**: ⚠️ WARNING (Backend still works, graceful degradation)

---

## What's Happening

Your backend is running perfectly, but Kafka is not available:

```
✅ FastAPI server:      http://127.0.0.1:8000 (WORKING)
✅ Database:            PostgreSQL (WORKING)
✅ API Endpoints:       /docs, /redoc (WORKING)
⚠️  Kafka Consumer:      localhost:9092 (NOT RUNNING)
```

The backend has **graceful degradation** - it keeps working without Kafka, but event streaming features are disabled.

---

## How to Fix

### Option 1: Start Kafka with Docker (RECOMMENDED)

**Windows Command:**
```batch
cd G:\Hackathon-2\phase-V
docker-compose up
```

Or start only Kafka:
```batch
docker-compose up kafka zookeeper
```

**What to expect:**
- Zookeeper starts on port 2181
- Kafka starts on port 9092
- Wait 30-60 seconds for readiness

**Then restart backend:**
```batch
cd backend
uvicorn src.main:app --reload --port 8000
```

**Verify Kafka is connected:**
Look for log message:
```
INFO - Kafka consumer connection successful
```

---

### Option 2: Start Kafka Locally (if installed)

If you have Kafka installed locally:

```bash
# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# In another terminal, start Kafka
bin/kafka-server-start.sh config/server.properties
```

---

### Option 3: Skip Kafka (for development)

If you don't need Kafka for now:

**Edit backend/.env:**
```env
ENABLE_EVENT_SOURCING=false
```

**Restart backend:**
```batch
cd backend
uvicorn src.main:app --reload --port 8000
```

This will disable event streaming but API will work normally.

---

### Option 4: Use Different Kafka Server

If you have Kafka running elsewhere:

**Edit backend/.env:**
```env
KAFKA_BROKERS=your-server-ip:9092
```

**Restart backend:**
```batch
uvicorn src.main:app --reload --port 8000
```

---

## Verification

### Check if Kafka is running

**Windows PowerShell:**
```powershell
netstat -ano | findstr :9092
```

**Linux/Mac:**
```bash
lsof -i :9092
```

### Check Docker containers

```bash
docker ps | grep kafka
```

Should show:
- kafka container running on 9092
- zookeeper container running on 2181

### Test Kafka connection

```bash
cd backend
python test_kafka.py
```

---

## Backend Status Without Kafka

### ✅ What STILL Works

- API Server (all endpoints)
- Authentication (JWT)
- Task CRUD operations
- Database operations
- Swagger documentation
- API testing

### ⚠️ What's Limited

- Real-time event processing
- Async task queue
- Event audit trail
- Kafka topics

**But don't worry**: Events are saved to database and will be retried when Kafka comes online.

---

## Complete Docker Setup

To start everything:

**Terminal 1: Start all services**
```batch
cd G:\Hackathon-2\phase-V
docker-compose up
```

**Terminal 2: Start backend**
```batch
cd backend
source .venv/bin/activate  (or .venv\Scripts\activate on Windows)
uvicorn src.main:app --reload --port 8000
```

**Terminal 3: Start frontend (optional)**
```batch
cd frontend
npm run dev
```

---

## Expected Logs

### Without Kafka (Current)
```
2026-03-04 07:40:16,101 - aiokafka - ERROR - Unable connect to "localhost:9092"
2026-03-04 07:40:16,102 - src.core.kafka - WARNING - Kafka consumer connection attempt 1/3 failed
```

### With Kafka (What you want)
```
INFO - Kafka broker connection established
INFO - Kafka consumer connection successful
INFO - Event consumer ready and listening
```

---

## Docker Compose Configuration

Your docker-compose.yml has:

```yaml
kafka:
  image: confluentinc/cp-kafka:7.5.0
  ports:
    - "9092:9092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    # ... other config
```

**To start only Kafka services:**
```bash
docker-compose up -d zookeeper kafka
```

**To check logs:**
```bash
docker-compose logs kafka
```

---

## Troubleshooting

### Issue: "Port 9092 already in use"
**Solution**:
```bash
# Kill the process on port 9092
netstat -ano | findstr :9092
taskkill /PID <PID> /F
```

### Issue: "Connection timeout"
**Solution**:
- Wait 60 seconds for Kafka to start
- Check: `docker ps | grep kafka`
- Restart: `docker-compose restart kafka`

### Issue: "Zookeeper not found"
**Solution**:
```bash
docker-compose up -d zookeeper
# Wait 30 seconds
docker-compose up -d kafka
```

### Issue: "Still getting Kafka errors"
**Solution**:
- Stop all: `docker-compose down`
- Restart: `docker-compose up`
- Clear volumes: `docker-compose down -v && docker-compose up`

---

## Current Status

**Right Now:**
- ✅ Backend is running and accessible
- ✅ API works fine
- ✅ Database is connected
- ⚠️ Kafka is not connected (but not critical)

**Recommendation:**
- Proceed with development
- Start Kafka when you need event streaming
- Events will queue up for processing

---

## Summary

| Aspect | Current | With Kafka |
|--------|---------|-----------|
| API | ✅ Works | ✅ Works |
| Database | ✅ Works | ✅ Works |
| Events | ⚠️ Queued | ✅ Streamed |
| Real-time | ❌ No | ✅ Yes |
| Testing | ✅ Full | ✅ Full |

**You can safely use the API now. Kafka is optional for this phase.**
