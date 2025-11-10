# ⚡ SPARK STREAMING CONSUMER - REAL-TIME ANALYTICS
# Multi-Source Data Processing with Apache Spark Streaming
# Text Analytics, Sentiment Analysis, Trending Keywords, Anomaly Detection

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import re
import argparse
import socket
from pyspark.sql import SparkSession
from py4j.protocol import Py4JJavaError

# Configuration pour trouver Spark
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

import findspark
findspark.init()

from pyspark import SparkContext, SparkConf
from pyspark.streaming import StreamingContext
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import Tokenizer, StopWordsRemover, CountVectorizer
from pyspark.ml.clustering import LDA
import pymongo
from pymongo import MongoClient
import numpy as np
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from collections import deque

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('spark_streaming.log'),
        logging.StreamHandler()
    ]
)

class StreamingAnalytics:
    """Analyseur principal pour les streams en temps réel"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger("StreamingAnalytics")
        
        # Initialisation de Spark
        self.spark = self._init_spark()
        self.streaming_context = None
        
        # Stockage MongoDB
        self.mongo_client = None
        self.db = None
        self._init_mongodb()
        
        # Analyseurs de sentiment
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Stockage temps réel pour analytics
        self.real_time_data = {
            'trending_keywords': deque(maxlen=1000),
            'sentiment_trends': deque(maxlen=1000),
            'anomalies': deque(maxlen=100),
            'source_stats': defaultdict(lambda: {'count': 0, 'sentiment_sum': 0}),
            'recent_messages': deque(maxlen=500)
        }
        
        # Lexiques de sentiment personnalisés
        self.positive_words = self._load_sentiment_lexicon('positive')
        self.negative_words = self._load_sentiment_lexicon('negative')
        
        # Mots vides étendus
        self.stop_words = self._load_stop_words()
        
        # Patterns de trending topics
        self.trending_patterns = {
            'breaking_news': [r'\bbreaking\b', r'\burgent\b', r'\balert\b'],
            'viral_content': [r'\bviral\b', r'\btrending\b', r'\bpopular\b'],
            'crisis': [r'\bcrisis\b', r'\bemergency\b', r'\bdisaster\b']
        }
    
    def _init_spark(self) -> SparkSession:
        """Initialise Spark Session avec configuration optimisée"""
        conf = SparkConf().setAppName("MultiSourceAnalytics") \
                         .setMaster("local[*]") \
                         .set("spark.sql.adaptive.enabled", "true") \
                         .set("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                         .set("spark.streaming.stopGracefullyOnShutdown", "true") \
                         .set("spark.sql.streaming.metricsEnabled", "true")
        
        spark = SparkSession.builder.config(conf=conf).getOrCreate()
        spark.sparkContext.setLogLevel("WARN")
        
        self.logger.info("✅ Spark Session initialisée")
        return spark
    
    def _init_mongodb(self):
        """Initialise la connexion MongoDB"""
        try:
            mongo_config = self.config.get('mongodb', {})
            connection_string = mongo_config.get('connection_string', 'mongodb://localhost:27017/')
            
            self.mongo_client = MongoClient(connection_string)
            self.db = self.mongo_client[mongo_config.get('database', 'multi_source_analytics')]
            
            # Test de connexion
            self.mongo_client.admin.command('ping')
            self.logger.info("✅ Connexion MongoDB réussie")
            
        except Exception as e:
            self.logger.warning(f"⚠️ MongoDB non disponible: {e}, stockage en mémoire uniquement")
            self.mongo_client = None
            self.db = None
    
    def _load_sentiment_lexicon(self, sentiment_type: str) -> set:
        """Charge les lexiques de sentiment"""
        # Lexiques simplifiés (en production, utiliser des lexiques complets)
        if sentiment_type == 'positive':
            return {
                'excellent', 'amazing', 'great', 'awesome', 'fantastic', 'wonderful',
                'good', 'better', 'best', 'perfect', 'outstanding', 'brilliant',
                'success', 'achievement', 'victory', 'win', 'progress', 'advance',
                'love', 'like', 'enjoy', 'happy', 'excited', 'thrilled',
                'innovation', 'breakthrough', 'revolutionary', 'incredible'
            }
        else:  # negative
            return {
                'terrible', 'awful', 'horrible', 'disgusting', 'worst', 'bad',
                'worse', 'failed', 'failure', 'disaster', 'crisis', 'problem',
                'issue', 'concern', 'worry', 'fear', 'hate', 'dislike',
                'angry', 'frustrated', 'disappointed', 'sad', 'devastated',
                'dangerous', 'threat', 'risk', 'warning', 'alert'
            }
    
    def _load_stop_words(self) -> set:
        """Charge une liste étendue de mots vides"""
        basic_stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'have', 'had', 'but', 'or',
            'this', 'these', 'they', 'them', 'their', 'we', 'our', 'you', 'your'
        }
        
        # Mots vides spécifiques aux réseaux sociaux
        social_stop_words = {
            'rt', 'http', 'https', 'www', 'com', 'co', 'via', 'amp',
            'like', 'follow', 'share', 'retweet', 'comment', 'subscribe'
        }
        
        return basic_stop_words.union(social_stop_words)
    
    def preprocess_text(self, text: str) -> List[str]:
        """Préprocessing du texte pour l'analyse"""
        if not text or not isinstance(text, str):
            return []
        
        # Nettoyer le texte
        text = text.lower()
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'@\w+', '', text)  # Mentions
        text = re.sub(r'#\w+', '', text)  # Hashtags (optionnel)
        text = re.sub(r'[^\w\s]', ' ', text)  # Ponctuation
        text = re.sub(r'\s+', ' ', text)  # Espaces multiples
        
        # Tokenisation
        words = text.split()
        
        # Filtrage
        words = [w for w in words if len(w) > 2 and w not in self.stop_words]
        
        return words
    
    def analyze_sentiment_comprehensive(self, text: str) -> Dict:
        """Analyse de sentiment comprehensive avec plusieurs méthodes"""
        if not text:
            return {'compound': 0, 'method': 'none', 'confidence': 0}
        
        # 1. VADER (optimisé pour réseaux sociaux)
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # 2. TextBlob
        try:
            blob = TextBlob(text)
            textblob_score = blob.sentiment.polarity
        except:
            textblob_score = 0
        
        # 3. Lexicon-based analysis
        words = self.preprocess_text(text)
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            lexicon_score = (positive_count - negative_count) / total_sentiment_words
        else:
            lexicon_score = 0
        
        # Combinaison pondérée des scores
        weights = {'vader': 0.5, 'textblob': 0.3, 'lexicon': 0.2}
        combined_score = (
            weights['vader'] * vader_scores['compound'] +
            weights['textblob'] * textblob_score +
            weights['lexicon'] * lexicon_score
        )
        
        # Calcul de confiance
        agreement_scores = [vader_scores['compound'], textblob_score, lexicon_score]
        confidence = 1 - np.std(agreement_scores) if len(set(agreement_scores)) > 1 else 1
        
        return {
            'compound': combined_score,
            'positive': vader_scores['pos'],
            'negative': vader_scores['neg'],
            'neutral': vader_scores['neu'],
            'confidence': confidence,
            'method': 'combined',
            'details': {
                'vader': vader_scores['compound'],
                'textblob': textblob_score,
                'lexicon': lexicon_score,
                'positive_words': positive_count,
                'negative_words': negative_count
            }
        }
    
    def extract_keywords_and_trends(self, texts: List[str], window_size: int = 100) -> Dict:
        """Extraction de mots-clés et détection de tendances"""
        all_words = []
        pattern_matches = defaultdict(int)
        
        for text in texts[-window_size:]:  # Fenêtre glissante
            words = self.preprocess_text(text)
            all_words.extend(words)
            
            # Détection de patterns
            text_lower = text.lower()
            for pattern_name, patterns in self.trending_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        pattern_matches[pattern_name] += 1
        
        # Comptage des mots
        word_counts = Counter(all_words)
        
        # Filtrage des mots les plus fréquents
        trending_keywords = []
        for word, count in word_counts.most_common(20):
            if count >= 2:  # Seuil minimum
                # Calcul du score de trending (fréquence récente vs fréquence historique)
                recent_count = sum(1 for text in texts[-10:] if word in self.preprocess_text(text))
                trending_score = recent_count / min(10, len(texts))
                
                trending_keywords.append({
                    'keyword': word,
                    'count': count,
                    'trending_score': trending_score,
                    'category': self._categorize_keyword(word)
                })
        
        return {
            'trending_keywords': sorted(trending_keywords, key=lambda x: x['trending_score'], reverse=True),
            'pattern_matches': dict(pattern_matches),
            'total_words': len(all_words),
            'unique_words': len(word_counts)
        }
    
    def _categorize_keyword(self, word: str) -> str:
        """Catégorise un mot-clé"""
        tech_words = {'ai', 'technology', 'innovation', 'digital', 'cyber', 'tech', 'data', 'algorithm'}
        politics_words = {'government', 'policy', 'election', 'politics', 'minister', 'president'}
        environment_words = {'climate', 'environment', 'green', 'sustainable', 'carbon', 'energy'}
        health_words = {'health', 'medical', 'hospital', 'treatment', 'vaccine', 'disease'}
        
        word_lower = word.lower()
        
        if word_lower in tech_words:
            return 'technology'
        elif word_lower in politics_words:
            return 'politics'
        elif word_lower in environment_words:
            return 'environment'
        elif word_lower in health_words:
            return 'health'
        else:
            return 'general'
    
    def detect_anomalies(self, current_metrics: Dict, historical_data: List[Dict]) -> List[Dict]:
        """Détection d'anomalies dans les métriques"""
        anomalies = []
        
        if len(historical_data) < 10:  # Pas assez de données historiques
            return anomalies
        
        # Analyser différentes métriques
        metrics_to_check = ['message_count', 'average_sentiment', 'unique_keywords']
        
        for metric in metrics_to_check:
            if metric in current_metrics:
                current_value = current_metrics[metric]
                historical_values = [data.get(metric, 0) for data in historical_data[-20:]]
                
                if historical_values:
                    mean_value = np.mean(historical_values)
                    std_value = np.std(historical_values)
                    
                    # Z-score pour détection d'anomalie
                    if std_value > 0:
                        z_score = abs(current_value - mean_value) / std_value
                        
                        if z_score > 2.5:  # Seuil d'anomalie
                            anomaly = {
                                'type': 'statistical_anomaly',
                                'metric': metric,
                                'current_value': current_value,
                                'expected_value': mean_value,
                                'z_score': z_score,
                                'severity': 'high' if z_score > 3 else 'medium',
                                'timestamp': datetime.now().isoformat(),
                                'description': f"Valeur anormale pour {metric}: {current_value:.2f} (attendu: {mean_value:.2f})"
                            }
                            anomalies.append(anomaly)
        
        # Détection d'anomalies de sentiment
        if 'sentiment_distribution' in current_metrics:
            sentiment_dist = current_metrics['sentiment_distribution']
            
            # Alerte si plus de 80% de sentiment négatif
            if sentiment_dist.get('negative', 0) > 0.8:
                anomalies.append({
                    'type': 'sentiment_anomaly',
                    'metric': 'negative_sentiment',
                    'current_value': sentiment_dist['negative'],
                    'severity': 'high',
                    'timestamp': datetime.now().isoformat(),
                    'description': f"Pic de sentiment négatif: {sentiment_dist['negative']:.1%}"
                })
        
        return anomalies
    
    def process_stream_batch(self, messages: List[Dict]) -> Dict:
        """Traite un batch de messages du stream"""
        if not messages:
            return {}
        
        batch_start = time.time()
        results = {
            'batch_size': len(messages),
            'timestamp': datetime.now().isoformat(),
            'processing_time': 0,
            'sources': defaultdict(int),
            'sentiment_analysis': {},
            'trending_analysis': {},
            'anomalies': [],
            'processed_messages': []
        }
        
        # Extraction des textes et métadonnées
        texts = []
        sentiments = []
        
        for msg in messages:
            try:
                # Parsing du message JSON
                if isinstance(msg, str):
                    data = json.loads(msg)
                else:
                    data = msg
                
                content = data.get('content', '')
                source = data.get('source', 'unknown')
                source_type = data.get('source_type', 'unknown')
                
                texts.append(content)
                results['sources'][f"{source_type}_{source}"] += 1
                
                # Analyse de sentiment
                sentiment_result = self.analyze_sentiment_comprehensive(content)
                sentiments.append(sentiment_result['compound'])
                
                # Message traité
                processed_msg = {
                    'message_id': data.get('message_id'),
                    'timestamp': data.get('timestamp'),
                    'source': source,
                    'source_type': source_type,
                    'content_length': len(content),
                    'sentiment': sentiment_result,
                    'keywords': self.preprocess_text(content)[:10]  # Top 10 keywords
                }
                results['processed_messages'].append(processed_msg)
                
                # Stockage en temps réel
                self.real_time_data['recent_messages'].append(processed_msg)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur traitement message: {e}")
                continue
        
        # Analyse de sentiment globale
        if sentiments:
            results['sentiment_analysis'] = {
                'average_sentiment': np.mean(sentiments),
                'sentiment_std': np.std(sentiments),
                'positive_ratio': sum(1 for s in sentiments if s > 0.1) / len(sentiments),
                'negative_ratio': sum(1 for s in sentiments if s < -0.1) / len(sentiments),
                'neutral_ratio': sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments),
                'sentiment_distribution': {
                    'positive': sum(1 for s in sentiments if s > 0.1) / len(sentiments),
                    'negative': sum(1 for s in sentiments if s < -0.1) / len(sentiments),
                    'neutral': sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments)
                }
            }
        
        # Analyse des tendances
        if texts:
            trending_analysis = self.extract_keywords_and_trends(texts)
            results['trending_analysis'] = trending_analysis
            
            # Mise à jour des données temps réel
            for keyword_data in trending_analysis['trending_keywords'][:10]:
                self.real_time_data['trending_keywords'].append({
                    'keyword': keyword_data['keyword'],
                    'score': keyword_data['trending_score'],
                    'timestamp': datetime.now().isoformat()
                })
        
        # Détection d'anomalies
        current_metrics = {
            'message_count': len(messages),
            'average_sentiment': results['sentiment_analysis'].get('average_sentiment', 0),
            'unique_keywords': len(results['trending_analysis'].get('trending_keywords', [])),
            'sentiment_distribution': results['sentiment_analysis'].get('sentiment_distribution', {})
        }
        
        # Récupérer les données historiques pour comparaison
        historical_data = list(self.real_time_data['recent_messages'])[-50:]
        historical_metrics = []
        
        # Calculer métriques historiques par fenêtres
        window_size = 10
        for i in range(0, len(historical_data), window_size):
            window = historical_data[i:i+window_size]
            if len(window) >= 5:  # Minimum pour une métrique valide
                window_sentiment = [msg['sentiment']['compound'] for msg in window if 'sentiment' in msg]
                if window_sentiment:
                    historical_metrics.append({
                        'message_count': len(window),
                        'average_sentiment': np.mean(window_sentiment),
                        'unique_keywords': len(set(kw for msg in window for kw in msg.get('keywords', [])))
                    })
        
        anomalies = self.detect_anomalies(current_metrics, historical_metrics)
        results['anomalies'] = anomalies
        
        # Sauvegarder les anomalies
        for anomaly in anomalies:
            self.real_time_data['anomalies'].append(anomaly)
        
        # Temps de traitement
        results['processing_time'] = time.time() - batch_start
        
        # Stockage MongoDB si disponible
        if self.db:
            try:
                self.db.batch_results.insert_one(results)
            except Exception as e:
                self.logger.error(f"❌ Erreur stockage MongoDB: {e}")
        
        return results
    
    def start_streaming(self):
        """Démarre le streaming Spark"""
        self.logger.info("🚀 Démarrage Spark Streaming...")
        
        try:
            # Configuration Kafka
            kafka_config = self.config['kafka']
            bootstrap_servers = ','.join(kafka_config['bootstrap_servers'])
            topics = ','.join(kafka_config['topics'].keys())
            
            # Lecture stream Kafka
            df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", bootstrap_servers) \
                .option("subscribe", topics) \
                .option("startingOffsets", "latest") \
                .load()
            
            # Schéma pour les messages
            message_schema = StructType([
                StructField("message_id", StringType(), True),
                StructField("timestamp", StringType(), True),
                StructField("source", StringType(), True),
                StructField("source_type", StringType(), True),
                StructField("content", StringType(), True),
                StructField("sentiment_score", FloatType(), True),
                StructField("location", MapType(StringType(), StringType()), True),
                StructField("metadata", MapType(StringType(), StringType()), True)
            ])
            
            # Parsing des messages JSON
            parsed_df = df.select(
                col("topic").alias("kafka_topic"),
                col("partition"),
                col("offset"),
                col("timestamp").alias("kafka_timestamp"),
                from_json(col("value").cast("string"), message_schema).alias("data")
            ).select("kafka_topic", "partition", "offset", "kafka_timestamp", "data.*")
            
            # Traitement par batch
            def process_batch(batch_df, batch_id):
                try:
                    self.logger.info(f"📊 Traitement batch {batch_id} - {batch_df.count()} messages")
                    
                    # Convertir en format Python pour traitement
                    messages = []
                    for row in batch_df.collect():
                        message = {
                            'message_id': row['message_id'],
                            'timestamp': row['timestamp'],
                            'source': row['source'],
                            'source_type': row['source_type'],
                            'content': row['content'],
                            'sentiment_score': row['sentiment_score'],
                            'location': row['location'],
                            'metadata': row['metadata']
                        }
                        messages.append(message)
                    
                    # Traitement du batch
                    if messages:
                        results = self.process_stream_batch(messages)
                        self.logger.info(f"✅ Batch {batch_id} traité: {results['batch_size']} messages en {results['processing_time']:.2f}s")
                        
                        # Log des anomalies
                        if results['anomalies']:
                            self.logger.warning(f"🚨 {len(results['anomalies'])} anomalies détectées dans le batch {batch_id}")
                            for anomaly in results['anomalies']:
                                self.logger.warning(f"   - {anomaly['description']}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur traitement batch {batch_id}: {e}")
            
            # Démarrage du stream
            query = parsed_df.writeStream \
                .foreachBatch(process_batch) \
                .outputMode("append") \
                .option("checkpointLocation", "/tmp/spark_streaming_checkpoint") \
                .trigger(processingTime='10 seconds') \
                .start()
            
            self.logger.info("✅ Spark Streaming démarré")
            
            # Attendre l'arrêt
            query.awaitTermination()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur Spark Streaming: {e}")
            raise
    
    def get_real_time_analytics(self) -> Dict:
        """Retourne les analytics temps réel"""
        # Top trending keywords des dernières 5 minutes
        recent_keywords = [
            kw for kw in self.real_time_data['trending_keywords']
            if datetime.fromisoformat(kw['timestamp']) > datetime.now() - timedelta(minutes=5)
        ]
        
        # Grouper par keyword et calculer score moyen
        keyword_scores = defaultdict(list)
        for kw_data in recent_keywords:
            keyword_scores[kw_data['keyword']].append(kw_data['score'])
        
        top_keywords = [
            {
                'keyword': keyword,
                'average_score': np.mean(scores),
                'mentions': len(scores)
            }
            for keyword, scores in keyword_scores.items()
        ]
        top_keywords.sort(key=lambda x: x['average_score'], reverse=True)
        
        # Sentiment trends des dernières 10 minutes
        recent_messages = [
            msg for msg in self.real_time_data['recent_messages']
            if datetime.fromisoformat(msg['timestamp']) > datetime.now() - timedelta(minutes=10)
        ]
        
        sentiment_by_minute = defaultdict(list)
        for msg in recent_messages:
            minute = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            sentiment_by_minute[minute].append(msg['sentiment']['compound'])
        
        sentiment_trends = [
            {
                'time': minute,
                'average_sentiment': np.mean(sentiments),
                'message_count': len(sentiments)
            }
            for minute, sentiments in sorted(sentiment_by_minute.items())
        ]
        
        # Anomalies récentes
        recent_anomalies = [
            anomaly for anomaly in self.real_time_data['anomalies']
            if datetime.fromisoformat(anomaly['timestamp']) > datetime.now() - timedelta(minutes=30)
        ]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'trending_keywords': top_keywords[:20],
            'sentiment_trends': sentiment_trends,
            'recent_anomalies': recent_anomalies,
            'source_statistics': dict(self.real_time_data['source_stats']),
            'total_messages_processed': len(self.real_time_data['recent_messages']),
            'system_health': {
                'mongodb_connected': self.mongo_client is not None,
                'spark_active': True,
                'last_update': datetime.now().isoformat()
            }
        }
    
    def stop_streaming(self):
        """Arrête le streaming"""
        if self.streaming_context:
            self.streaming_context.stop(stopSparkContext=False, stopGraceFully=True)
        
        if self.spark:
            self.spark.stop()
        
        if self.mongo_client:
            self.mongo_client.close()
        
        self.logger.info("✅ Streaming arrêté")

def create_spark_session(app_name="SparkConnectionCheck", kafka_packages=None):
    builder = SparkSession.builder.appName(app_name)
    if kafka_packages:
        logger.info(f"Ajout du package Spark jars: {kafka_packages}")
        builder = builder.config("spark.jars.packages", kafka_packages)
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def is_kafka_datasource_available(spark):
    try:
        # Vérifie la présence de la classe KafkaSourceProvider
        spark._jvm.org.apache.spark.sql.kafka010.KafkaSourceProvider
        return True
    except Exception:
        return False


def check_jdbc_driver(spark, driver_class="org.postgresql.Driver"):
    try:
        spark._jvm.java.lang.Class.forName(driver_class)
        return True
    except Py4JJavaError:
        return False
    except Exception:
        return False


def test_port_tcp(host, port, timeout=5):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def parse_jdbc_url(jdbc_url):
    # Ex: jdbc:postgresql://host:5432/dbname
    try:
        m = re.match(r"jdbc:\w+://([^/]+)", jdbc_url)
        host_port = m.group(1)
        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host, port = host_port, 5432
        return host, int(port)
    except Exception:
        return None, None


def test_kafka_brokers(bootstrap_servers, timeout=5):
    # Try kafka-python if available, else TCP socket
    servers = [s.strip() for s in str(bootstrap_servers).split(",") if s.strip()]
    try:
        from kafka import KafkaProducer
        try:
            producer = KafkaProducer(bootstrap_servers=servers, request_timeout_ms=timeout*1000)
            producer.close()
            return True
        except Exception:
            pass
    except Exception:
        pass

    # Fallback socket check
    for s in servers:
        if ":" in s:
            host, port = s.split(":", 1)
            if test_port_tcp(host, port, timeout=timeout):
                return True
    return False


def run_checks(kafka_bootstrap="localhost:9092", jdbc_url="jdbc:postgresql://localhost:5432/postgres",
               jdbc_driver="org.postgresql.Driver", auto_fix=False):
    # 1) Spark sans packages (création initiale)
    spark = create_spark_session("ConnectivityCheck")
    kafka_available = is_kafka_datasource_available(spark)
    logger.info(f"Kafka data source available in Spark: {kafka_available}")

    # 2) Si manquant et auto_fix demandé, redémarrer Spark avec le package kafka
    if not kafka_available and auto_fix:
        spark_version = spark.sparkContext.version
        # Scala 2.12 is default for Spark 3.x; ajuster si besoin
        kafka_pkg = f"org.apache.spark:spark-sql-kafka-0-10_2.12:{spark_version}"
        logger.info("Redémarrage Spark avec le package Kafka...")
        try:
            spark.stop()
            spark = create_spark_session("ConnectivityCheck", kafka_packages=kafka_pkg)
            time.sleep(2)
            kafka_available = is_kafka_datasource_available(spark)
            logger.info(f"Après redémarrage, Kafka data source available: {kafka_available}")
        except Exception as e:
            logger.error(f"Échec redémarrage Spark avec package Kafka: {e}")

    # 3) Test brokers Kafka directement
    kafka_brokers_ok = test_kafka_brokers(kafka_bootstrap)
    if kafka_brokers_ok:
        logger.info(f"✅ Kafka brokers reachable: {kafka_bootstrap}")
    else:
        logger.warning(f"❌ Kafka brokers unreachable: {kafka_bootstrap}")

    # 4) Test JDBC driver availability
    jdbc_driver_ok = check_jdbc_driver(spark, jdbc_driver)
    if jdbc_driver_ok:
        logger.info(f"✅ JDBC driver présent: {jdbc_driver}")
    else:
        logger.warning(f"❌ JDBC driver absent: {jdbc_driver} (placer le driver jar dans spark classpath)")

    # 5) Test connexion réseau au port DB
    db_host, db_port = parse_jdbc_url(jdbc_url)
    db_port_ok = False
    if db_host and db_port:
        db_port_ok = test_port_tcp(db_host, db_port)
        if db_port_ok:
            logger.info(f"✅ Port DB accessible: {db_host}:{db_port}")
        else:
            logger.warning(f"❌ Port DB inaccessible: {db_host}:{db_port}")
    else:
        logger.warning("❌ Impossible de parser JDBC URL fournie pour tester le port")

    # Résumé
    summary = {
        "kafka_datasource": kafka_available,
        "kafka_brokers": kafka_brokers_ok,
        "jdbc_driver": jdbc_driver_ok,
        "db_port": db_port_ok
    }

    spark.stop()
    return summary


def main():
    """Fonction principale"""
    print("⚡ SPARK STREAMING CONSUMER - REAL-TIME ANALYTICS")
    print("=" * 60)
    print("Capacités:")
    print("• 📊 Traitement multi-sources Kafka en temps réel")
    print("• 🧠 Analyse de sentiment avancée (VADER + TextBlob + Lexicon)")
    print("• 📈 Détection de trending keywords avec fenêtres glissantes")
    print("• 🚨 Détection d'anomalies statistiques")
    print("• 💾 Stockage MongoDB avec partitioning")
    print("• ⚡ Analytics temps réel sans redémarrage")
    print()
    
    # Configuration
    config = {
        'kafka': {
            'bootstrap_servers': ['localhost:9092'],
            'topics': {
                'reddit_stream': 3,
                'twitter_stream': 3,
                'iot_sensors': 5,
                'news_feed': 2
            }
        },
        'mongodb': {
            'connection_string': 'mongodb://localhost:27017/',
            'database': 'multi_source_analytics'
        },
        'spark': {
            'app_name': 'MultiSourceAnalytics',
            'master': 'local[*]'
        }
    }
    
    # Créer et démarrer l'analyseur
    analytics = StreamingAnalytics(config)
    
    try:
        analytics.start_streaming()
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé...")
    finally:
        analytics.stop_streaming()
        print("✅ Spark Streaming arrêté proprement")

    parser = argparse.ArgumentParser(description="Check Spark connectivity to Kafka and JDBC.")
    parser.add_argument("--kafka-bootstrap", default="localhost:9092", help="Kafka bootstrap servers (comma separated)")
    parser.add_argument("--jdbc-url", default="jdbc:postgresql://localhost:5432/postgres", help="JDBC URL to test")
    parser.add_argument("--jdbc-driver", default="org.postgresql.Driver", help="JDBC driver class name")
    parser.add_argument("--auto-fix", action="store_true", help="Try to restart Spark with kafka package automatically")
    args = parser.parse_args()

    logger.info("🔎 Lancement des vérifications Spark <-> Kafka/JDBC")
    result = run_checks(
        kafka_bootstrap=args.kafka_bootstrap,
        jdbc_url=args.jdbc_url,
        jdbc_driver=args.jdbc_driver,
        auto_fix=args.auto_fix
    )

    logger.info("✅ Résumé des vérifications:")
    for k, v in result.items():
        logger.info(f" - {k}: {'OK' if v else 'KO'}")

    if not result["kafka_datasource"]:
        logger.error("Kafka DataSource manquant côté Spark. Pour corriger: lancer spark-submit avec --packages org.apache.spark:spark-sql-kafka-0-10_2.12:<spark_version>")
    if not result["jdbc_driver"]:
        logger.error("Driver JDBC manquant. Ajoutez le driver (ex. postgresql) à spark.jars ou au classpath.")

    # exit code utile pour automation
    exit(0 if all(result.values()) else 1)


if __name__ == "__main__":
    main()