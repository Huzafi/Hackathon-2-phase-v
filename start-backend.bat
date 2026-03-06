@echo off
REM Hackathon Phase V - Complete Backend Startup Script
REM This script starts Kafka and the FastAPI backend

echo ========================================
echo   Hackathon Phase V - Backend Startup
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

echo [1/4] Checking Docker... OK
echo.

REM Check if .env file exists
if not exist "backend\.env" (
    echo [WARNING] backend\.env file not found!
    echo Creating from .env.example...
    copy backend\.env.example backend\.env
    echo.
    echo [ACTION REQUIRED] Please edit backend\.env with your configuration:
    echo   - DATABASE_URL
    echo   - JWT_SECRET
    echo   - OPENAI_API_KEY
    echo.
    echo Press any key after updating .env file...
    pause
)

echo [2/4] Checking .env file... OK
echo.

REM Start Kafka + Zookeeper
echo [3/4] Starting Kafka + Zookeeper...
docker-compose -f docker-compose.kafka.yml up -d

echo Waiting for Kafka to be ready (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo [4/4] Starting FastAPI Backend...
cd backend

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo [WARNING] Virtual environment not found. Using global Python.
)

echo.
echo Starting uvicorn server...
echo.
echo ========================================
echo   Backend is starting...
echo ========================================
echo.
echo API Docs:         http://localhost:8000/docs
echo Kafka UI:         http://localhost:8080
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn src.main:app --reload --port 8000

cd ..
