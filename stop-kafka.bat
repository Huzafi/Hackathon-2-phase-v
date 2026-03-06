@echo off
REM Hackathon Phase V - Kafka Stop Script for Windows

echo ========================================
echo   Stopping Kafka Services
echo ========================================
echo.

docker-compose -f docker-compose.kafka.yml down

echo.
echo [OK] Kafka services stopped
echo.
pause
