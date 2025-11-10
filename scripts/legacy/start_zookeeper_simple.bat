@echo off
echo ===================================
echo Starting Zookeeper for AFP System
echo ===================================

cd /d "%~dp0downloads\kafka_2.13-3.6.0"

echo.
echo Starting Zookeeper on port 2181...
echo.

java -Xmx512M -Xms512M -server -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35 -XX:+ExplicitGCInvokesConcurrent -Djava.awt.headless=true -Dlog4j.configuration=file:config/log4j.properties -cp "libs/*" org.apache.zookeeper.server.quorum.QuorumPeerMain config/zookeeper.properties

pause
