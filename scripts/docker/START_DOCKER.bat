@echo off
REM 🐳 Windows Batch Launcher for Docker System
REM Use this if PowerShell scripts are blocked

echo ========================================
echo   AFP Analytics - Docker Deployment
echo ========================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker is running...
echo.

REM Stop existing containers
echo Stopping existing containers...
docker-compose down 2>nul

REM Build and start
echo.
echo Building and starting containers...
echo This will take 5-10 minutes on first run...
echo.
docker-compose up --build -d

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start containers!
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo   System Started Successfully!
echo ========================================
echo.
echo Service URLs:
echo   Dashboard:  http://localhost:8501
echo   Spark UI:   http://localhost:4040
echo   Kafka:      localhost:9092
echo.
echo Useful commands:
echo   View logs:  docker-compose logs -f
echo   Stop:       docker-compose down
echo.

REM Wait a bit for services to start
timeout /t 10 /nobreak

REM Open dashboard
echo Opening dashboard...
start http://localhost:8501

echo.
echo Press any key to view logs...
pause >nul

docker-compose logs -f
