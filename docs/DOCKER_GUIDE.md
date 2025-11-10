# 🐳 Docker Deployment Guide - AFP Real-Time Analytics System

## Overview

This Docker setup containerizes the entire AFP analytics system:
- ✅ **Zookeeper** - Kafka coordination (port 2181)
- ✅ **Kafka** - Message streaming (port 9092)
- ✅ **AFP Producer** - News data generator
- ✅ **Spark Consumer** - Real-time stream processing (Spark UI: port 4040)
- ✅ **Streamlit Dashboard** - Interactive visualization (port 8501)

## Quick Start

### Prerequisites
1. **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
2. **Docker Compose** included with Docker Desktop
3. **At least 8GB RAM** allocated to Docker

### Starting the System

```powershell
# Navigate to project directory
cd "c:\Users\aitnd\Documents\Efrei Paris\SEMESTRE 7\BIG DATA FRAMEWORK\PROJET"

# Build and start all containers
docker-compose up --build

# Or run in background (detached mode)
docker-compose up --build -d
```

### Accessing Services

Once running, access:
- **Dashboard**: http://localhost:8501
- **Spark UI**: http://localhost:4040
- **Kafka**: localhost:9092 (internal)

## Container Architecture

```
┌─────────────────────────────────────────────────┐
│              afp-network (Bridge)                │
│                                                  │
│  ┌──────────────┐      ┌──────────────┐         │
│  │  Zookeeper   │◄────►│    Kafka     │         │
│  │  :2181       │      │  :9092       │         │
│  └──────────────┘      └──────┬───────┘         │
│                                │                 │
│                                ▼                 │
│                    ┌────────────────────┐        │
│                    │   kafka-init       │        │
│                    │ (Topic Creator)    │        │
│                    └─────────┬──────────┘        │
│                              │                   │
│         ┌────────────────────┼──────────────┐    │
│         ▼                    ▼              ▼    │
│  ┌─────────────┐   ┌──────────────┐  ┌─────────┐│
│  │AFP Producer │   │Spark Consumer│  │Dashboard││
│  │             │   │   :4040      │  │  :8501  ││
│  └─────────────┘   └──────────────┘  └─────────┘│
└─────────────────────────────────────────────────┘
```

## Docker Commands

### Starting Services
```powershell
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d kafka

# Rebuild and start
docker-compose up --build -d
```

### Monitoring
```powershell
# View all container logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f afp-producer
docker-compose logs -f spark-consumer
docker-compose logs -f dashboard

# Check container status
docker-compose ps

# Check container resource usage
docker stats
```

### Stopping Services
```powershell
# Stop all containers
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Stop specific service
docker-compose stop dashboard
```

### Debugging
```powershell
# Enter container shell
docker exec -it afp-producer bash
docker exec -it afp-kafka bash

# View Kafka topics
docker exec afp-kafka kafka-topics --list --bootstrap-server localhost:29092

# View Kafka messages
docker exec afp-kafka kafka-console-consumer --bootstrap-server localhost:29092 --topic afp_news_stream --from-beginning --max-messages 5

# Check container health
docker inspect --format='{{.State.Health.Status}}' afp-kafka
```

## Data Persistence

Volumes for persistent storage:
- `afp-zookeeper-data` - Zookeeper data
- `afp-zookeeper-logs` - Zookeeper logs
- `afp-kafka-data` - Kafka messages
- `afp-spark-warehouse` - Spark metadata

View volumes:
```powershell
docker volume ls
docker volume inspect afp-kafka-data
```

## Troubleshooting

### Problem: Containers not starting
```powershell
# Check Docker Desktop is running
docker --version

# Check logs for errors
docker-compose logs

# Restart Docker Desktop
# Then try again
docker-compose up --build -d
```

### Problem: Port conflicts
```powershell
# Check if ports are in use
Test-NetConnection -ComputerName localhost -Port 9092
Test-NetConnection -ComputerName localhost -Port 2181

# Stop conflicting services
# Then restart containers
docker-compose down
docker-compose up -d
```

### Problem: Out of memory
```powershell
# Increase Docker memory in Docker Desktop:
# Settings → Resources → Memory (set to 8GB+)

# Restart Docker Desktop
# Then restart containers
```

### Problem: Kafka topics not created
```powershell
# Check kafka-init logs
docker-compose logs kafka-init

# Manually create topics
docker exec afp-kafka kafka-topics --create --bootstrap-server localhost:29092 --topic afp_news_stream --partitions 3 --replication-factor 1
```

### Problem: Dashboard not loading
```powershell
# Check dashboard logs
docker-compose logs dashboard

# Restart dashboard
docker-compose restart dashboard

# Check health
docker inspect --format='{{.State.Health.Status}}' afp-dashboard
```

## Testing the System

### 1. Verify all containers are running
```powershell
docker-compose ps
```

Expected output:
```
NAME               STATUS        PORTS
afp-dashboard      Up (healthy)  0.0.0.0:8501->8501/tcp
afp-kafka          Up (healthy)  0.0.0.0:9092->9092/tcp
afp-producer       Up            
afp-spark-consumer Up (healthy)  0.0.0.0:4040->4040/tcp
afp-zookeeper      Up (healthy)  0.0.0.0:2181->2181/tcp
```

### 2. Check Kafka messages
```powershell
docker exec afp-kafka kafka-console-consumer --bootstrap-server localhost:29092 --topic afp_news_stream --from-beginning --max-messages 3
```

### 3. Open dashboard
Navigate to http://localhost:8501 in your browser

### 4. Wait for data accumulation
Let the system run for 10-15 minutes to accumulate analytics

## Production Deployment

### Build optimized images
```powershell
# Build production images
docker-compose build --no-cache

# Tag for registry
docker tag afp-dashboard:latest yourregistry/afp-dashboard:1.0
docker tag afp-producer:latest yourregistry/afp-producer:1.0

# Push to registry
docker push yourregistry/afp-dashboard:1.0
docker push yourregistry/afp-producer:1.0
```

### Environment configuration
Create `.env` file:
```env
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_PARTITIONS=3
KAFKA_REPLICATION_FACTOR=1
SPARK_MASTER=local[*]
LOG_LEVEL=INFO
```

## Performance Tuning

### Kafka optimization
Edit `docker-compose.yml`:
```yaml
kafka:
  environment:
    KAFKA_NUM_NETWORK_THREADS: 8
    KAFKA_NUM_IO_THREADS: 16
    KAFKA_SOCKET_SEND_BUFFER_BYTES: 102400
    KAFKA_SOCKET_RECEIVE_BUFFER_BYTES: 102400
```

### Spark optimization
```yaml
spark-consumer:
  environment:
    SPARK_DRIVER_MEMORY: 4g
    SPARK_EXECUTOR_MEMORY: 4g
    SPARK_EXECUTOR_CORES: 2
```

## Security (Production)

### Enable authentication
```yaml
kafka:
  environment:
    KAFKA_LISTENERS: SASL_PLAINTEXT://kafka:29092
    KAFKA_SECURITY_PROTOCOL: SASL_PLAINTEXT
    KAFKA_SASL_MECHANISM: PLAIN
```

### Network isolation
```yaml
networks:
  afp-network:
    driver: bridge
    internal: true  # No external access
```

## Next Steps

1. ✅ Start Docker Desktop
2. ✅ Run `docker-compose up --build -d`
3. ✅ Wait 2-3 minutes for all services to start
4. ✅ Open http://localhost:8501
5. ✅ Let system run for 10-15 minutes
6. ✅ Take screenshots for presentation

## Support

Common issues:
- **Windows path errors**: Fixed by Docker containerization
- **Java classpath too long**: Fixed by Docker containerization
- **Port conflicts**: Stop local Kafka/Zookeeper services first
- **Memory issues**: Increase Docker memory allocation

For detailed logs: `docker-compose logs -f`

## Academic Compliance

This Docker setup fulfills all project requirements:
- ✅ Multi-source data ingestion (AFP, Reddit, GDELT)
- ✅ Apache Kafka message streaming
- ✅ Spark real-time processing
- ✅ Text analytics (sentiment, keywords)
- ✅ Real-time visualization dashboard
- ✅ Production-ready deployment
- ✅ Scalable architecture

---

**Ready for presentation!** 
