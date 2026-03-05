# Quick Start: Advanced Task Management Features

**Feature**: 005-advanced-features-kafka-dapr
**Version**: 2.0.0
**Last Updated**: 2026-02-23

**Features Included**:
1. Due Dates, Priorities, and Tags
2. Recurring Tasks (Daily, Weekly, Monthly, Yearly)
3. Reminders with In-App Notifications
4. Full-Text Search and Advanced Filtering
5. Multi-Criteria Sorting with Persistence

---

## Overview

This guide walks you through setting up and running the advanced task management features including due dates, priorities, tags, reminders, recurring tasks, search, filter, and sort functionality with event-driven architecture.

---

## Prerequisites

### Required Software

- **Docker Desktop** (for containerized deployment)
- **Docker Compose** v2.0+ (included with Docker Desktop)
- **Git** (for source control)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)

### Optional Tools

- **Dapr CLI** (for local Dapr development)
- **Kafka CLI tools** (for monitoring topics)
- **PostgreSQL client** (for database inspection)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
│                   Port 3000                         │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                 │
│                   Port 8000                         │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ Kafka Client │  │  Dapr Client │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────┬───────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│   PostgreSQL    │       │  Kafka + ZK     │
│   Port 5432     │       │  Port 9092      │
└─────────────────┘       └─────────────────┘
```

---

## Quick Start (Docker Compose)

### Step 1: Clone and Navigate

```bash
cd /path/to/Hackathon-2/phase-V
```

### Step 2: Configure Environment Variables

Create `.env` file in project root:

```bash
# JWT Configuration
JWT_SECRET=your-super-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI Configuration (for AI agent)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Frontend Configuration
BETTER_AUTH_SECRET=your-better-auth-secret-here
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Kafka Configuration
KAFKA_BROKERS=kafka:9092
KAFKA_TOPIC_EVENTS=task-events

# Dapr Configuration (optional for advanced features)
DAPR_HTTP_ENDPOINT=http://dapr:3500
```

### Step 3: Update Docker Compose

The `docker-compose.yml` has been extended with Kafka and Zookeeper services:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: todo-postgres
    environment:
      POSTGRES_USER: todouser
      POSTGRES_PASSWORD: todopassword
      POSTGRES_DB: tododb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U todouser -d tododb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - todo-network

  # Zookeeper (required for Kafka)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: todo-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - todo-network

  # Kafka Broker
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: todo-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    networks:
      - todo-network

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: todo-backend
    environment:
      DATABASE_URL: postgresql://todouser:todopassword@postgres:5432/tododb?sslmode=disable
      JWT_SECRET: ${JWT_SECRET}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      KAFKA_BROKERS: kafka:29092
      KAFKA_TOPIC_EVENTS: task-events
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_started
    networks:
      - todo-network
    restart: unless-stopped

  # Frontend Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: todo-frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      BETTER_AUTH_SECRET: ${BETTER_AUTH_SECRET}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - todo-network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local

networks:
  todo-network:
    driver: bridge
```

### Step 4: Build and Start Services

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Step 5: Verify Services

```bash
# Check running containers
docker-compose ps

# Expected output:
# NAME                STATUS                   PORTS
# todo-backend        Up (healthy)             0.0.0.0:8000->8000/tcp
# todo-frontend       Up (healthy)             0.0.0.0:3000->3000/tcp
# todo-postgres       Up (healthy)             0.0.0.0:5432->5432/tcp
# todo-kafka          Up                       0.0.0.0:9092->9092/tcp
# todo-zookeeper      Up                       2181/tcp
```

### Step 6: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## Local Development Setup

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for advanced features
pip install aiokafka python-dateutil dapr-ext-fastapi

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# (see Environment Variables section below)

# Run database migrations
# (Alembic will be configured for new entities)
alembic upgrade head

# Start backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-key-here
EOF

# Start development server
npm run dev
```

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://todouser:todopassword@localhost:5432/tododb?sslmode=disable

# JWT Authentication
JWT_SECRET=your-super-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI (for AI agent)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
AGENT_TIMEOUT=30
CONTEXT_WINDOW_SIZE=20

# Kafka Configuration
KAFKA_BROKERS=localhost:9092
KAFKA_TOPIC_EVENTS=task-events
KAFKA_CONSUMER_GROUP=task-service-group

# Dapr Configuration (optional)
DAPR_HTTP_ENDPOINT=http://localhost:3500

# Feature Flags
ENABLE_REMINDERS=true
ENABLE_RECURRENCE=true
ENABLE_EVENT_SOURCING=true
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-auth-secret-here
BETTER_AUTH_URL=http://localhost:3000
```

---

## Database Migration

### Run Migrations

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate

# Run migrations
alembic upgrade head
```

### Migration Verification

```bash
# Connect to PostgreSQL
docker exec -it todo-postgres psql -U todouser -d tododb

# List tables
\dt

# Verify new tables exist:
# - tag
# - task_tag
# - reminder
# - recurrence_rule
# - event_log
```

---

## Testing the Features

### 1. Create a Tag

```bash
curl -X POST http://localhost:8000/api/tags \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "work",
    "color": "#3B82F6"
  }'
```

### 2. Create a Task with Due Date and Priority

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete quarterly report",
    "description": "Finish Q1 financial report",
    "due_date": "2026-02-28T23:59:59Z",
    "priority": "high",
    "tag_ids": [1]
  }'
```

### 3. Search and Filter Tasks

```bash
# Search by keyword
curl -X GET "http://localhost:8000/api/tasks?q=report" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Filter by priority
curl -X GET "http://localhost:8000/api/tasks?priority=high" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Filter by status (overdue)
curl -X GET "http://localhost:8000/api/tasks?status=overdue" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Sort by due date
curl -X GET "http://localhost:8000/api/tasks?sort_by=due_date&sort_order=asc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Set a Reminder

```bash
curl -X POST http://localhost:8000/api/reminders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "trigger_time": "2026-02-28T09:00:00Z"
  }'
```

### 5. Set Recurrence

```bash
curl -X POST http://localhost:8000/api/tasks/1/recurrence \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "weekly",
    "interval": 1,
    "start_date": "2026-02-23"
  }'
```

---

## Kafka Monitoring

### View Topics

```bash
# List Kafka topics
docker exec -it todo-kafka kafka-topics --list --bootstrap-server localhost:9092

# Expected output:
# task-events
# reminder-events
# recurrence-events
```

### Consume Events

```bash
# Consume task events
docker exec -it todo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic task-events \
  --from-beginning
```

---

## Troubleshooting

### Backend Won't Start

**Issue**: Database connection error

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Verify DATABASE_URL is correct
cat backend/.env | grep DATABASE_URL
```

### Kafka Connection Error

**Issue**: Cannot connect to Kafka broker

```bash
# Check if Kafka is running
docker-compose ps kafka

# View Kafka logs
docker-compose logs kafka

# Verify KAFKA_BROKERS environment variable
cat backend/.env | grep KAFKA_BROKERS
```

### Migration Failures

**Issue**: Table already exists

```bash
# Check current migration status
alembic current

# If needed, stamp head (mark all migrations as applied)
alembic stamp head

# Or downgrade and re-upgrade
alembic downgrade base
alembic upgrade head
```

### Frontend Build Errors

**Issue**: Module not found

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Next.js cache
rm -rf .next

# Rebuild
npm run build
```

---

## Performance Tuning

### PostgreSQL Indexes

Verify indexes are created:

```sql
-- Connect to database
\c tododb

-- List indexes
\di

-- Verify task indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'todo';
```

### Kafka Performance

For high-throughput scenarios:

```bash
# Increase Kafka partitions (requires topic recreation)
docker exec -it todo-kafka kafka-topics \
  --alter --topic task-events \
  --partitions 10 \
  --bootstrap-server localhost:9092
```

---

## Next Steps

1. **Explore API Documentation**: Visit http://localhost:8000/docs
2. **Test Features**: Use the curl examples above
3. **Review Data Model**: See `data-model.md` for entity details
4. **Review API Contracts**: See `contracts/` for endpoint specifications
5. **Run Tests**: `pytest backend/tests/` for backend tests

---

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f <service>`
2. Review API documentation: http://localhost:8000/docs
3. Check feature specification: `spec.md`
4. Review implementation plan: `plan.md`

---

## Production Deployment

For production deployment:

1. **Use managed Kafka**: Confluent Cloud or AWS MSK
2. **Use managed PostgreSQL**: AWS RDS, Google Cloud SQL, or Azure Database
3. **Enable SSL/TLS**: For all service communication
4. **Configure secrets management**: AWS Secrets Manager, HashiCorp Vault
5. **Set up monitoring**: Prometheus, Grafana, ELK stack
6. **Enable autoscaling**: Kubernetes HPA for backend services
7. **Configure backups**: Daily database backups, Kafka topic replication

See `K8S_DEPLOYMENT_SUMMARY.md` for Kubernetes deployment instructions.
