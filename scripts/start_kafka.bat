@echo off
echo Starting Kafka Server...
cd /d "C:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET\downloads\kafka_2.13-3.6.0"
bin\windows\kafka-server-start.bat config\server.properties
