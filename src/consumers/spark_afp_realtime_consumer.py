#!/usr/bin/env python3
"""
⚡ SPARK STREAMING CONSUMER - AFP REAL-TIME COMPARISON
Consumes AFP, Reddit, and GDELT streams in real-time
Performs AI-powered content analysis, deformation detection, and objectivity scoring
"""

import os
import sys
import json
import logging
import findspark
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from pathlib import Path

# Configure Spark environment BEFORE importing PySpark
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# CRITICAL: Add Kafka packages to Spark submit arguments
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.0 pyspark-shell'

findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('spark_afp_realtime.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AFPRealTimeAnalyzer")

class AFPRealtimeComparator:
    """Real-time AFP comparison engine with AI-powered analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger("AFPComparator")
        self.spark = None
        self.vader = SentimentIntensityAnalyzer()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        
        # Database for storing results
        self.db_path = "afp_realtime_analysis.db"
        self._init_database()
        
        # Cache for AFP articles
        self.afp_cache = {}
        self.comparison_results = []
        
    def _init_database(self):
        """Initialize SQLite database for real-time results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # AFP articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS afp_articles (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                category TEXT,
                timestamp DATETIME,
                reliability_score REAL,
                keywords TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Comparison results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                afp_id TEXT,
                source_type TEXT,
                source_id TEXT,
                similarity_score REAL,
                deformation_score REAL,
                objectivity_score REAL,
                sentiment_diff REAL,
                key_differences TEXT,
                timestamp DATETIME,
                FOREIGN KEY (afp_id) REFERENCES afp_articles(id)
            )
        ''')
        
        # Real-time metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_metrics (
                timestamp DATETIME PRIMARY KEY,
                afp_count INTEGER,
                reddit_count INTEGER,
                gdelt_count INTEGER,
                avg_similarity REAL,
                avg_deformation REAL,
                avg_objectivity REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("✅ Database initialized")
    
    def create_spark_session(self):
        """Create Spark session with Kafka support"""
        try:
            self.spark = SparkSession.builder \
                .appName("AFP-RealTime-Comparison") \
                .master("local[*]") \
                .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
                .config("spark.sql.streaming.checkpointLocation", "./checkpoints") \
                .config("spark.streaming.stopGracefullyOnShutdown", "true") \
                .config("spark.sql.shuffle.partitions", "4") \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            self.logger.info("✅ Spark Session created successfully with Kafka support")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create Spark session: {e}")
            return False
    
    def start_streaming(self):
        """Start consuming from all Kafka topics"""
        if not self.create_spark_session():
            return
        
        try:
            self.logger.info("🚀 Starting Kafka stream consumption...")
            
            # Read from multiple Kafka topics
            # Use environment variable so the container can reach Kafka (e.g. 'kafka:29092')
            kafka_bootstrap = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

            kafka_stream = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", kafka_bootstrap) \
                .option("subscribe", "afp_news_stream,reddit_comparison_stream,gdelt_comparison_stream") \
                .option("startingOffsets", "latest") \
                .option("failOnDataLoss", "false") \
                .load()
            
            # Parse JSON messages
            schema = StructType([
                StructField("message_id", StringType(), True),
                StructField("timestamp", StringType(), True),
                StructField("source", StringType(), True),
                StructField("source_type", StringType(), True),
                StructField("title", StringType(), True),
                StructField("content", StringType(), True),
                StructField("category", StringType(), True),
                StructField("metadata", MapType(StringType(), StringType()), True)
            ])
            
            parsed_stream = kafka_stream.select(
                col("topic").alias("kafka_topic"),
                from_json(col("value").cast("string"), schema).alias("data"),
                col("timestamp").alias("kafka_timestamp")
            ).select(
                col("kafka_topic"),
                col("data.*"),
                col("kafka_timestamp")
            )
            
            # Process stream in batches
            query = parsed_stream.writeStream \
                .foreachBatch(self.process_batch) \
                .outputMode("append") \
                .trigger(processingTime='5 seconds') \
                .start()
            
            self.logger.info("✅ Streaming started successfully")
            self.logger.info("📊 Dashboard: Open streamlit run dashboard_afp_realtime.py")
            
            query.awaitTermination()
            
        except Exception as e:
            self.logger.error(f"❌ Streaming error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.spark:
                self.spark.stop()
    
    def process_batch(self, batch_df, batch_id):
        """Process each micro-batch of data"""
        try:
            if batch_df.isEmpty():
                return
            
            self.logger.info(f"🔄 Processing batch {batch_id} with {batch_df.count()} messages")
            
            # Convert to Pandas for easier processing
            batch_pd = batch_df.toPandas()
            
            # Separate by source
            afp_messages = batch_pd[batch_pd['source'] == 'AFP']
            reddit_messages = batch_pd[batch_pd['source'] == 'Reddit']
            gdelt_messages = batch_pd[batch_pd['source'] == 'GDELT']
            
            # Store AFP articles
            for _, afp_msg in afp_messages.iterrows():
                self._store_afp_article(afp_msg)
            
            # Compare with AFP articles
            for _, reddit_msg in reddit_messages.iterrows():
                self._compare_with_afp(reddit_msg, 'Reddit')
            
            for _, gdelt_msg in gdelt_messages.iterrows():
                self._compare_with_afp(gdelt_msg, 'GDELT')
            
            # Update real-time metrics
            self._update_metrics(len(afp_messages), len(reddit_messages), len(gdelt_messages))
            
            self.logger.info(f"✅ Batch {batch_id} processed: AFP={len(afp_messages)}, Reddit={len(reddit_messages)}, GDELT={len(gdelt_messages)}")
            
        except Exception as e:
            self.logger.error(f"❌ Error processing batch {batch_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def _store_afp_article(self, afp_msg):
        """Store AFP article in database and cache"""
        try:
            article_id = afp_msg['message_id']
            
            # Cache
            self.afp_cache[article_id] = {
                'title': afp_msg['title'],
                'content': afp_msg['content'],
                'category': afp_msg['category'],
                'timestamp': afp_msg['timestamp'],
                'metadata': json.loads(afp_msg['metadata']) if isinstance(afp_msg['metadata'], str) else afp_msg['metadata']
            }
            
            # Database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metadata = afp_msg.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            cursor.execute('''
                INSERT OR REPLACE INTO afp_articles 
                (id, title, content, category, timestamp, reliability_score, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id,
                afp_msg['title'],
                afp_msg['content'],
                afp_msg.get('category', 'unknown'),
                afp_msg['timestamp'],
                metadata.get('reliability_score', 0.98),
                ','.join(metadata.get('keywords', []))
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📰 Stored AFP article: {article_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error storing AFP article: {e}")
    
    def _compare_with_afp(self, message, source_type):
        """Compare Reddit/GDELT message with AFP articles using AI"""
        try:
            if not self.afp_cache:
                return
            
            message_content = message['content']
            message_title = message['title']
            combined_message = f"{message_title} {message_content}"
            
            best_match = None
            best_similarity = 0
            
            # Find most similar AFP article
            for afp_id, afp_article in self.afp_cache.items():
                afp_combined = f"{afp_article['title']} {afp_article['content']}"
                
                # Calculate text similarity using TF-IDF
                similarity = self._calculate_similarity(combined_message, afp_combined)
                
                if similarity > best_similarity and similarity > 0.3:  # Threshold
                    best_similarity = similarity
                    best_match = (afp_id, afp_article)
            
            if best_match:
                afp_id, afp_article = best_match
                
                # Perform detailed comparison
                comparison = self._detailed_comparison(
                    afp_article,
                    {
                        'title': message_title,
                        'content': message_content,
                        'source_id': message['message_id'],
                        'source_type': source_type
                    }
                )
                
                comparison['similarity_score'] = best_similarity
                comparison['afp_id'] = afp_id
                
                # Store comparison result
                self._store_comparison(comparison)
                
                self.logger.info(f"🔍 Match found: {source_type} ({best_similarity:.2%} similarity)")
            
        except Exception as e:
            self.logger.error(f"❌ Error comparing with AFP: {e}")
    
    def _calculate_similarity(self, text1, text2):
        """Calculate text similarity using TF-IDF and cosine similarity"""
        try:
            # Preprocess
            text1 = text1.lower()[:1000]  # Limit length
            text2 = text2.lower()[:1000]
            
            # TF-IDF vectorization
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
            
            # Cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating similarity: {e}")
            return 0.0
    
    def _detailed_comparison(self, afp_article, source_message):
        """Perform detailed AI-powered comparison"""
        try:
            afp_content = afp_article['content']
            source_content = source_message['content']
            
            # 1. Sentiment Analysis
            afp_sentiment = self.vader.polarity_scores(afp_content)
            source_sentiment = self.vader.polarity_scores(source_content)
            sentiment_diff = abs(afp_sentiment['compound'] - source_sentiment['compound'])
            
            # 2. Objectivity Score (based on sentiment neutrality and language)
            afp_objectivity = self._calculate_objectivity(afp_content, afp_sentiment)
            source_objectivity = self._calculate_objectivity(source_content, source_sentiment)
            
            # 3. Deformation Score (how much the information has changed)
            deformation_score = self._calculate_deformation(
                afp_content, source_content, sentiment_diff
            )
            
            # 4. Key Differences
            key_differences = self._extract_key_differences(afp_content, source_content)
            
            return {
                'source_id': source_message['source_id'],
                'source_type': source_message['source_type'],
                'sentiment_diff': sentiment_diff,
                'afp_objectivity': afp_objectivity,
                'source_objectivity': source_objectivity,
                'objectivity_score': abs(afp_objectivity - source_objectivity),
                'deformation_score': deformation_score,
                'key_differences': json.dumps(key_differences),
                'afp_sentiment': afp_sentiment['compound'],
                'source_sentiment': source_sentiment['compound'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in detailed comparison: {e}")
            return {}
    
    def _calculate_objectivity(self, text, sentiment):
        """Calculate objectivity score (0-1, higher = more objective)"""
        # Factors:
        # 1. Sentiment neutrality (compound close to 0)
        # 2. Balanced positive/negative words
        # 3. Lack of extreme words
        
        sentiment_neutrality = 1 - abs(sentiment['compound'])
        balance = 1 - abs(sentiment['pos'] - sentiment['neg'])
        
        # Count subjective words
        subjective_words = ['amazing', 'terrible', 'horrible', 'wonderful', 
                           'awful', 'fantastic', 'disgusting', 'brilliant']
        subjective_count = sum(1 for word in subjective_words if word in text.lower())
        subjectivity_penalty = min(0.5, subjective_count * 0.05)
        
        objectivity = (sentiment_neutrality * 0.5 + balance * 0.5) - subjectivity_penalty
        return max(0, min(1, objectivity))
    
    def _calculate_deformation(self, afp_content, source_content, sentiment_diff):
        """Calculate information deformation score"""
        # Factors:
        # 1. Sentiment difference
        # 2. Content similarity (inverse)
        # 3. Key facts preservation
        
        similarity = self._calculate_similarity(afp_content, source_content)
        content_change = 1 - similarity
        
        # Deformation score: weighted combination
        deformation = (
            sentiment_diff * 0.4 +
            content_change * 0.4 +
            (1 - self._check_facts_preserved(afp_content, source_content)) * 0.2
        )
        
        return min(1, deformation)
    
    def _check_facts_preserved(self, afp_content, source_content):
        """Check if key facts are preserved"""
        # Extract numbers and key entities
        import re
        
        afp_numbers = set(re.findall(r'\d+', afp_content))
        source_numbers = set(re.findall(r'\d+', source_content))
        
        if not afp_numbers:
            return 0.8  # No numbers to compare
        
        # Jaccard similarity of numbers
        intersection = len(afp_numbers & source_numbers)
        union = len(afp_numbers | source_numbers)
        
        return intersection / union if union > 0 else 0
    
    def _extract_key_differences(self, afp_content, source_content):
        """Extract key differences between AFP and source"""
        differences = []
        
        # Sentiment difference
        afp_sent = self.vader.polarity_scores(afp_content)
        source_sent = self.vader.polarity_scores(source_content)
        
        if abs(afp_sent['compound'] - source_sent['compound']) > 0.2:
            differences.append({
                'type': 'sentiment',
                'afp': afp_sent['compound'],
                'source': source_sent['compound'],
                'description': 'Significant sentiment difference detected'
            })
        
        # Length difference
        afp_length = len(afp_content.split())
        source_length = len(source_content.split())
        
        if abs(afp_length - source_length) / max(afp_length, source_length) > 0.5:
            differences.append({
                'type': 'length',
                'afp': afp_length,
                'source': source_length,
                'description': 'Significant length difference'
            })
        
        return differences[:5]  # Top 5 differences
    
    def _store_comparison(self, comparison):
        """Store comparison result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO comparisons
                (afp_id, source_type, source_id, similarity_score, deformation_score,
                 objectivity_score, sentiment_diff, key_differences, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comparison['afp_id'],
                comparison['source_type'],
                comparison['source_id'],
                comparison['similarity_score'],
                comparison['deformation_score'],
                comparison['objectivity_score'],
                comparison['sentiment_diff'],
                comparison['key_differences'],
                comparison['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error storing comparison: {e}")
    
    def _update_metrics(self, afp_count, reddit_count, gdelt_count):
        """Update real-time metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent comparisons for averages
            cursor.execute('''
                SELECT AVG(similarity_score), AVG(deformation_score), AVG(objectivity_score)
                FROM comparisons
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            
            result = cursor.fetchone()
            avg_similarity = result[0] or 0
            avg_deformation = result[1] or 0
            avg_objectivity = result[2] or 0
            
            cursor.execute('''
                INSERT INTO realtime_metrics
                (timestamp, afp_count, reddit_count, gdelt_count, 
                 avg_similarity, avg_deformation, avg_objectivity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                afp_count,
                reddit_count,
                gdelt_count,
                avg_similarity,
                avg_deformation,
                avg_objectivity
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error updating metrics: {e}")

def main():
    """Main entry point"""
    print("=" * 70)
    print("⚡ AFP REAL-TIME COMPARISON ENGINE")
    print("=" * 70)
    print("Features:")
    print("  • Real-time Kafka stream processing")
    print("  • AI-powered content similarity analysis")
    print("  • Deformation & objectivity scoring")
    print("  • Multi-source comparison (AFP vs Reddit vs GDELT)")
    print("=" * 70)
    print()
    
    comparator = AFPRealtimeComparator()
    
    try:
        comparator.start_streaming()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping AFP Real-Time Comparator...")
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
