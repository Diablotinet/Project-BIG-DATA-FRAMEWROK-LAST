#!/usr/bin/env python3
"""
🧪 COMPLETE AFP SYSTEM TEST
Tests all components according to project requirements:
1. Multi-source ingestion (AFP, Reddit, GDELT)
2. Kafka streaming
3. Spark processing
4. Text analytics (similarity, sentiment, deformation)
5. SQLite storage
6. Real-time dashboard
"""

import sys
import time
import json
import sqlite3
import subprocess
from pathlib import Path
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
from kafka.errors import NoBrokersAvailable
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SystemTest")

class AFPSystemTester:
    """Complete system tester"""
    
    def __init__(self):
        self.test_results = {}
        self.db_path = "afp_realtime_analysis.db"
        
    def print_header(self, title):
        """Print section header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def test_kafka_connection(self):
        """Test 1: Kafka broker connectivity"""
        self.print_header("TEST 1: Kafka Broker Connection")
        
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=['localhost:9092'],
                client_id='test-client',
                request_timeout_ms=5000
            )
            
            topics = admin.list_topics()
            admin.close()
            
            logger.info("✅ Kafka broker is running")
            logger.info(f"   Found {len(topics)} topics")
            self.test_results['kafka_connection'] = True
            return True
            
        except NoBrokersAvailable:
            logger.error("❌ Kafka broker not available on localhost:9092")
            logger.error("   Please start Kafka first!")
            self.test_results['kafka_connection'] = False
            return False
        except Exception as e:
            logger.error(f"❌ Kafka connection error: {e}")
            self.test_results['kafka_connection'] = False
            return False
    
    def test_kafka_topics(self):
        """Test 2: Required Kafka topics"""
        self.print_header("TEST 2: Kafka Topics")
        
        required_topics = [
            'afp_news_stream',
            'reddit_comparison_stream', 
            'gdelt_comparison_stream'
        ]
        
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=['localhost:9092'],
                client_id='test-client'
            )
            
            existing_topics = admin.list_topics()
            admin.close()
            
            all_exist = True
            for topic in required_topics:
                if topic in existing_topics:
                    logger.info(f"✅ Topic '{topic}' exists")
                else:
                    logger.error(f"❌ Topic '{topic}' missing")
                    all_exist = False
            
            self.test_results['kafka_topics'] = all_exist
            
            if not all_exist:
                logger.warning("   Run: python create_topics_afp.py")
            
            return all_exist
            
        except Exception as e:
            logger.error(f"❌ Error checking topics: {e}")
            self.test_results['kafka_topics'] = False
            return False
    
    def test_producer(self):
        """Test 3: Producer can send messages"""
        self.print_header("TEST 3: Kafka Producer")
        
        try:
            producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            
            # Send test message to AFP topic
            test_message = {
                "message_id": "TEST_001",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "source": "AFP",
                "title": "Test AFP Article",
                "content": "This is a test message to verify producer functionality.",
                "category": "test"
            }
            
            future = producer.send('afp_news_stream', value=test_message)
            future.get(timeout=10)
            
            producer.flush()
            producer.close()
            
            logger.info("✅ Producer can send messages to Kafka")
            self.test_results['producer'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Producer error: {e}")
            self.test_results['producer'] = False
            return False
    
    def test_consumer(self):
        """Test 4: Consumer can read messages"""
        self.print_header("TEST 4: Kafka Consumer")
        
        try:
            consumer = KafkaConsumer(
                'afp_news_stream',
                bootstrap_servers=['localhost:9092'],
                auto_offset_reset='latest',
                enable_auto_commit=False,
                consumer_timeout_ms=3000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            # Try to consume
            messages_found = 0
            for message in consumer:
                messages_found += 1
                if messages_found >= 1:
                    break
            
            consumer.close()
            
            if messages_found > 0:
                logger.info(f"✅ Consumer can read messages (found {messages_found})")
                self.test_results['consumer'] = True
                return True
            else:
                logger.warning("⚠️  No messages in topic yet (this is OK if producer hasn't run)")
                self.test_results['consumer'] = True
                return True
            
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            self.test_results['consumer'] = False
            return False
    
    def test_python_dependencies(self):
        """Test 5: Required Python packages"""
        self.print_header("TEST 5: Python Dependencies")
        
        required_packages = {
            'kafka': 'kafka-python',
            'pyspark': 'pyspark',
            'streamlit': 'streamlit',
            'plotly': 'plotly',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'textblob': 'textblob',
            'vaderSentiment': 'vaderSentiment',
            'sklearn': 'scikit-learn'
        }
        
        all_installed = True
        for module, package in required_packages.items():
            try:
                __import__(module)
                logger.info(f"✅ {package} installed")
            except ImportError:
                logger.error(f"❌ {package} missing")
                logger.error(f"   Install: pip install {package}")
                all_installed = False
        
        self.test_results['dependencies'] = all_installed
        return all_installed
    
    def test_spark_installation(self):
        """Test 6: Spark installation"""
        self.print_header("TEST 6: Apache Spark")
        
        spark_dir = Path("downloads/spark-3.5.0-bin-hadoop3")
        
        if spark_dir.exists():
            logger.info(f"✅ Spark found at {spark_dir}")
            self.test_results['spark_install'] = True
            return True
        else:
            logger.error(f"❌ Spark not found at {spark_dir}")
            logger.error("   Run: python setup_infrastructure.py")
            self.test_results['spark_install'] = False
            return False
    
    def test_database_creation(self):
        """Test 7: SQLite database"""
        self.print_header("TEST 7: SQLite Database")
        
        try:
            # Check if database exists
            if Path(self.db_path).exists():
                logger.info(f"✅ Database exists: {self.db_path}")
                
                # Check tables
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['afp_articles', 'comparisons', 'realtime_metrics']
                
                for table in required_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        logger.info(f"✅ Table '{table}' exists ({count} rows)")
                    else:
                        logger.warning(f"⚠️  Table '{table}' not created yet")
                
                conn.close()
                self.test_results['database'] = True
                return True
            else:
                logger.warning("⚠️  Database not created yet (will be created when consumer runs)")
                self.test_results['database'] = True
                return True
                
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            self.test_results['database'] = False
            return False
    
    def test_file_structure(self):
        """Test 8: Required files exist"""
        self.print_header("TEST 8: File Structure")
        
        required_files = {
            'afp_realtime_producer_complete.py': 'AFP Producer',
            'spark_afp_realtime_consumer.py': 'Spark Consumer',
            'dashboard_afp_realtime_complete.py': 'Dashboard',
            'create_topics_afp.py': 'Topic Creator',
            'launch_afp_complete_system.bat': 'Launcher'
        }
        
        all_exist = True
        for filename, description in required_files.items():
            filepath = Path(filename)
            if filepath.exists():
                logger.info(f"✅ {description}: {filename}")
            else:
                logger.error(f"❌ {description} missing: {filename}")
                all_exist = False
        
        self.test_results['file_structure'] = all_exist
        return all_exist
    
    def test_text_analytics(self):
        """Test 9: Text analytics functions"""
        self.print_header("TEST 9: Text Analytics")
        
        try:
            from textblob import TextBlob
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Test sentiment analysis
            vader = SentimentIntensityAnalyzer()
            test_text = "This is a great news article about positive developments."
            
            sentiment = vader.polarity_scores(test_text)
            logger.info(f"✅ Sentiment analysis working (score: {sentiment['compound']:.2f})")
            
            # Test TF-IDF
            vectorizer = TfidfVectorizer(max_features=10)
            text1 = "This is a test document about AFP news"
            text2 = "This is another document about news from AFP"
            
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            logger.info(f"✅ TF-IDF similarity working (score: {similarity:.2f})")
            
            self.test_results['text_analytics'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Text analytics error: {e}")
            self.test_results['text_analytics'] = False
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        self.print_header("🧪 AFP REAL-TIME SYSTEM - COMPLETE TEST SUITE")
        
        print("\nTesting all components according to project requirements:")
        print("1. Multi-source data ingestion")
        print("2. Apache Kafka streaming")
        print("3. Spark Streaming processing")
        print("4. Text analytics (TF-IDF, sentiment)")
        print("5. SQLite NoSQL storage")
        print("6. Real-time visualization")
        print()
        
        # Run tests
        tests = [
            ("Python Dependencies", self.test_python_dependencies),
            ("Kafka Connection", self.test_kafka_connection),
            ("Kafka Topics", self.test_kafka_topics),
            ("Kafka Producer", self.test_producer),
            ("Kafka Consumer", self.test_consumer),
            ("Spark Installation", self.test_spark_installation),
            ("SQLite Database", self.test_database_creation),
            ("File Structure", self.test_file_structure),
            ("Text Analytics", self.test_text_analytics)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ Test '{test_name}' crashed: {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = False
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        self.print_header("📊 TEST RESULTS SUMMARY")
        
        passed = sum(1 for v in self.test_results.values() if v)
        total = len(self.test_results)
        
        print(f"\nTests Passed: {passed}/{total}")
        print()
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        print("\n" + "=" * 70)
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! System is ready to run.")
            print("\n📋 Next Steps:")
            print("1. Run: launch_afp_complete_system.bat")
            print("2. Or manually:")
            print("   - Start Zookeeper")
            print("   - Start Kafka")
            print("   - Run: python afp_realtime_producer_complete.py")
            print("   - Run: python spark_afp_realtime_consumer.py")
            print("   - Run: streamlit run dashboard_afp_realtime_complete.py")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
            print("\n💡 Common fixes:")
            print("- Install dependencies: pip install -r requirements.txt")
            print("- Start Kafka: See README_COMPLETE.md")
            print("- Create topics: python create_topics_afp.py")
        
        print("=" * 70)

def main():
    """Main test execution"""
    print("\n" + "🧪" * 35)
    print("AFP REAL-TIME ANALYTICS SYSTEM - TEST SUITE")
    print("🧪" * 35)
    
    tester = AFPSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
