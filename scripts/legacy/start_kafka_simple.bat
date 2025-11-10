@echo off
echo ===================================
echo Starting Kafka for AFP System
echo ===================================

cd /d "%~dp0downloads\kafka_2.13-3.6.0"

echo.
echo Starting Kafka broker on port 9092...
echo Waiting for Zookeeper connection...
echo.

timeout /t 5 /nobreak >nul

java -Xmx1G -Xms1G -server -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:+ExplicitGCInvokesConcurrent -Djava.awt.headless=true -Dlog4j.configuration=file:config/log4j.properties -cp "libs/*" kafka.Kafka config/server.properties

pause
