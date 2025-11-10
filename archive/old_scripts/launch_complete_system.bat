@echo off
echo ========================================
echo   SYSTÈME COMPLET AFP vs SOURCES
echo   Analyse Cross-Source en Temps Réel
echo ========================================

REM 1. Installer package Kafka si nécessaire
call install_spark_kafka.bat

REM 2. Créer topic AFP
cd downloads\kafka_2.13-3.6.0
bin\windows\kafka-topics.bat --create --topic afp_stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>nul
cd ..\..

REM 3. Lancer producers
echo.
echo Démarrage des producers...
start "AFP Producer" cmd /k "python afp_api_producer.py"
timeout /t 5
start "Reddit Producer" cmd /k "python kafka_producers.py"

REM 4. Lancer Spark consumer
echo.
echo Démarrage Spark Streaming...
timeout /t 10
start "Spark Consumer" cmd /k "python spark_stream_corrected.py"

REM 5. Lancer dashboard
echo.
echo Démarrage Dashboard...
timeout /t 5
start "Dashboard" cmd /k "streamlit run dashboard_afp_enhanced.py --server.port 8505"

echo.
echo ========================================
echo SYSTÈME DÉMARRÉ!
echo ========================================
echo.
echo Services actifs:
echo - AFP Producer (vraies données)
echo - Reddit/GDELT Producers
echo - Spark Streaming (analyse temps réel)
echo - Dashboard: http://localhost:8505
echo.
pause
