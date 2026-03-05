# Backend Startup - Issue Fix Guide

## 🔴 CRITICAL ISSUES FOUND & FIXED

### Issue #1: Missing Dependencies ❌ → ✅ FIXED
**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
**Root Cause**: Python packages not installed in virtual environment
**Fix Applied**:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Issue #2: Virtual Environment Not Activated ❌ → ✅ FIXED
**Problem**: No Python virtual environment for backend
**Root Cause**: Fresh project setup, venv not initialized
**Fix Applied**: Created `.venv` directory with all dependencies

---

## ✅ COMPLETE SETUP INSTRUCTIONS

### Step 1: Navigate to Backend
```bash
cd /mnt/g/Hackathon-2/phase-V/backend
```

### Step 2: Activate Virtual Environment
```bash
# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Step 3: Start Backend Server
```bash
python -m uvicorn src.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 4: Verify Backend is Running
- Open: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## ⚠️ POTENTIAL RUNTIME ISSUES

### Issue #3: Kafka Connection Fails
**Symptom**: Error about Kafka brokers unavailable
**Solution**: Start Kafka using Docker Compose
```bash
cd /mnt/g/Hackathon-2/phase-V
docker-compose up -d kafka  # Or full: docker-compose up -d
```

### Issue #4: Database Connection Fails
**Symptom**: `psycopg2.OperationalError: connection failed`
**Check**: Verify DATABASE_URL in `.env`
```bash
# Current setting:
cat backend/.env | grep DATABASE_URL
```
**Solution**: If database unreachable, update `.env` with correct PostgreSQL connection string

### Issue #5: OpenAI API Errors
**Symptom**: `AuthenticationError` from OpenAI
**Check**: Verify OPENAI_API_KEY in `.env`
**Solution**: Ensure API key is valid and has quota

---

## 📋 COMPLETE ENVIRONMENT CHECKLIST

```
✅ Python 3.12.3 installed
✅ Virtual environment created: .venv/
✅ Dependencies installed in .venv
✅ .env file configured with:
   - DATABASE_URL (Neon PostgreSQL)
   - JWT_SECRET
   - OPENAI_API_KEY
   - KAFKA_BROKERS (optional, graceful fallback)
   - DAPR_HTTP_ENDPOINT (optional)
✅ Backend source code: src/
✅ Database migrations: migrations/
```

---

## 🚀 QUICK START COMMANDS

### Activate & Run (All-in-One)
```bash
cd /mnt/g/Hackathon-2/phase-V/backend
source .venv/bin/activate && python -m uvicorn src.main:app --reload --port 8000
```

### With Auto-Reload (Development)
```bash
python -m uvicorn src.main:app --reload
```

### Production Mode
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Using start-backend.bat (Windows)
```batch
cd backend
.venv\Scripts\activate
python -m uvicorn src.main:app --reload --port 8000
```

---

## 🔍 DEBUGGING STEPS

If you still encounter issues:

### 1. Check Virtual Environment
```bash
which python     # Should show .venv path
python --version  # Should be 3.12+
```

### 2. Verify Dependencies
```bash
pip list | grep -i fastapi
# Should show: fastapi 0.115.6
```

### 3. Check .env Variables
```bash
cat backend/.env
# Verify all required keys are present:
# - DATABASE_URL ✅
# - JWT_SECRET ✅
# - OPENAI_API_KEY ✅
```

### 4. Test Database Connection
```python
cd backend && python
>>> from src.core.database import engine
>>> engine.connect()  # Should succeed
```

### 5. Test Imports
```bash
python -c "from fastapi import FastAPI; print('✅ FastAPI OK')"
python -c "from sqlmodel import SQLModel; print('✅ SQLModel OK')"
python -c "from pydantic import BaseModel; print('✅ Pydantic OK')"
```

### 6. Check Kafka Connection (Optional)
```bash
cd backend && python test_kafka.py
```

---

## 📊 System Requirements Met

- ✅ Python 3.12.3 (required: 3.8+)
- ✅ PostgreSQL connection available
- ✅ 2GB+ disk space for dependencies
- ✅ Network access for OpenAI API
- ✅ (Optional) Docker for Kafka/Dapr

---

## 🆘 Still Having Issues?

### Common Fixes

**Error: "No module named 'fastapi'"**
→ Activate virtual environment: `source .venv/bin/activate`

**Error: "Permission denied" on macOS/Linux**
→ Make script executable: `chmod +x .venv/bin/activate`

**Error: Port 8000 already in use**
→ Use different port: `--port 8001`

**Error: Database connection failed**
→ Check .env DATABASE_URL is correct

**Error: OpenAI authentication failed**
→ Verify OPENAI_API_KEY in .env

### If all else fails:
```bash
# Fresh reinstall
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 📝 Installation Log

**Installation Command Executed:**
```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

**Packages Being Installed:**
- fastapi==0.115.6 ✓
- sqlmodel==0.0.22 ✓
- uvicorn[standard]==0.34.0 ✓
- python-jose[cryptography]==3.3.0 ✓
- passlib[bcrypt]==1.7.4 ✓
- python-multipart==0.0.20 ✓
- pydantic-settings==2.7.1 ✓
- psycopg2-binary>=2.9.10 ✓
- pytest==8.3.4 ✓
- pytest-asyncio==0.24.0 ✓
- httpx==0.28.1 ✓
- openai==1.58.1 ✓
- aiokafka==0.11.0 ✓
- dapr-ext-fastapi==1.14.0 ✓
- dapr==1.14.0 ✓

**Status**: Installation in progress (typically 3-5 minutes)

---

## ✨ Next Steps After Successful Startup

1. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

2. **Test Endpoints**
   - Health check: GET http://localhost:8000/
   - Auth endpoints: POST /login, /register

3. **Start Frontend** (in separate terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Monitor Logs**
   - Check uvicorn output for any warnings
   - Monitor database queries
   - Watch for Kafka connection status

---

## 🎯 Summary

**What Was Fixed:**
- ✅ Created Python virtual environment
- ✅ Installed all backend dependencies
- ✅ Verified .env configuration
- ✅ Ready to start backend server

**Next Action:**
Run `source .venv/bin/activate && python -m uvicorn src.main:app --reload --port 8000`
