#!/usr/bin/env powershell
# Reorganize project to match clean structure

$projectRoot = "c:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET"
Set-Location $projectRoot

Write-Host "`n🗂️  REORGANIZING PROJECT STRUCTURE`n" -ForegroundColor Cyan

# STEP 1: Move source code files to src/
Write-Host "Moving source code to src/..." -ForegroundColor Yellow

# Create src subdirectories if they don't exist
@("src\producers", "src\consumers", "src\utils", "src\dashboard") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "  ✓ Created: $_"
    }
}

# Move producer files
@("afp_realtime_producer_complete.py") | ForEach-Object {
    if (Test-Path $_) {
        $srcPath = Join-Path "src" "producers" (Split-Path $_ -Leaf)
        if (-not (Test-Path $srcPath)) {
            Move-Item $_ -Destination $srcPath -Force
            Write-Host "  ✓ Moved: $_ → src/producers/"
        }
    }
}

# Move consumer files
@("spark_afp_realtime_consumer.py", "spark_streaming_consumer.py") | ForEach-Object {
    if (Test-Path $_) {
        $srcPath = Join-Path "src" "consumers" (Split-Path $_ -Leaf)
        if (-not (Test-Path $srcPath)) {
            Move-Item $_ -Destination $srcPath -Force
            Write-Host "  ✓ Moved: $_ → src/consumers/"
        }
    }
}

# Move utils/dashboard files
@("content_comparator.py", "create_topics.py") | ForEach-Object {
    if (Test-Path $_) {
        $srcPath = Join-Path "src" "utils" (Split-Path $_ -Leaf)
        if (-not (Test-Path $srcPath)) {
            Move-Item $_ -Destination $srcPath -Force
            Write-Host "  ✓ Moved: $_ → src/utils/"
        }
    }
}

@("dashboard_afp_realtime_complete.py") | ForEach-Object {
    if (Test-Path $_) {
        $srcPath = Join-Path "src" "dashboard" (Split-Path $_ -Leaf)
        if (-not (Test-Path $srcPath)) {
            Move-Item $_ -Destination $srcPath -Force
            Write-Host "  ✓ Moved: $_ → src/dashboard/"
        }
    }
}

# STEP 2: Move test files to tests/
Write-Host "`nMoving test files to tests/..." -ForegroundColor Yellow

@("test_complete_afp_system.py", "test_kafka_client.py") | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ -Destination "tests\" -Force
        Write-Host "  ✓ Moved: $_ → tests/"
    }
}

# STEP 3: Move documentation to docs/
Write-Host "`nMoving documentation to docs/..." -ForegroundColor Yellow

@("PROJECT_COMPLETION_REPORT.md", "SYSTEM_STATUS.md", "FINAL_COMPLETION_REPORT.md", "PROJECT_REQUIREMENTS_VERIFICATION.md", "CLEANUP_VERIFICATION.md") | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ -Destination "docs\" -Force
        Write-Host "  ✓ Moved: $_ → docs/"
    }
}

# STEP 4: Move setup/infrastructure files to config/
Write-Host "`nMoving configuration files to config/..." -ForegroundColor Yellow

@("setup_infrastructure.py", "setup.log") | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ -Destination "config\" -Force
        Write-Host "  ✓ Moved: $_ → config/"
    }
}

# STEP 5: Move log files to logs/
Write-Host "`nMoving log files to logs/..." -ForegroundColor Yellow

@("kafka_producers.log") | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ -Destination "logs\" -Force
        Write-Host "  ✓ Moved: $_ → logs/"
    }
}

# STEP 6: Move old/unused scripts to archive/
Write-Host "`nMoving old scripts to archive/..." -ForegroundColor Yellow

@("kafka_producers.py", "monitor_system.py", "launch_afp_complete_system.bat", "CLEANUP_PROJECT.ps1") | ForEach-Object {
    if (Test-Path $_) {
        Move-Item $_ -Destination "archive\" -Force
        Write-Host "  ✓ Moved: $_ → archive/"
    }
}

# STEP 7: Ensure Docker files are in root (not in docker/ folder)
Write-Host "`nVerifying Docker files in root..." -ForegroundColor Yellow

$dockerFilesNeeded = @("docker-compose.yml", "Dockerfile", ".dockerignore")
$dockerFilesNeeded | ForEach-Object {
    if (-not (Test-Path $_) -and (Test-Path "docker\$_")) {
        Copy-Item "docker\$_" -Destination $_ -Force
        Write-Host "  ✓ Copied: $_ to root"
    } elseif (Test-Path $_) {
        Write-Host "  ✓ Already in root: $_"
    }
}

# STEP 8: Ensure environment files are in root
Write-Host "`nVerifying environment files..." -ForegroundColor Yellow

@(".env.template", ".env") | ForEach-Object {
    if (-not (Test-Path $_) -and (Test-Path "docker\$_")) {
        Copy-Item "docker\$_" -Destination $_ -Force
        Write-Host "  ✓ Copied: $_ to root"
    } elseif (Test-Path $_) {
        Write-Host "  ✓ Already in root: $_"
    }
}

# STEP 9: Ensure requirements.txt is in root
Write-Host "`nVerifying requirements.txt..." -ForegroundColor Yellow

if (-not (Test-Path "requirements.txt")) {
    if (Test-Path "docker\requirements.txt") {
        Copy-Item "docker\requirements.txt" -Destination "requirements.txt" -Force
        Write-Host "  ✓ Copied: requirements.txt to root"
    }
}

# STEP 10: Display final structure
Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ REORGANIZATION COMPLETE!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Green

Write-Host "📁 FINAL PROJECT STRUCTURE:" -ForegroundColor Cyan
Write-Host "PROJET/"
Write-Host "├── 📂 docker/                (Docker config & volumes)"
Write-Host "├── 📂 src/                  (Application source code)"
Write-Host "│   ├── producers/"
Write-Host "│   ├── consumers/"
Write-Host "│   ├── utils/"
Write-Host "│   └── dashboard/"
Write-Host "├── 📂 tests/                (Test suite)"
Write-Host "├── 📂 docs/                 (Documentation)"
Write-Host "├── 📂 data/                 (Local data)"
Write-Host "├── 📂 logs/                 (Local logs)"
Write-Host "├── 📂 archive/              (Old files)"
Write-Host "├── 📂 scripts/              (Shell scripts)"
Write-Host "├── 📂 config/               (Config & setup)"
Write-Host "├── 📂 downloads/            (Kafka/Spark)"
Write-Host "├── docker-compose.yml       (ROOT)"
Write-Host "├── Dockerfile               (ROOT)"
Write-Host "├── requirements.txt         (ROOT)"
Write-Host "├── .env.template            (ROOT)"
Write-Host "├── .env                     (ROOT)"
Write-Host "└── README.md                (ROOT)"

Write-Host "`n✅ All files are now properly organized!"
Write-Host "`nRoot directory files:"
Write-Host ""
(Get-ChildItem -File | Measure-Object).Count | ForEach-Object { Write-Host "  Count: $_" }
Write-Host ""
