# MVP Deployment Guide

**Version**: 1.0.0  
**Date**: 2026-02-23  
**Feature**: Advanced Task Management with Due Dates, Priorities, and Tags  
**Branch**: `005-advanced-features-kafka-dapr`

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Deployment](#local-development-deployment)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Software

- **Docker Desktop** v2.0+ (or Docker Engine + Docker Compose)
- **Git** for source control
- **PostgreSQL client** (psql) for database management
- **Node.js 18+** (for frontend development)
- **Python 3.11+** (for backend development)

### Required Accounts

- **OpenAI API Key** (for AI agent features)
- **Docker Hub** account (for pulling images)
- **Domain name** (for production deployment)

### System Requirements

- **Minimum**: 4GB RAM, 2 CPU cores, 10GB disk space
- **Recommended**: 8GB RAM, 4 CPU cores, 20GB disk space
- **Ports**: 3000 (frontend), 8000 (backend), 5432 (postgres), 9092 (kafka)

---

## Local Development Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/Huzafi/Hackathon-2.git
cd Hackathon-2/phase-V
git checkout 005-advanced-features-kafka-dapr
```

### Step 2: Configure Environment Variables

Create `.env` file in project root:

```bash
# Copy example files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local 2>/dev/null || true
```

Edit `.env` with your values:

```bash
# JWT Configuration
JWT_SECRET=your-super-secret-key-min-32-characters-long-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Frontend Configuration
BETTER_AUTH_SECRET=your-better-auth-secret-here
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Kafka Configuration
KAFKA_BROKERS=localhost:9092
KAFKA_TOPIC_EVENTS=task-events
KAFKA_CONSUMER_GROUP=task-service-group

# Dapr Configuration
DAPR_HTTP_ENDPOINT=http://localhost:3500

# Feature Flags
ENABLE_REMINDERS=true
ENABLE_RECURRENCE=true
ENABLE_EVENT_SOURCING=true
```

### Step 3: Start All Services

```bash
# Build and start all containers
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

**Expected Output**:
```
NAME                STATUS                   PORTS
todo-backend        Up (healthy)             0.0.0.0:8000->8000/tcp
todo-frontend       Up (healthy)             0.0.0.0:3000->3000/tcp
todo-postgres       Up (healthy)             0.0.0.0:5432->5432/tcp
todo-kafka          Up                       0.0.0.0:9092->9092/tcp
todo-zookeeper      Up                       2181/tcp
```

### Step 4: Run Database Migrations

```bash
# Run migrations
docker-compose exec backend python migrate.py

# Check migration status
docker-compose exec backend python migrate.py status
```

**Expected Output**:
```
✓ Applied migration: 001_add_event_driven_architecture.sql
✓ Applied migration: 002_add_advanced_task_features.sql
✓ Successfully applied 2/2 migrations
```

### Step 5: Verify Deployment

```bash
# Test backend health
curl http://localhost:8000/

# Expected response:
# {"message":"Todo Backend API","status":"running","docs":"/docs","redoc":"/redoc"}

# Test frontend
curl http://localhost:3000/

# Open in browser
open http://localhost:3000  # macOS
xdg-open http://localhost:3000  # Linux
start http://localhost:3000  # Windows
```

### Step 6: Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Step 7: Create Test User and Tasks

1. Open http://localhost:3000
2. Click "Sign Up"
3. Create account with email and password
4. Create tasks with:
   - Due dates
   - Priority levels (high/medium/low)
   - Tags (create tags first in tag management)

---

## Staging Deployment

### Step 1: Prepare Staging Environment

```bash
# Ensure you're on the correct branch
git checkout 005-advanced-features-kafka-dapr
git pull origin 005-advanced-features-kafka-dapr
```

### Step 2: Configure Staging Environment

Create staging-specific `.env.staging`:

```bash
# Use production-like values but with staging prefixes
JWT_SECRET=staging-secret-key-change-in-production
DATABASE_URL=postgresql://staging_user:staging_password@staging-db:5432/staging_db
OPENAI_API_KEY=sk-staging-api-key
NEXT_PUBLIC_API_URL=https://staging-api.yourdomain.com
BETTER_AUTH_URL=https://staging.yourdomain.com
```

### Step 3: Deploy to Staging Server

```bash
# SSH to staging server
ssh user@staging-server

# Navigate to app directory
cd /opt/todo-app

# Pull latest code
git pull origin 005-advanced-features-kafka-dapr

# Stop existing services
docker-compose down

# Build new images
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend python migrate.py
```

### Step 4: Verify Staging Deployment

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f backend frontend

# Test endpoints
curl https://staging-api.yourdomain.com/
curl https://staging.yourdomain.com/
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (backend and frontend)
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Database backups configured
- [ ] Monitoring and alerting configured
- [ ] SSL/TLS certificates ready
- [ ] Domain DNS configured
- [ ] Environment variables secured (use secrets management)
- [ ] Rollback plan documented and tested

### Step 1: Security Hardening

Update `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - todo-network
    # Restrict to internal network only
    # No ports exposed externally

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: ${DATABASE_URL}
      JWT_SECRET: ${JWT_SECRET}
      # Use secrets management in production
      # AWS Secrets Manager, HashiCorp Vault, etc.
    networks:
      - todo-network
      - web-network
    # Deploy behind reverse proxy (nginx, traefik)
    restart: unless-stopped
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    networks:
      - web-network
    restart: unless-stopped
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

networks:
  todo-network:
    internal: true  # Backend services only
  web-network:
    driver: bridge  # Public-facing

volumes:
  postgres_data:
    driver: local
```

### Step 2: Configure Reverse Proxy (nginx)

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    return 301 https://yourdomain.com$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 3: Deploy to Production

```bash
# SSH to production server
ssh user@production-server

# Navigate to app directory
cd /opt/todo-app

# Pull latest code
git pull origin 005-advanced-features-kafka-dapr

# Load production environment variables
source .env.production

# Stop existing services
docker-compose down

# Build production images
docker-compose build --no-cache

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend python migrate.py

# Verify deployment
docker-compose ps
docker-compose logs -f
```

### Step 4: Configure Monitoring

**Recommended monitoring setup**:

1. **Application Monitoring**:
   - Prometheus + Grafana for metrics
   - ELK Stack (Elasticsearch, Logstash, Kibana) for logs
   - Jaeger or Zipkin for distributed tracing

2. **Infrastructure Monitoring**:
   - CPU, memory, disk usage
   - Network I/O
   - Container health checks

3. **Business Metrics**:
   - User registrations
   - Task creation rate
   - API response times
   - Error rates

### Step 5: Configure Backups

**Database Backup Script** (`backup.sh`):

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/todo_backup_$DATE.sql.gz"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
docker-compose exec -T postgres pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip > $BACKUP_FILE

# Verify backup
if [ -f $BACKUP_FILE ] && [ -s $BACKUP_FILE ]; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Remove old backups
    find $BACKUP_DIR -name "todo_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Cleaned up backups older than $RETENTION_DAYS days"
else
    echo "Backup failed!"
    exit 1
fi
```

**Add to crontab**:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/todo-app/backup.sh >> /var/log/todo-backup.log 2>&1
```

---

## Post-Deployment Verification

### Health Checks

```bash
# Backend health
curl -f http://localhost:8000/ || exit 1

# Frontend health
curl -f http://localhost:3000/ || exit 1

# Database connection
docker-compose exec postgres pg_isready -U $POSTGRES_USER -d $POSTGRES_DB

# Kafka connection
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Functional Testing

```bash
# 1. Create test user via API
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# 2. Sign in and get JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}' | jq -r '.access_token')

# 3. Create a tag
curl -X POST http://localhost:8000/api/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","color":"#3B82F6"}'

# 4. Create a task with due date and priority
curl -X POST http://localhost:8000/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Test Task",
    "description":"Testing MVP deployment",
    "due_date":"2026-03-01T23:59:59Z",
    "priority":"high"
  }'

# 5. List tasks
curl -X GET "http://localhost:8000/api/todos?priority=high" \
  -H "Authorization: Bearer $TOKEN"

# 6. Verify event logging
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT COUNT(*) FROM event_log;"
```

### Performance Testing

```bash
# Install k6 for load testing
# https://k6.io/docs/getting-started/installation/

# Create load test script (load-test.js)
export default function () {
  http.get('http://localhost:8000/api/todos');
}

# Run load test
k6 run --vus 10 --duration 30s load-test.js

# Expected: All requests complete with <500ms response time
```

---

## Troubleshooting

### Common Issues

#### Backend Won't Start

**Symptom**: Container exits immediately

```bash
# Check logs
docker-compose logs backend

# Common causes:
# 1. Database not ready
docker-compose logs postgres
# Solution: Wait for postgres health check to pass

# 2. Missing environment variables
docker-compose exec backend env | grep -E "DATABASE_URL|JWT_SECRET"
# Solution: Add missing variables to .env

# 3. Database migration failed
docker-compose exec backend python migrate.py status
# Solution: Run migrations manually
```

#### Frontend Can't Connect to Backend

**Symptom**: Network errors in browser console

```bash
# Verify backend is accessible
curl http://localhost:8000/

# Check CORS configuration
docker-compose exec backend grep -A 5 "CORS" src/main.py

# Verify NEXT_PUBLIC_API_URL
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL
# Solution: Update .env with correct URL
```

#### Kafka Connection Failed

**Symptom**: Event emission errors in logs

```bash
# Check Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Verify broker configuration
docker-compose exec kafka kafka-configs --bootstrap-server localhost:9092 --describe --broker 1

# Solution: Ensure KAFKA_ADVERTISED_LISTENERS is correctly configured
```

#### Database Migration Failed

**Symptom**: Tables missing or schema outdated

```bash
# Check migration status
docker-compose exec backend python migrate.py status

# Rollback and re-run (if needed)
docker-compose exec backend python migrate.py rollback
docker-compose exec backend python migrate.py

# Manual verification
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "\dt"  # List tables
```

---

## Rollback Procedures

### Quick Rollback (Last Deployment)

```bash
# SSH to server
ssh user@production-server

# Navigate to app directory
cd /opt/todo-app

# Revert to previous git commit
git revert HEAD --no-edit

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Verify rollback
docker-compose ps
curl http://localhost:8000/
```

### Full Rollback to Previous Version

```bash
# Checkout previous stable version
git checkout <previous-tag-or-commit>

# Restore database from backup
# 1. Find backup file
ls -lt /backups/postgres/ | head

# 2. Restore
gunzip -c /backups/postgres/todo_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:8000/
```

### Emergency Rollback (Database Corruption)

```bash
# 1. Stop all services
docker-compose down

# 2. Restore from latest backup
LATEST_BACKUP=$(ls -t /backups/postgres/*.sql.gz | head -1)
gunzip -c $LATEST_BACKUP | \
  docker run --rm -i \
    -e PGPASSWORD=$POSTGRES_PASSWORD \
    postgres:16-alpine \
    psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB

# 3. Start services with previous known-good image
docker-compose up -d

# 4. Verify data integrity
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT COUNT(*) FROM users;"
  -c "SELECT COUNT(*) FROM todos;"
```

---

## Support and Maintenance

### Regular Maintenance Tasks

**Daily**:
- [ ] Check error logs
- [ ] Verify backups completed
- [ ] Monitor disk space

**Weekly**:
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review user feedback

**Monthly**:
- [ ] Apply security patches
- [ ] Performance optimization
- [ ] Database optimization (VACUUM ANALYZE)

### Contact and Support

- **GitHub Issues**: https://github.com/Huzafi/Hackathon-2/issues
- **Documentation**: https://github.com/Huzafi/Hackathon-2/tree/main/phase-V
- **Emergency Contact**: [Your contact information]

---

## Appendix: Environment Variables Reference

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/database
JWT_SECRET=your-secret-key-min-32-characters
OPENAI_API_KEY=sk-your-api-key

# Optional (with defaults)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
OPENAI_MODEL=gpt-4
AGENT_TIMEOUT=30
CONTEXT_WINDOW_SIZE=20
KAFKA_BROKERS=localhost:9092
KAFKA_TOPIC_EVENTS=task-events
KAFKA_CONSUMER_GROUP=task-service-group
DAPR_HTTP_ENDPOINT=http://localhost:3500
ENABLE_REMINDERS=true
ENABLE_RECURRENCE=true
ENABLE_EVENT_SOURCING=true
```

### Frontend (.env.local)

```bash
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-auth-secret
BETTER_AUTH_URL=http://localhost:3000

# Optional
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
```

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-02-23  
**Maintained By**: Development Team
