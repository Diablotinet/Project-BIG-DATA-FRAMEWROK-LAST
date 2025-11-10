@echo off
call "C:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET\spark_env.bat"
echo Starting Spark Worker...
cd /d "%SPARK_HOME%"
bin\spark-class.cmd org.apache.spark.deploy.worker.Worker spark://localhost:7077
