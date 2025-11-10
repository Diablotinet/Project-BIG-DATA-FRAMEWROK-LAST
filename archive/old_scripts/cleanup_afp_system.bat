@echo off
REM ====================================================================
REM  AFP SYSTEM - AUTOMATED CLEANUP SCRIPT
REM  Removes all obsolete files from old multi-source system
REM  Keeps only AFP-specific files for real-time comparison project
REM ====================================================================

echo.
echo ========================================================================
echo   AFP REAL-TIME SYSTEM - CLEANUP SCRIPT
echo   Removing obsolete files from old multi-source system
echo ========================================================================
echo.

REM Create backup folder first
if not exist "backup_old_files" mkdir backup_old_files
echo [BACKUP] Creating backup folder...
echo.

REM Display what will be deleted
echo The following files will be DELETED (moved to backup_old_files):
echo.
echo OLD PRODUCERS:
echo   - kafka_producers.py
echo   - afp_api_producer.py
echo   - afp_realtime_producer.py
echo.
echo OLD CONSUMERS:
echo   - spark_streaming_consumer.py
echo   - spark_afp_comparison_consumer.py
echo   - spark_stream_corrected.py
echo.
echo OLD DASHBOARDS:
echo   - dashboard_afp_enhanced.py
echo   - dashboard_afp_realtime.py
echo.
echo OLD LAUNCHERS/SETUP:
echo   - launch_system.bat
echo   - start_afp_system.py
echo   - create_topics.py
echo   - install_spark_kafka.bat
echo.
echo OLD TESTS/MONITORING:
echo   - test_complete_system.py
echo   - test_kafka_client.py
echo   - monitor_system.py
echo   - content_comparator.py
echo.
echo OLD DOCUMENTATION:
echo   - README.md
echo   - GUIDE_DEMARRAGE.md
echo   - SYSTEM_STATUS.md
echo.
echo OLD DATA/LOGS:
echo   - cross_source_analysis_20251014_145718.json
echo   - spark_streaming.log
echo   - requirements_complete.txt
echo.
echo OLD SCRIPTS:
echo   - scripts\create_topics.bat
echo   - scripts\start_spark_master.bat
echo   - scripts\start_spark_worker.bat
echo.
echo ========================================================================
echo.

choice /C YN /M "Do you want to proceed with cleanup"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :cleanup

:cleanup
echo.
echo [CLEANUP] Starting cleanup process...
echo.

REM Move old producer files
if exist "kafka_producers.py" (
    move /Y "kafka_producers.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved kafka_producers.py
)
if exist "afp_api_producer.py" (
    move /Y "afp_api_producer.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved afp_api_producer.py
)
if exist "afp_realtime_producer.py" (
    move /Y "afp_realtime_producer.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved afp_realtime_producer.py
)

REM Move old consumer files
if exist "spark_streaming_consumer.py" (
    move /Y "spark_streaming_consumer.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved spark_streaming_consumer.py (had Kafka bug)
)
if exist "spark_afp_comparison_consumer.py" (
    move /Y "spark_afp_comparison_consumer.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved spark_afp_comparison_consumer.py
)
if exist "spark_stream_corrected.py" (
    move /Y "spark_stream_corrected.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved spark_stream_corrected.py
)

REM Move old dashboard files
if exist "dashboard_afp_enhanced.py" (
    move /Y "dashboard_afp_enhanced.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved dashboard_afp_enhanced.py
)
if exist "dashboard_afp_realtime.py" (
    move /Y "dashboard_afp_realtime.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved dashboard_afp_realtime.py
)

REM Move old launcher/setup files
if exist "launch_system.bat" (
    move /Y "launch_system.bat" "backup_old_files\" >nul 2>&1
    echo [OK] Moved launch_system.bat
)
if exist "start_afp_system.py" (
    move /Y "start_afp_system.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved start_afp_system.py
)
if exist "create_topics.py" (
    move /Y "create_topics.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved create_topics.py
)
if exist "install_spark_kafka.bat" (
    move /Y "install_spark_kafka.bat" "backup_old_files\" >nul 2>&1
    echo [OK] Moved install_spark_kafka.bat
)

REM Move old test/monitor files
if exist "test_complete_system.py" (
    move /Y "test_complete_system.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved test_complete_system.py
)
if exist "test_kafka_client.py" (
    move /Y "test_kafka_client.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved test_kafka_client.py
)
if exist "monitor_system.py" (
    move /Y "monitor_system.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved monitor_system.py
)
if exist "content_comparator.py" (
    move /Y "content_comparator.py" "backup_old_files\" >nul 2>&1
    echo [OK] Moved content_comparator.py
)

REM Move old documentation
if exist "README.md" (
    move /Y "README.md" "backup_old_files\" >nul 2>&1
    echo [OK] Moved README.md
)
if exist "GUIDE_DEMARRAGE.md" (
    move /Y "GUIDE_DEMARRAGE.md" "backup_old_files\" >nul 2>&1
    echo [OK] Moved GUIDE_DEMARRAGE.md
)
if exist "SYSTEM_STATUS.md" (
    move /Y "SYSTEM_STATUS.md" "backup_old_files\" >nul 2>&1
    echo [OK] Moved SYSTEM_STATUS.md
)

REM Move old data/log files
if exist "cross_source_analysis_20251014_145718.json" (
    move /Y "cross_source_analysis_20251014_145718.json" "backup_old_files\" >nul 2>&1
    echo [OK] Moved cross_source_analysis_20251014_145718.json
)
if exist "spark_streaming.log" (
    move /Y "spark_streaming.log" "backup_old_files\" >nul 2>&1
    echo [OK] Moved spark_streaming.log
)
if exist "requirements_complete.txt" (
    move /Y "requirements_complete.txt" "backup_old_files\" >nul 2>&1
    echo [OK] Moved requirements_complete.txt
)

REM Move old scripts
if exist "scripts\create_topics.bat" (
    move /Y "scripts\create_topics.bat" "backup_old_files\" >nul 2>&1
    echo [OK] Moved scripts\create_topics.bat
)
if exist "scripts\start_spark_master.bat" (
    move /Y "scripts\start_spark_master.bat" "backup_old_files\" >nul 2>&1
    echo [OK] Moved scripts\start_spark_master.bat
)
if exist "scripts\start_spark_worker.bat" (
    move /Y "scripts\start_spark_worker.bat" "backup_old_files\" >nul 2>&1
    echo [OK] Moved scripts\start_spark_worker.bat
)

echo.
echo ========================================================================
echo   CLEANUP COMPLETED SUCCESSFULLY
echo ========================================================================
echo.
echo KEPT FILES (AFP Project Only):
echo   Core System:
echo     - afp_realtime_producer_complete.py
echo     - spark_afp_realtime_consumer.py
echo     - dashboard_afp_realtime_complete.py
echo     - create_topics_afp.py
echo     - launch_afp_complete_system.bat
echo     - test_complete_afp_system.py
echo.
echo   Documentation:
echo     - README_COMPLETE.md
echo     - QUICKSTART.md
echo     - PROJECT_SUMMARY.md
echo     - CLEANUP_REPORT.md
echo.
echo   Configuration:
echo     - requirements.txt
echo     - spark_env.bat
echo.
echo   Infrastructure:
echo     - downloads/kafka_2.13-3.6.0/
echo     - downloads/spark-3.5.0-bin-hadoop3/
echo     - scripts/start_zookeeper.bat
echo     - scripts/start_kafka.bat
echo.
echo BACKUP:
echo   All deleted files are in: backup_old_files\
echo   You can restore them if needed.
echo.
echo NEXT STEPS:
echo   1. Run test: python test_complete_afp_system.py
echo   2. Launch system: launch_afp_complete_system.bat
echo   3. View dashboard: http://localhost:8501
echo.
echo ========================================================================
goto :end

:cancel
echo.
echo [CANCELLED] Cleanup cancelled by user. No files were deleted.
echo.
goto :end

:end
pause
