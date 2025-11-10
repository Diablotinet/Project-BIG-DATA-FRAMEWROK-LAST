@echo off
echo Creating Kafka Topics...
cd /d "C:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET\downloads\kafka_2.13-3.6.0"

rem Topic pour Reddit
bin\windows\kafka-topics.bat --create --topic reddit_stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

rem Topic pour Twitter  
bin\windows\kafka-topics.bat --create --topic twitter_stream --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

rem Topic pour IoT Sensors
bin\windows\kafka-topics.bat --create --topic iot_sensors --bootstrap-server localhost:9092 --partitions 5 --replication-factor 1

rem Topic pour News Feed
bin\windows\kafka-topics.bat --create --topic news_feed --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1

echo Topics created successfully!
pause
