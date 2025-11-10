@echo off
call "C:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET\spark_env.bat"
echo Starting Spark Master...
cd /d "%SPARK_HOME%"
bin\spark-class.cmd org.apache.spark.deploy.master.Master
