@echo off
REM Hackathon Phase V - Kafka Startup Script for Windows
REM This script starts Kafka + Zookeeper using Docker Compose

echo ========================================
echo   Hackathon Phase V - Kafka Setup
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Stop any existing containers
echo Stopping existing Kafka containers...
docker-compose -f docker-compose.kafka.yml down
echo.

REM Start Kafka + Zookeeper
echo Starting Kafka + Zookeeper...
docker-compose -f docker-compose.kafka.yml up -d

REM Wait for services to be healthy
echo.
echo Waiting for services to start (this may take 30-60 seconds)...
timeout /t 10 /nobreak >nul

REM Check container status
echo.
echo Container Status:
docker-compose -f docker-compose.kafka.yml ps

echo.
echo ========================================
echo   Kafka Setup Complete!
echo ========================================
echo.
echo Kafka Broker:     localhost:9092
echo Kafka UI:         http://localhost:8080
echo Zookeeper:        localhost:2181
echo.
echo To stop Kafka:    stop-kafka.bat
echo To view logs:     docker-compose -f docker-compose.kafka.yml logs -f
echo.
pause
