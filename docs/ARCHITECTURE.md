# AFP Analytics System - Complete Architecture

## Container Architecture Diagram

```
╔════════════════════════════════════════════════════════════════════╗
║                     AFP ANALYTICS SYSTEM                            ║
║                   Docker Container Network                          ║
╚════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                           │
└──────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐
    │   ZOOKEEPER     │◄───────►│     KAFKA       │
    │   Container     │         │   Container     │
    │                 │         │                 │
    │  Port: 2181     │         │  Port: 9092     │
    │  Health: ✓      │         │  Port: 29092    │
    │                 │         │  Health: ✓      │
    │  Volume:        │         │                 │
    │  - zk-data      │         │  Volume:        │
    │  - zk-logs      │         │  - kafka-data   │
    └─────────────────┘         └────────┬────────┘
                                         │
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                          │

┌──────────────────────────────────────────────────────────────────┐
│                    INITIALIZATION LAYER                           │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   KAFKA-INIT        │
                    │   Container         │
                    │                     │
                    │  Creates Topics:    │
                    │  • afp_news_stream  │
                    │  • reddit_compare   │
                    │  • gdelt_events     │
                    │                     │
                    │  Auto-exits after   │
                    │  topic creation     │
                    └──────────┬──────────┘
                               │
                               ▼
                    (Topics Created Successfully)
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │

┌──────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
└──────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
  │  AFP PRODUCER   │  │ SPARK CONSUMER  │  │   DASHBOARD     │
  │   Container     │  │   Container     │  │   Container     │
  │                 │  │                 │  │                 │
  │  Produces:      │  │  Processes:     │  │  Displays:      │
  │  • AFP news     │  │  • Sentiments   │  │  • Real-time    │
  │  • Reddit data  │  │  • Keywords     │  │    analytics    │
  │  • GDELT events │  │  • Trends       │  │  • Visualizations│
  │                 │  │  • Comparisons  │  │  • Statistics   │
  │  Health: ✓      │  │                 │  │                 │
  │                 │  │  Port: 4040     │  │  Port: 8501     │
  │  Volume:        │  │  Health: ✓      │  │  Health: ✓      │
  │  - logs/        │  │                 │  │                 │
  │                 │  │  Volume:        │  │  Volume:        │
  │                 │  │  - data/        │  │  - data/ (ro)   │
  │                 │  │  - spark-wh/    │  │  - logs/        │
  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
           │                    │                    │
           │                    │                    │
           └──────────►Kafka◄───┴───────────────────►│
                      Topics                     Reads Data

┌──────────────────────────────────────────────────────────────────┐
│                      DATA FLOW                                    │
└──────────────────────────────────────────────────────────────────┘

1. AFP Producer → Kafka (afp_news_stream topic)
   │
   ├─► News articles with metadata
   ├─► Reddit comparison data
   └─► GDELT event data

2. Kafka → Spark Consumer
   │
   ├─► Real-time stream processing
   ├─► Sentiment analysis (VADER + TextBlob)
   ├─► Keyword extraction (TF-IDF)
   ├─► Trend detection
   └─► Cross-source analysis

3. Spark Consumer → Data Storage
   │
   ├─► Processed analytics saved to data/
   ├─► Aggregated statistics
   └─► Time-series data

4. Dashboard ← Data Storage
   │
   ├─► Reads processed data
   ├─► Real-time visualization updates
   └─► Interactive charts and metrics

┌──────────────────────────────────────────────────────────────────┐
│                      NETWORK TOPOLOGY                             │
└──────────────────────────────────────────────────────────────────┘

    Internet                                        Host Machine
       │                                                │
       │                                                │
       └─────────────────┬──────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Docker Bridge      │
              │   afp-network        │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ Port    │    │ Port    │    │ Port    │
    │ 2181    │    │ 9092    │    │ 8501    │
    │ Zk      │    │ Kafka   │    │ Dash    │
    └─────────┘    └─────────┘    └─────────┘
                                        │
                                   ┌────▼────┐
                                   │ Port    │
                                   │ 4040    │
                                   │ Spark   │
                                   └─────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    VOLUME PERSISTENCE                             │
└──────────────────────────────────────────────────────────────────┘

Host Machine                     Docker Volumes
    └── Project/                     
        ├── data/        ◄──────► afp-spark-warehouse
        │                           (Spark metadata)
        │
        ├── logs/        ◄──────► (Mounted in all containers)
        │                           (Application logs)
        │
        └── afp_news_cache.json    (Mounted read-only)


Docker Named Volumes:
    ├── afp-zookeeper-data   (Zookeeper state)
    ├── afp-zookeeper-logs   (Zookeeper logs)
    ├── afp-kafka-data       (Kafka messages)
    └── afp-spark-warehouse  (Spark metadata)

┌──────────────────────────────────────────────────────────────────┐
│                    HEALTH CHECKS                                  │
└──────────────────────────────────────────────────────────────────┘

Service          Health Check                     Interval  Timeout
────────────────────────────────────────────────────────────────────
Zookeeper        nc -z localhost 2181             10s       5s
Kafka            kafka-broker-api-versions        15s       10s
AFP Producer     python -c "import sys..."        30s       10s
Spark Consumer   curl http://localhost:4040       30s       10s
Dashboard        curl http://localhost:8501       30s       10s

┌──────────────────────────────────────────────────────────────────┐
│                    STARTUP SEQUENCE                               │
└──────────────────────────────────────────────────────────────────┘

Time    Event
─────────────────────────────────────────────────────────────────
0s      docker-compose up --build -d
        │
5s      ├─► Zookeeper starts
        │   └─► Binding to port 2181
        │
15s     ├─► Kafka starts (waits for Zookeeper healthy)
        │   ├─► Connects to Zookeeper
        │   └─► Listening on port 9092
        │
20s     ├─► kafka-init runs (waits for Kafka healthy)
        │   ├─► Creates afp_news_stream topic
        │   ├─► Creates reddit_comparisons topic
        │   ├─► Creates gdelt_events topic
        │   └─► Exits successfully
        │
25s     ├─► AFP Producer starts (waits for kafka-init)
        │   └─► Begins publishing messages
        │
30s     ├─► Spark Consumer starts (waits for Producer)
        │   ├─► Initializes Spark session
        │   └─► Begins processing stream
        │
35s     └─► Dashboard starts (waits for Consumer)
            └─► Streamlit ready on port 8501

60s     All services healthy and running ✅

┌──────────────────────────────────────────────────────────────────┐
│                    ACCESS ENDPOINTS                               │
└──────────────────────────────────────────────────────────────────┘

Service              URL                          Purpose
────────────────────────────────────────────────────────────────────
Dashboard            http://localhost:8501        Main visualization
Spark UI             http://localhost:4040        Processing metrics
Kafka (external)     localhost:9092               External connections
Kafka (internal)     kafka:29092                  Container connections
Zookeeper            localhost:2181               Coordination service

┌──────────────────────────────────────────────────────────────────┐
│                    RESOURCE ALLOCATION                            │
└──────────────────────────────────────────────────────────────────┘

Container        CPU    Memory    Disk      Network
────────────────────────────────────────────────────────────────────
Zookeeper        0.5    512MB     2GB       Low
Kafka            1.0    2GB       10GB      Medium
AFP Producer     0.5    512MB     100MB     Medium
Spark Consumer   2.0    4GB       2GB       High
Dashboard        0.5    1GB       100MB     Low
────────────────────────────────────────────────────────────────────
TOTAL            4.5    8GB       14GB      -

Recommended Docker Desktop allocation: 8GB+ RAM, 20GB+ Disk

┌──────────────────────────────────────────────────────────────────┐
│                    MONITORING COMMANDS                            │
└──────────────────────────────────────────────────────────────────┘

# View all container status
docker-compose ps

# Monitor resource usage
docker stats

# Stream all logs
docker-compose logs -f

# Check specific service
docker-compose logs -f spark-consumer

# Inspect container health
docker inspect --format='{{.State.Health.Status}}' afp-kafka

# View Kafka topics
docker exec afp-kafka kafka-topics --list --bootstrap-server localhost:29092

# Count messages in topic
docker exec afp-kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:29092 --topic afp_news_stream

# Consumer group status
docker exec afp-kafka kafka-consumer-groups --bootstrap-server localhost:29092 --list
```

## Key Features

### 1. **Automatic Orchestration**
   - Services start in correct order
   - Dependencies managed automatically
   - Health checks ensure readiness

### 2. **Data Persistence**
   - Named volumes preserve data
   - Survives container restarts
   - Easy backup and restore

### 3. **Scalability**
   - Easy to add replicas
   - Load balancing ready
   - Horizontal scaling support

### 4. **Monitoring**
   - Built-in health checks
   - Comprehensive logging
   - Resource usage tracking

### 5. **Isolation**
   - Separate network namespace
   - No port conflicts
   - Clean environment

## Deployment Options

### Development (Current)
```yaml
docker-compose up --build -d
```

### Production
```yaml
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling
```yaml
docker-compose up --scale afp-producer=3 -d
```

---

**Architecture designed for academic requirements and production readiness!** 
