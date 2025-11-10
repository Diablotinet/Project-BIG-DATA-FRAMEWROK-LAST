# 🚀 QUICK START GUIDE - AFP Real-Time Analytics

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 minute)

```bash
pip install kafka-python pyspark findspark streamlit plotly pandas numpy textblob vaderSentiment scikit-learn
```

### Step 2: Start Services (2 minutes)

**Terminal 1 - Zookeeper:**
```bash
cd downloads\kafka_2.13-3.6.0
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
```

**Terminal 2 - Kafka:**
```bash
cd downloads\kafka_2.13-3.6.0
bin\windows\kafka-server-start.bat config\server.properties
```

**Terminal 3 - Create Topics:**
```bash
python create_topics_afp.py
```

### Step 3: Run AFP System (2 minutes)

**Terminal 4 - Producer:**
```bash
python afp_realtime_producer_complete.py
```

**Terminal 5 - Spark Consumer:**
```bash
python spark_afp_realtime_consumer.py
```

**Terminal 6 - Dashboard:**
```bash
streamlit run dashboard_afp_realtime_complete.py
```

### Step 4: View Results! ✅

Open browser: **http://localhost:8501**

---

## 🎯 What You'll See

### Dashboard Metrics
- 📰 **AFP Articles** - Official news count
- 💬 **Reddit Comparisons** - Social media reactions
- 🌍 **GDELT Events** - Global event correlations
- ⚠️ **Deformation Score** - Information accuracy

### Real-Time Analysis
- **Similarity:** How close Reddit/GDELT matches AFP
- **Deformation:** How much info has changed
- **Objectivity:** Bias detection
- **Timing:** Propagation speed

---

## 🔍 Expected Output Examples

### Producer Console:
```
📰 AFP Article sent: UE adopte nouvelles sanctions...
💬 Reddit post sent (delay: 2.3h, deformation: medium)
🌍 GDELT event sent (delay: 1.5h, sources: 15)
```

### Consumer Console:
```
🔄 Processing batch 1 with 5 messages
📰 Stored AFP article: AFP_001
🔍 Match found: Reddit (72% similarity)
✅ Batch 1 processed: AFP=1, Reddit=2, GDELT=1
```

### Dashboard:
```
📊 Real-Time Metrics
━━━━━━━━━━━━━━━━━━━
📰 AFP Articles: 15
💬 Reddit: 35 (2.3 per article)
🌍 GDELT: 22 (1.5 per article)
⚠️ Avg Deformation: 32%
🎯 Avg Similarity: 68%
```

---

## ⚠️ Troubleshooting

### "Kafka connection refused"
- ✅ Wait 20 seconds after starting Kafka
- ✅ Check port 9092 is free

### "No data in dashboard"
- ✅ Ensure producer is sending messages
- ✅ Check consumer is processing
- ✅ Refresh dashboard (Ctrl+R)

### "Java not found"
- ✅ Install Java 8 or 11
- ✅ Set JAVA_HOME environment variable

---

## 📊 Success Indicators

✅ **Producer:** Sending 1 article every 10-20 seconds  
✅ **Consumer:** Processing batches every 5 seconds  
✅ **Dashboard:** Auto-updating every 5 seconds  
✅ **Database:** Growing in size (afp_realtime_analysis.db)

---

## 🎓 For Your Presentation

### Demo Flow (5 minutes):
1. Show all 6 terminals running ✅
2. Open dashboard ✅
3. Explain AFP → Reddit → GDELT flow ✅
4. Point out deformation detection ✅
5. Show real-time updates ✅

### Key Points:
- ✅ Multi-source real-time ingestion
- ✅ Kafka streaming with 3 topics
- ✅ Spark processing in 5-second batches
- ✅ AI-powered similarity & deformation detection
- ✅ SQLite NoSQL storage
- ✅ Real-time Streamlit dashboard

---

## 📝 Files You Created

1. `afp_realtime_producer_complete.py` - Produces AFP/Reddit/GDELT
2. `spark_afp_realtime_consumer.py` - Processes with Spark
3. `dashboard_afp_realtime_complete.py` - Visualizes results
4. `create_topics_afp.py` - Creates Kafka topics
5. `launch_afp_complete_system.bat` - Auto-launcher

---

## 🎯 Next Steps

1. ✅ Run the system
2. ✅ Watch real-time processing
3. ✅ Analyze deformation patterns
4. ✅ Prepare presentation
5. ✅ Write technical report

---

**Ready? Run:** `launch_afp_complete_system.bat`

**Good luck! 🚀**
