# Local Development Setup Guide

**Quick, Simple Setup Without Kafka and Dapr**

---

## Quick Start (3 Commands)

```bash
# 1. Copy environment template
cp .env.local.example .env.local

# 2. Start all services
./start-local.sh

# 3. Open browser
open http://localhost:3000  # macOS
xdg-open http://localhost:3000  # Linux
start http://localhost:3000  # Windows
```

That's it! Your application is running. 🎉

---

## What You Get

✅ **All Core Features**:
- Due dates, priorities, tags
- Recurring tasks (daily, weekly, monthly, yearly)
- Reminders (polling-based, checks every 60 seconds)
- Full-text search
- Advanced filtering
- Multi-criteria sorting

✅ **Services Running**:
- PostgreSQL 16 (database)
- FastAPI backend (port 8000)
- Next.js frontend (port 3000)

❌ **Not Included** (add later if needed):
- Kafka (event streaming)
- Dapr (distributed runtime)

---

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
- **Git** (for cloning repository)
- **Web Browser** (Chrome, Firefox, Edge, Safari)

**System Requirements**:
- 4GB RAM minimum (8GB recommended)
- 2 CPU cores minimum (4 recommended)
- 5GB disk space

---

## Step-by-Step Setup

### 1. Clone Repository (if not done)

```bash
git clone https://github.com/Huzafi/Hackathon-2.git
cd Hackathon-2/phase-V
```

### 2. Configure Environment

```bash
# Copy template
cp .env.local.example .env.local

# Edit with your values (optional - defaults work)
nano .env.local  # or use your preferred editor
```

**Required Variables**:
```bash
# JWT Secret (CHANGE THIS!)
# Generate with: openssl rand -base64 32
JWT_SECRET=your-random-32-character-secret-here

# OpenAI API Key (optional - for AI features)
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Start Services

```bash
# Start everything (runs migrations automatically)
./start-local.sh
```

**What happens**:
1. ✅ Creates `.env.local` if missing
2. ✅ Starts PostgreSQL
3. ✅ Runs database migrations
4. ✅ Starts backend API
5. ✅ Starts frontend web app
6. ✅ Waits for all services to be ready

### 4. Verify Services

```bash
# Check running containers
docker-compose -f docker-compose.local.yml ps

# Expected output:
# NAME                STATUS
# todo-backend        Up (healthy)
# todo-frontend       Up
# todo-postgres       Up (healthy)
```

### 5. Access Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Web application |
| **Backend** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI (test API) |
| **Database** | localhost:5432 | PostgreSQL (for debugging) |

---

## Create Your First User

1. Open http://localhost:3000
2. Click **"Sign Up"**
3. Enter email and password
4. Click **"Create Account"**
5. Start creating tasks!

---

## Useful Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose.local.yml logs -f

# Specific service
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend
docker-compose -f docker-compose.local.yml logs -f postgres
```

### Stop Services

```bash
# Stop (preserves data)
./stop-local.sh

# Or manually
docker-compose -f docker-compose.local.yml down
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.local.yml restart

# Restart specific service
docker-compose -f docker-compose.local.yml restart backend
```

### Rebuild

```bash
# Rebuild after code changes
docker-compose -f docker-compose.local.yml build

# Rebuild and restart
docker-compose -f docker-compose.local.yml up -d --build
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.local.yml exec postgres psql -U todouser -d tododb

# Run migrations manually
docker-compose -f docker-compose.local.yml exec backend python migrate.py

# Check migration status
docker-compose -f docker-compose.local.yml exec backend python migrate.py status
```

### Backend Shell

```bash
# Access backend container
docker-compose -f docker-compose.local.yml exec backend /bin/bash

# Run Python commands
docker-compose -f docker-compose.local.yml exec backend python -c "from src.core.database import get_session; print('DB connected!')"
```

### Frontend Shell

```bash
# Access frontend container
docker-compose -f docker-compose.local.yml exec frontend /bin/sh
```

---

## Troubleshooting

### Port Already in Use

**Error**: "Bind for 0.0.0.0:3000 failed: port is already allocated"

**Solution**:
```bash
# Find what's using the port
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Stop the conflicting service
# Or change the port in docker-compose.local.yml
```

### Database Connection Failed

**Error**: "could not connect to server"

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.local.yml ps postgres

# View PostgreSQL logs
docker-compose -f docker-compose.local.yml logs postgres

# Restart PostgreSQL
docker-compose -f docker-compose.local.yml restart postgres
```

### Backend Won't Start

**Error**: "Failed to bind to 0.0.0.0:8000"

**Solution**:
```bash
# Check logs
docker-compose -f docker-compose.local.yml logs backend

# Common issues:
# 1. Database not ready - wait for PostgreSQL health check
# 2. Missing environment variables - check .env.local
# 3. Port conflict - change port in docker-compose.local.yml
```

### Frontend Shows Blank Page

**Solution**:
```bash
# Check backend is accessible
curl http://localhost:8000/

# Expected: {"message":"Todo Backend API","status":"running",...}

# Check frontend logs
docker-compose -f docker-compose.local.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.local.yml build frontend
docker-compose -f docker-compose.local.yml restart frontend
```

### Migrations Failed

**Solution**:
```bash
# Run migrations manually
docker-compose -f docker-compose.local.yml exec backend python migrate.py

# Check status
docker-compose -f docker-compose.local.yml exec backend python migrate.py status

# If stuck, reset (WARNING: deletes all data!)
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

---

## Development Workflow

### Backend Changes

```bash
# Code changes auto-reload (uvicorn --reload enabled)
# Just save your files and refresh browser

# If not reloading, restart backend
docker-compose -f docker-compose.local.yml restart backend
```

### Frontend Changes

```bash
# Next.js has hot reload enabled
# Save files and see changes instantly

# If not reloading, rebuild
docker-compose -f docker-compose.local.yml build frontend
docker-compose -f docker-compose.local.yml restart frontend
```

### Database Schema Changes

```bash
# Create new migration
# (Use your preferred migration tool or write SQL directly)

# Apply migrations
docker-compose -f docker-compose.local.yml exec backend python migrate.py
```

---

## Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/

# Get API docs
open http://localhost:8000/docs

# Create test user
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# Sign in and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}' | jq -r '.access_token')

# Create task
curl -X POST http://localhost:8000/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test task","priority":"high"}'
```

### Test Frontend

1. Open http://localhost:3000
2. Create account
3. Create tasks with due dates, priorities, tags
4. Test search, filter, sort
5. Test recurring tasks
6. Test reminders

---

## Clean Up

### Stop and Remove Everything

```bash
# Stop services and remove data
docker-compose -f docker-compose.local.yml down -v

# Remove images (optional)
docker-compose -f docker-compose.local.yml down --rmi all

# Remove everything
docker system prune -a
```

### Reset Database Only

```bash
# Remove database volume
docker volume rm phase-V_postgres_data

# Or remove all volumes
docker-compose -f docker-compose.local.yml down -v
```

---

## Next Steps

1. ✅ **Create your first task** - http://localhost:3000
2. ✅ **Explore features** - due dates, priorities, tags, recurring, reminders
3. ✅ **Test API** - http://localhost:8000/docs
4. ✅ **Read documentation** - See docs/ folder
5. ✅ **Start developing** - Add your own features!

---

## Getting Help

- **Documentation**: See `PROJECT_COMPLETE.md` for full overview
- **API Docs**: http://localhost:8000/docs
- **Issues**: https://github.com/Huzafi/Hackathon-2/issues
- **Logs**: `docker-compose -f docker-compose.local.yml logs -f`

---

**Happy Coding!** 🚀

**Document Version**: 1.0.0  
**Last Updated**: 2026-02-23
