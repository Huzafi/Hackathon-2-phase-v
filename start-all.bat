@echo off
REM Complete Kafka & Dapr Stack Startup Script for Windows

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║     Event-Driven Architecture Stack Startup                    ║
echo ║     Kafka + Dapr + PostgreSQL + Backend + Frontend             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is running
docker ps > nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker is not running!
    echo.
    echo Please start Docker Desktop:
    echo 1. Click Docker Desktop icon
    echo 2. Wait for it to start
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Check if Docker Compose is available
docker-compose --version > nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker Compose is not available!
    pause
    exit /b 1
)

echo ✅ Docker Compose is available
echo.

REM Navigate to project directory
cd /d "%~dp0"

echo 📍 Current Directory: %cd%
echo.

REM Check if docker-compose.yml exists
if not exist docker-compose.yml (
    echo ❌ ERROR: docker-compose.yml not found!
    pause
    exit /b 1
)

echo ✅ docker-compose.yml found
echo.

echo 🔍 Checking for existing containers...
docker-compose ps
echo.

echo 🚀 Starting complete stack with Kafka & Dapr...
echo.
echo Services that will start:
echo   • PostgreSQL (Database) - Port 5432
echo   • Zookeeper (Kafka Coordination) - Port 2181
echo   • Kafka (Event Streaming) - Port 9092
echo   • Kafka UI (Monitoring) - Port 8080
echo   • Redis (State Store) - Port 6379
echo   • Backend (FastAPI) - Port 8000
echo   • Dapr Sidecar - Port 3500, 50001
echo   • Frontend (Next.js) - Port 3000
echo.

echo ⏱️  Estimated startup time: 2-3 minutes (first run may take longer)
echo.

REM Start Docker Compose
docker-compose up

REM Check exit code
if errorlevel 1 (
    echo.
    echo ❌ Docker Compose failed to start!
    echo.
    echo Try these troubleshooting steps:
    echo 1. Check Docker Desktop is running: docker ps
    echo 2. View logs: docker-compose logs
    echo 3. Clean up: docker-compose down -v
    echo 4. Rebuild: docker-compose up --build
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ All services started successfully!
echo.
echo 📚 Access your services:
echo   • Backend API:  http://localhost:8000
echo   • API Docs:     http://localhost:8000/docs
echo   • Kafka UI:     http://localhost:8080
echo   • Frontend:     http://localhost:3000
echo.
echo Press CTRL+C to stop all services
echo.
