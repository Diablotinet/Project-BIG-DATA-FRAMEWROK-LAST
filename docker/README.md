# 🐳 AFP REAL-TIME ANALYTICS - DOCKER DEPLOYMENT

## 🎯 Problem Solved

**Issue**: Kafka not running (port 9092 not accessible)
- Zookeeper is running ✅
- Kafka failed to start due to Windows path length limitations ❌

**Solution**: Docker containerization eliminates ALL Windows issues:
- ✅ No Windows path length limits
- ✅ No batch script problems
- ✅ Automated service orchestration
- ✅ Reproducible deployment
- ✅ Easy scaling and management

## 🚀 Quick Start (3 Steps)

### Step 1: Install Docker Desktop
Download and install: https://www.docker.com/products/docker-desktop
- Allocate at least 8GB RAM to Docker
- Enable WSL 2 backend (recommended)

### Step 2: Start the System

**Option A - PowerShell (Recommended):**
```powershell
.\START_DOCKER.ps1
```

**Option B - Batch File:**
```cmd
START_DOCKER.bat
```

**Option C - Manual:**
```powershell
docker-compose up --build -d
```

### Step 3: Access Dashboard
Open http://localhost:8501 in your browser

**That's it!** The system is fully running with:
- Zookeeper (coordination)
- Kafka (message streaming)
- AFP Producer (news data)
- Spark Consumer (real-time processing)
- Streamlit Dashboard (visualization)

## 📊 System Architecture

```
┌─────────────────────────────────────────────────┐
│              Docker Network                      │
│                                                  │
│  [Zookeeper] ◄──► [Kafka]                       │
│                      │                           │
│                      ├──► [AFP Producer]         │
│                      │                           │
│                      ├──► [Spark Consumer] ──►[Dashboard]
│                      │      (Port 4040)     (Port 8501)
│                      │                           │
│                      └──► [Topic Creator]        │
└─────────────────────────────────────────────────┘
```

## 🔧 What's Included

### Containers Created
1. **afp-zookeeper** - Kafka coordination (port 2181)
2. **afp-kafka** - Message broker (port 9092)
3. **kafka-init** - Automatic topic creation
4. **afp-producer** - Generates AFP news data
5. **afp-spark-consumer** - Real-time stream processing (port 4040)
6. **afp-dashboard** - Interactive visualization (port 8501)

### Persistent Storage
- Zookeeper data & logs
- Kafka messages
- Spark warehouse
- Application data

## 📝 Common Commands

```powershell
# View all services
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f afp-producer
docker-compose logs -f spark-consumer
docker-compose logs -f dashboard

# Stop system
docker-compose down

# Stop and remove all data
docker-compose down -v

# Restart a service
docker-compose restart dashboard

# Check Kafka topics
docker exec afp-kafka kafka-topics --list --bootstrap-server localhost:29092

# View Kafka messages
docker exec afp-kafka kafka-console-consumer --bootstrap-server localhost:29092 --topic afp_news_stream --from-beginning --max-messages 5
```

## 🐛 Troubleshooting

### Docker not installed
- Download: https://www.docker.com/products/docker-desktop
- Install and restart your computer
- Run: `docker --version` to verify

### Docker daemon not running
- Start Docker Desktop application
- Wait for "Docker Desktop is running" message
- Try again

### Port conflicts
```powershell
# Check if ports are in use
Test-NetConnection -ComputerName localhost -Port 8501
Test-NetConnection -ComputerName localhost -Port 9092

# Stop local Kafka/Zookeeper if running
# Then restart Docker containers
```

### Containers not healthy
```powershell
# Check container status
docker-compose ps

# Check specific container logs
docker-compose logs kafka
docker-compose logs spark-consumer

# Restart unhealthy service
docker-compose restart <service-name>
```

### Out of memory
- Open Docker Desktop
- Go to Settings → Resources
- Increase Memory to 8GB or more
- Click "Apply & Restart"

## ✅ Verification

After starting, verify everything is working:

```powershell
# 1. Check all containers are running
docker-compose ps

# Expected: All services "Up" or "Up (healthy)"

# 2. Check Kafka topics exist
docker exec afp-kafka kafka-topics --list --bootstrap-server localhost:29092

# Expected: afp_news_stream, reddit_comparisons, gdelt_events

# 3. Check messages are flowing
docker-compose logs afp-producer | Select-String "Published"

# Expected: "📰 Published AFP article: AFP_001" etc.

# 4. Open dashboard
# Navigate to http://localhost:8501
# Expected: Interactive dashboard with real-time data
```

## 🎓 Academic Requirements Met

✅ **Multi-source data ingestion** - AFP news, Reddit, GDELT  
✅ **Apache Kafka** - Message streaming platform  
✅ **Spark Streaming** - Real-time processing  
✅ **Text Analytics** - Sentiment analysis, keyword extraction  
✅ **Visualization** - Real-time Streamlit dashboard  
✅ **Production deployment** - Docker containerization  
✅ **Scalability** - Easy to scale with docker-compose  

## 📈 Next Steps for Presentation

1. ✅ Run `.\START_DOCKER.ps1` or `START_DOCKER.bat`
2. ✅ Wait 2-3 minutes for all services to start
3. ✅ Open http://localhost:8501
4. ✅ Let system run for 10-15 minutes to accumulate data
5. ✅ Take screenshots of:
   - Dashboard with real-time analytics
   - Spark UI (http://localhost:4040)
   - Container status (`docker-compose ps`)
6. ✅ Demonstrate live data updates
7. ✅ Show logs with `docker-compose logs -f`

## 🌟 Advantages Over Manual Setup

| Manual Setup | Docker Setup |
|--------------|--------------|
| Windows path issues ❌ | No path issues ✅ |
| Manual service startup ❌ | Automatic orchestration ✅ |
| Complex troubleshooting ❌ | Simple commands ✅ |
| Platform-dependent ❌ | Cross-platform ✅ |
| Hard to reproduce ❌ | Reproducible ✅ |
| 6 manual steps ❌ | 1 command ✅ |

## 📚 Documentation

- **DOCKER_GUIDE.md** - Complete Docker guide with all commands
- **docker-compose.yml** - Service definitions
- **Dockerfile** - Application container specification
- **.dockerignore** - Files excluded from containers

---

**Ready for deployment!** 🚀

Run `.\START_DOCKER.ps1` and you're done!
