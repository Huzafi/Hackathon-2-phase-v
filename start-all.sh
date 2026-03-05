#!/bin/bash

# Complete Kafka & Dapr Stack Startup Script for Linux/Mac

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Event-Driven Architecture Stack Startup                    ║"
echo "║     Kafka + Dapr + PostgreSQL + Backend + Frontend             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ ERROR: Docker is not running!"
    echo ""
    echo "Please start Docker:"
    echo "  sudo systemctl start docker    # Linux"
    echo "  open -a Docker                 # Mac"
    echo ""
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ ERROR: Docker Compose is not available!"
    exit 1
fi

echo "✅ Docker Compose is available"
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

echo "📍 Current Directory: $(pwd)"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERROR: docker-compose.yml not found!"
    exit 1
fi

echo "✅ docker-compose.yml found"
echo ""

echo "🔍 Checking for existing containers..."
docker-compose ps
echo ""

echo "🚀 Starting complete stack with Kafka & Dapr..."
echo ""
echo "Services that will start:"
echo "  • PostgreSQL (Database) - Port 5432"
echo "  • Zookeeper (Kafka Coordination) - Port 2181"
echo "  • Kafka (Event Streaming) - Port 9092"
echo "  • Kafka UI (Monitoring) - Port 8080"
echo "  • Redis (State Store) - Port 6379"
echo "  • Backend (FastAPI) - Port 8000"
echo "  • Dapr Sidecar - Port 3500, 50001"
echo "  • Frontend (Next.js) - Port 3000"
echo ""

echo "⏱️  Estimated startup time: 2-3 minutes (first run may take longer)"
echo ""

# Start Docker Compose
docker-compose up

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Docker Compose failed to start!"
    echo ""
    echo "Try these troubleshooting steps:"
    echo "  1. Check Docker is running: docker ps"
    echo "  2. View logs: docker-compose logs"
    echo "  3. Clean up: docker-compose down -v"
    echo "  4. Rebuild: docker-compose up --build"
    echo ""
    exit 1
fi

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📚 Access your services:"
echo "  • Backend API:  http://localhost:8000"
echo "  • API Docs:     http://localhost:8000/docs"
echo "  • Kafka UI:     http://localhost:8080"
echo "  • Frontend:     http://localhost:3000"
echo ""
echo "Press CTRL+C to stop all services"
echo ""
