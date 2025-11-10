@echo off
echo ========================================
echo   AFP REAL-TIME ANALYTICS SYSTEM
echo   Complete Launch Script
echo ========================================
echo.

echo Prerequisites Check...
echo [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo OK: Python found

echo [2/7] Checking Kafka installation...
if not exist "downloads\kafka_2.13-3.6.0" (
    echo ERROR: Kafka not found in downloads folder!
    pause
    exit /b 1
)
echo OK: Kafka found

echo [3/7] Checking Spark installation...
if not exist "downloads\spark-3.5.0-bin-hadoop3" (
    echo ERROR: Spark not found in downloads folder!
    pause
    exit /b 1
)
echo OK: Spark found

echo.
echo ========================================
echo   STARTING SERVICES
echo ========================================
echo.

echo [1/4] Starting Zookeeper...
start "Zookeeper" cmd /k "cd downloads\kafka_2.13-3.6.0 && bin\windows\zookeeper-server-start.bat config\zookeeper.properties"
timeout /t 10

echo [2/4] Starting Kafka...
start "Kafka" cmd /k "cd downloads\kafka_2.13-3.6.0 && bin\windows\kafka-server-start.bat config\server.properties"
timeout /t 15

echo [3/4] Creating Kafka topics...
python create_topics_afp.py
timeout /t 5

echo [4/4] Installing required Python packages...
pip install -q kafka-python pyspark textblob vaderSentiment scikit-learn streamlit plotly pandas numpy

echo.
echo ========================================
echo   STARTING AFP ANALYTICS PIPELINE
echo ========================================
echo.

echo [1/3] Starting AFP Producer (Kafka messages)...
start "AFP Producer" cmd /k "python afp_realtime_producer_complete.py"
timeout /t 5

echo [2/3] Starting Spark Consumer (Real-time processing)...
start "Spark Consumer" cmd /k "python spark_afp_realtime_consumer.py"
timeout /t 10

echo [3/3] Starting Streamlit Dashboard...
start "Dashboard" cmd /k "streamlit run dashboard_afp_realtime_complete.py"
timeout /t 5

echo.
echo ========================================
echo   SYSTEM STARTED SUCCESSFULLY!
echo ========================================
echo.
echo Services running:
echo   [1] Zookeeper      : localhost:2181
echo   [2] Kafka          : localhost:9092
echo   [3] AFP Producer   : Publishing to Kafka
echo   [4] Spark Consumer : Processing streams
echo   [5] Dashboard      : http://localhost:8501
echo.
echo Open your browser to http://localhost:8501
echo.
echo Press Ctrl+C in each window to stop services
echo ========================================
pause
