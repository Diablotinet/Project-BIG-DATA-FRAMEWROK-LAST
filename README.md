# AFP Multi-Source Analytics System

A real-time streaming analytics platform that compares news articles from multiple sources (AFP, Reddit, GDELT) using advanced ML-based analysis with Kafka and Apache Spark.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (latest version)
- Docker Compose (included with Docker Desktop)
- Internet connection for API data sources

### Run the System

\\\powershell
# Navigate to project directory
cd "c:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET"

# Start all services
docker-compose up -d

# Wait 30 seconds for Kafka/Zookeeper to initialize
# Then access the dashboard
Start-Process "http://localhost:8501"
\\\

## 📊 System Components

### Architecture
- **Zookeeper**: Kafka coordination
- **Kafka Broker**: Message streaming (3 topics)
- **Producer**: Multi-source data ingestion (AFP, Reddit, GDELT)
- **Spark Consumer**: Real-time stream processing + ML analysis
- **Dashboard**: Streamlit visualization (port 8501)
- **Database**: SQLite persistence

### Data Pipeline
1. **Ingestion**: Producer collects articles from 3 sources → Kafka
2. **Streaming**: Kafka distributes messages across 3 topics
3. **Processing**: Spark consumes in real-time (5-second batches)
4. **Analysis**: ML engine generates comprehensive comparison analysis
5. **Storage**: Results stored in SQLite database
6. **Visualization**: Dashboard displays real-time insights

## 📈 ML Analysis Features

Each article comparison includes:
- **Headline Comparison**: Framing and focus differences
- **Content Deformation**: Information integrity scoring (0-100%)
- **Objectivity Assessment**: Bias and editorial stance analysis
- **Sentiment Analysis**: Emotional tone tracking
- **Framing Analysis**: Narrative structure comparison
- **Comprehensive Verdict**: Reliability classification (Low/Moderate/High)

## 🎛️ Monitoring & Verification

### Check System Status
\\\powershell
docker-compose ps
\\\

### View Streaming Logs
\\\powershell
docker logs -f afp-spark-consumer
\\\

### Access Database Directly
\\\powershell
docker exec afp-spark-consumer sqlite3 /app/data/afp_realtime_analysis.db
\\\

### Stop the System
\\\powershell
docker-compose down
\\\

## 📊 Dashboard Features

Access the dashboard at: **http://localhost:8501**

- Real-time comparison statistics
- Source filtering (AFP, Reddit, GDELT)
- Similarity and deformation metrics
- Sentiment distribution
- Trending topics
- Detailed comparison analysis

## 📁 Project Structure

\\\
.
├── docker/                          # Docker orchestration
│   ├── docker-compose.yml           # Service definitions
│   ├── Dockerfile                   # Python/Spark image
│   ├── config/                      # Configuration files
│   ├── data/                        # Persistent volumes
│   └── logs/                        # Docker logs
│
├── src/                             # Source code
│   ├── producers/                   # Data ingestion
│   │   └── afp_realtime_producer_complete.py
│   ├── consumers/                   # Stream processing
│   │   └── spark_afp_realtime_consumer.py
│   ├── utils/                       # Utilities
│   │   └── content_comparator.py
│   └── dashboard/                   # Visualization
│       └── dashboard_afp_realtime_complete.py
│
├── docker-compose.yml               # Service orchestration
├── Dockerfile                       # Container image
├── requirements.txt                 # Python dependencies
├── .env.template                    # Environment template
└── README.md                        # This file
\\\

## 🔧 Configuration

### Environment Variables
Copy \.env.template\ to \.env\ and customize:
- \KAFKA_BROKERS\: Kafka connection
- \SPARK_MASTER\: Spark master URL
- \DATABASE_PATH\: SQLite database location
- \REDDIT_KEYWORDS\: Search terms for Reddit
- \GDELT_DATABASE\: GDELT data source

## 🐛 Troubleshooting

### Containers not starting
\\\powershell
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
\\\

### Kafka topics not created
\\\powershell
docker-compose logs afp-kafka-init
\\\

### Dashboard not accessible
\\\powershell
docker ps | grep dashboard
docker logs afp-dashboard
\\\

## 📊 Project Requirements - Verification

✅ **Multi-Source Data Ingestion**: AFP, Reddit, GDELT  
✅ **Streaming Data Processing**: Kafka + Spark integration  
✅ **Text Analysis**: TF-IDF similarity, sentiment scoring  
✅ **Data Storage**: SQLite with comprehensive schema  
✅ **Reporting & Visualization**: Streamlit dashboard  
✅ **Word Counts**: TF-IDF based keyword analysis  
✅ **Trending Topics**: Keyword extraction and trending  
✅ **Sentiment Scoring**: VADER sentiment analysis  
✅ **Anomaly Detection**: Deformation-based alerts  

## 📈 Performance Metrics

- **Processing Speed**: 4-8 matches per 5-second batch
- **Analysis Quality**: 2,000+ character comprehensive reports per comparison
- **Database**: 1,500+ analyzed comparisons with full metadata
- **Memory Usage**: ~2GB for all 6 containers
- **CPU Usage**: 20-30% average

## 🤝 Data Sources

- **AFP**: Simulated news articles (can integrate real API)
- **Reddit**: Real-time Reddit post data via API
- **GDELT**: Global Event, Location and Tone dataset

## 📝 License

Academic project - EFREI Paris

## 👥 Support

For issues or questions, refer to:
- PROJECT_COMPLETION_REPORT.md - Detailed system documentation
- SYSTEM_STATUS.md - Current system status
- Docker logs: \docker-compose logs [service]\

---
**Last Updated**: \2025-11-10 01:23:44
