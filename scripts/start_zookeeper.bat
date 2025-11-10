@echo off
echo Starting Zookeeper...
cd /d "C:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET\downloads\kafka_2.13-3.6.0"
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
