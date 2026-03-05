# 🚀 Hackathon Phase V - Quick Start Guide

## ⚡ 5-Minute Setup (Windows)

### Step 1: Start Kafka (30 seconds)
```bash
# Double-click or run in terminal:
start-kafka.bat
```
**Wait 30 seconds** for Kafka to be ready.

### Step 2: Configure Backend (1 minute)
```bash
cd backend
copy .env.example .env
notepad .env
```

**Minimum required settings:**
```env
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
JWT_SECRET=your-secret-key-min-32-chars-hackathon-2026
OPENAI_API_KEY=sk-proj-your-key-here
KAFKA_BROKERS=localhost:9092
```

### Step 3: Install Dependencies (2 minutes)
```bash
pip install -r requirements.txt
```

### Step 4: Start Backend (1 minute)
```bash
cd ..
start-backend.bat
```

### Step 5: Verify (30 seconds)
Open these URLs:
- **API Docs**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:8080

Look for these logs:
```
✅ Kafka producer connected to localhost:9092
✅ Kafka consumer connected to localhost:9092
✅ Database tables created successfully
```

---

## 🎯 What Was Fixed

### 1. Kafka Connection Issues
**Before:** Hard failure when Kafka unavailable
**After:** Graceful degradation with auto-reconnection

### 2. Event Consumer Crashes
**Before:** NoneType errors crashed consumer loop
**After:** Validates events, handles None values, auto-reconnects

### 3. Event Producer Failures
**Before:** API calls failed when Kafka down
**After:** Events saved to DB, processed when Kafka available

### 4. No Retry Logic
**Before:** Failed events lost forever
**After:** Background task retries every 60 seconds

---

## 🧪 Test Your Setup

### Test 1: Basic Connectivity
```bash
cd backend
python test_kafka.py
```

Expected output:
```
✅ Producer connected successfully
✅ Consumer connected successfully
✅ Test event sent successfully
```

### Test 2: Create Task via API
1. Go to http://localhost:8000/docs
2. Click "Authorize" and login
3. POST to `/api/todos` with:
```json
{
  "title": "Test Kafka Integration",
  "priority": "high"
}
```
4. Check Kafka UI: http://localhost:8080/ui/clusters/local/topics/task-events
5. Should see event with `event_type: "task.created"`

### Test 3: Fault Tolerance
```bash
# 1. Stop Kafka
stop-kafka.bat

# 2. Create task via API (should still work!)

# 3. Check backend logs - should see:
# "⚠️ Kafka unavailable, skipping event: task.created"
# "Event stored in EventLog: task.created"

# 4. Start Kafka
start-kafka.bat

# 5. Wait 60 seconds - backend will retry unprocessed events
# Should see: "Successfully retried X events"
```

---

## 🐛 Troubleshooting

### "Unable to connect to localhost:9092"
**Solution:** Wait 30-60 seconds after starting Kafka
```bash
docker-compose -f docker-compose.kafka.yml ps
```
All services should show "healthy"

### "NoneType has no attribute 'check_errors'"
**Solution:** Already fixed! Update your code:
```bash
git pull origin 005-advanced-features-kafka-dapr
```

### Backend starts but shows Kafka warnings
**This is NORMAL!** Backend runs in degraded mode:
- ✅ API works
- ✅ Events saved to database
- ⚠️ Real-time processing disabled
- 🔄 Will auto-reconnect when Kafka available

### Port conflicts
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 9092
docker-compose -f docker-compose.kafka.yml down
```

---

## 📊 Monitoring

### View Kafka Topics
http://localhost:8080/ui/clusters/local/topics/task-events

### View Backend Logs
Look for these indicators:
- `✅` = Success
- `⚠️` = Warning (degraded mode)
- `❌` = Error (will retry)

### Check Event Processing
```bash
# View Kafka logs
docker logs hackathon-kafka -f

# View consumer logs
# Backend logs show: "Event received: task.created for user X"
```

---

## 🎓 Architecture

```
API Request → EventProducer → [EventLog DB] → Kafka → EventConsumer
                                    ↓                        ↓
                              (Guaranteed)            (Async Processing)
```

**Key Features:**
1. **Dual Write**: Events saved to DB + Kafka
2. **Graceful Degradation**: Works without Kafka
3. **Auto Retry**: Background task retries failed events
4. **Auto Reconnect**: Reconnects when Kafka available

---

## 🎉 Success Checklist

- [ ] Docker Desktop running
- [ ] Kafka containers healthy
- [ ] Kafka UI accessible (http://localhost:8080)
- [ ] Backend starts without errors
- [ ] Logs show "✅ Kafka producer connected"
- [ ] Logs show "✅ Kafka consumer connected"
- [ ] Can create tasks via API
- [ ] Events visible in Kafka UI

**All checked? You're ready for the hackathon demo! 🚀**

---

## 📞 Quick Commands

```bash
# Start everything
start-backend.bat

# Stop Kafka
stop-kafka.bat

# View logs
docker-compose -f docker-compose.kafka.yml logs -f

# Test Kafka
cd backend && python test_kafka.py

# Restart everything
stop-kafka.bat
start-kafka.bat
cd backend && uvicorn src.main:app --reload --port 8000
```

---

## 🔥 Demo Tips

1. **Show Kafka UI**: Impress judges with real-time event monitoring
2. **Show Fault Tolerance**: Stop Kafka, create task, restart Kafka
3. **Show Auto-Recovery**: Events automatically processed when Kafka returns
4. **Show Logs**: Clean, emoji-based status indicators

**Pro Tip:** Keep Kafka UI open during demo to show events flowing in real-time!
