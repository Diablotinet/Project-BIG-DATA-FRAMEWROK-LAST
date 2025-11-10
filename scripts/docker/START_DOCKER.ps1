# 🐳 Docker Startup Script - AFP Real-Time Analytics System
# Automated Docker deployment with health checks

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "🐳 AFP REAL-TIME ANALYTICS SYSTEM - DOCKER DEPLOYMENT" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Check Docker is installed
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found! Please install Docker Desktop:" -ForegroundColor Red
    Write-Host "   https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker is running
Write-Host ""
Write-Host "🔍 Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker daemon not running! Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check docker-compose
Write-Host ""
Write-Host "🔍 Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose not found!" -ForegroundColor Red
    exit 1
}

# Stop any existing containers
Write-Host ""
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "✅ Existing containers stopped" -ForegroundColor Green

# Build and start containers
Write-Host ""
Write-Host "🔨 Building containers (this may take 5-10 minutes)..." -ForegroundColor Yellow
Write-Host "   - Downloading base images" -ForegroundColor Gray
Write-Host "   - Installing Python dependencies" -ForegroundColor Gray
Write-Host "   - Downloading Spark" -ForegroundColor Gray
Write-Host ""

docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Containers built and started successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Failed to build containers. Check logs with: docker-compose logs" -ForegroundColor Red
    exit 1
}

# Wait for services to be healthy
Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow

$maxWait = 120  # 2 minutes
$waited = 0
$interval = 5

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds $interval
    $waited += $interval
    
    $status = docker-compose ps --format json | ConvertFrom-Json
    $healthy = 0
    $total = 0
    
    foreach ($container in $status) {
        $total++
        $health = docker inspect --format='{{.State.Health.Status}}' $container.Name 2>$null
        if ($health -eq "healthy" -or $health -eq "") {
            $healthy++
        }
    }
    
    Write-Host "   [$waited/$maxWait seconds] $healthy/$total services ready" -ForegroundColor Gray
    
    if ($healthy -eq $total) {
        Write-Host "✅ All services are healthy!" -ForegroundColor Green
        break
    }
}

# Display container status
Write-Host ""
Write-Host "📊 Container Status:" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
docker-compose ps

# Display service URLs
Write-Host ""
Write-Host "🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "📊 Dashboard:     http://localhost:8501" -ForegroundColor Green
Write-Host "⚡ Spark UI:      http://localhost:4040" -ForegroundColor Green
Write-Host "📨 Kafka:         localhost:9092" -ForegroundColor Green
Write-Host "🔧 Zookeeper:     localhost:2181" -ForegroundColor Green

# Check Kafka topics
Write-Host ""
Write-Host "📋 Checking Kafka topics..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
$topics = docker exec afp-kafka kafka-topics --list --bootstrap-server localhost:29092 2>$null

if ($topics) {
    Write-Host "✅ Kafka topics created:" -ForegroundColor Green
    foreach ($topic in $topics -split "`n") {
        if ($topic.Trim()) {
            Write-Host "   - $topic" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "⚠️  Topics not yet created, waiting..." -ForegroundColor Yellow
}

# Display logs command
Write-Host ""
Write-Host "📝 Useful Commands:" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "View all logs:        docker-compose logs -f" -ForegroundColor Gray
Write-Host "View producer logs:   docker-compose logs -f afp-producer" -ForegroundColor Gray
Write-Host "View consumer logs:   docker-compose logs -f spark-consumer" -ForegroundColor Gray
Write-Host "View dashboard logs:  docker-compose logs -f dashboard" -ForegroundColor Gray
Write-Host "Stop system:          docker-compose down" -ForegroundColor Gray
Write-Host "Restart service:      docker-compose restart <service-name>" -ForegroundColor Gray

# Final message
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "✅ SYSTEM READY!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Open dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "   2. Wait 10-15 minutes for data accumulation" -ForegroundColor White
Write-Host "   3. Explore real-time analytics and visualizations" -ForegroundColor White
Write-Host "   4. Check Spark UI for processing details: http://localhost:4040" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Run 'docker-compose logs -f' to see real-time logs" -ForegroundColor Cyan
Write-Host ""

# Ask to open dashboard
$response = Read-Host "Would you like to open the dashboard now? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "🌐 Opening dashboard..." -ForegroundColor Green
    Start-Process "http://localhost:8501"
}

Write-Host ""
Write-Host "✨ System is running! Press Ctrl+C to view logs or close this window." -ForegroundColor Green
Write-Host ""

# Follow logs
docker-compose logs -f
