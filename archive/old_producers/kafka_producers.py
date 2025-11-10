# 🏗️ KAFKA PRODUCERS - MULTI-SOURCE DATA INGESTION
# Real-Time Data Collection from Multiple Sources
# Sources: Reddit API, Twitter/X API, IoT Sensors, News Feeds (GDELT)

import json
import time
import random
import threading
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import requests
import logging
from faker import Faker
import numpy as np
from textblob import TextBlob
import tweepy  # Twitter API v2
import praw   # Reddit API
from typing import Dict, List, Optional
import os
from dataclasses import dataclass, asdict
import uuid

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('kafka_producers.log'),
        logging.StreamHandler()
    ]
)

fake = Faker()

@dataclass
class StreamMessage:
    """Structure standard pour tous les messages de stream"""
    message_id: str
    timestamp: str
    source: str
    source_type: str  # 'social_media', 'iot_sensor', 'news_feed'
    content: str
    metadata: Dict
    sentiment_score: Optional[float] = None
    location: Optional[Dict] = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

class BaseProducer:
    """Classe de base pour tous les producers Kafka"""
    
    def __init__(self, kafka_config: Dict, topic: str, source_name: str):
        self.kafka_config = kafka_config
        self.topic = topic
        self.source_name = source_name
        self.producer = None
        self.running = False
        self.logger = logging.getLogger(f"Producer-{source_name}")
        
        # Statistiques
        self.messages_sent = 0
        self.errors_count = 0
        self.start_time = None
        
    def connect_kafka(self):
        """Connexion au cluster Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda v: v.encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Attendre confirmation de tous les replicas
                retries=3,
                retry_backoff_ms=1000,
                batch_size=16384,
                linger_ms=10,
                compression_type='gzip'
            )
            self.logger.info(f"✅ Connexion Kafka réussie pour {self.source_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur connexion Kafka: {e}")
            return False
    
    def send_message(self, message: StreamMessage, key: Optional[str] = None):
        """Envoi d'un message vers Kafka"""
        try:
            if not self.producer:
                if not self.connect_kafka():
                    return False
            
            # Callback pour confirmer l'envoi
            def delivery_callback(record_metadata):
                self.messages_sent += 1
                if self.messages_sent % 100 == 0:
                    self.logger.info(f"📊 {self.messages_sent} messages envoyés vers {self.topic}")
            
            def error_callback(exception):
                self.errors_count += 1
                self.logger.error(f"❌ Erreur envoi message: {exception}")
            
            # Envoi asynchrone
            future = self.producer.send(
                self.topic,
                key=key or str(uuid.uuid4()),
                value=message.to_json()
            )
            future.add_callback(delivery_callback)
            future.add_errback(error_callback)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi message: {e}")
            self.errors_count += 1
            return False
    
    def start_producing(self):
        """Démarre la production de messages"""
        self.running = True
        self.start_time = datetime.now()
        self.logger.info(f"🚀 Démarrage producer {self.source_name}")
        
        try:
            while self.running:
                self.produce_data()
                time.sleep(self.get_sleep_interval())
        except KeyboardInterrupt:
            self.logger.info(f"⏹️ Arrêt producer {self.source_name}")
        finally:
            self.stop_producing()
    
    def stop_producing(self):
        """Arrête la production et ferme les connexions"""
        self.running = False
        if self.producer:
            self.producer.flush()
            self.producer.close()
        
        # Statistiques finales
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        rate = self.messages_sent / duration if duration > 0 else 0
        
        self.logger.info(f"📊 Statistiques finales {self.source_name}:")
        self.logger.info(f"   Messages envoyés: {self.messages_sent}")
        self.logger.info(f"   Erreurs: {self.errors_count}")
        self.logger.info(f"   Durée: {duration:.1f}s")
        self.logger.info(f"   Débit: {rate:.2f} msg/s")
    
    def produce_data(self):
        """Méthode à implémenter par les sous-classes"""
        raise NotImplementedError
    
    def get_sleep_interval(self) -> float:
        """Intervalle entre les messages (à personnaliser par source)"""
        return 1.0

class RedditProducer(BaseProducer):
    """Producer pour les données Reddit"""
    
    def __init__(self, kafka_config: Dict, reddit_config: Dict):
        super().__init__(kafka_config, "reddit_stream", "Reddit")
        self.reddit_config = reddit_config
        self.reddit = None
        
        # Configuration simulée si pas d'API réelle
        self.simulation_mode = reddit_config.get('simulation', True)
        
        if not self.simulation_mode:
            try:
                self.reddit = praw.Reddit(
                    client_id=reddit_config['client_id'],
                    client_secret=reddit_config['client_secret'],
                    user_agent=reddit_config['user_agent']
                )
                self.logger.info("✅ Connexion Reddit API réussie")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur Reddit API, passage en mode simulation: {e}")
                self.simulation_mode = True
    
    def produce_data(self):
        """Génère des données Reddit"""
        if self.simulation_mode:
            self._simulate_reddit_data()
        else:
            self._fetch_real_reddit_data()
    
    def _simulate_reddit_data(self):
        """Simulation de données Reddit réalistes"""
        subreddits = [
            'worldnews', 'technology', 'science', 'politics', 
            'environment', 'business', 'health', 'space'
        ]
        
        # Sujets trending simulés
        trending_topics = [
            "climate change summit", "AI breakthrough", "space mission",
            "economic policy", "healthcare innovation", "renewable energy",
            "cybersecurity", "social media regulation"
        ]
        
        subreddit = random.choice(subreddits)
        topic = random.choice(trending_topics)
        
        # Génération de contenu réaliste
        post_types = ['news', 'discussion', 'question', 'opinion']
        post_type = random.choice(post_types)
        
        if post_type == 'news':
            content = f"Breaking: {topic} - {fake.sentence()}"
        elif post_type == 'discussion':
            content = f"Discussion: What do you think about {topic}? {fake.text()[:200]}"
        elif post_type == 'question':
            content = f"Question about {topic}: {fake.sentence()}?"
        else:
            content = f"Opinion: {topic} - {fake.text()[:150]}"
        
        # Score et métriques réalistes
        score = int(np.random.exponential(100)) + 1
        num_comments = int(np.random.exponential(20))
        upvote_ratio = round(np.random.beta(8, 2), 2)
        
        # Analyse de sentiment
        sentiment = TextBlob(content).sentiment.polarity
        
        message = StreamMessage(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source=f"r/{subreddit}",
            source_type="social_media",
            content=content,
            sentiment_score=sentiment,
            metadata={
                'platform': 'reddit',
                'subreddit': subreddit,
                'post_type': post_type,
                'score': score,
                'num_comments': num_comments,
                'upvote_ratio': upvote_ratio,
                'trending_topic': topic,
                'author': fake.user_name(),
                'created_utc': datetime.now().timestamp()
            }
        )
        
        self.send_message(message, key=f"reddit_{subreddit}")
    
    def _fetch_real_reddit_data(self):
        """Récupération de vraies données Reddit"""
        try:
            # Subreddits populaires pour actualités
            subreddit_names = ['worldnews', 'technology', 'science']
            
            for sub_name in subreddit_names:
                subreddit = self.reddit.subreddit(sub_name)
                
                # Récupérer les posts les plus récents
                for post in subreddit.new(limit=5):
                    sentiment = TextBlob(post.title + " " + (post.selftext or "")).sentiment.polarity
                    
                    message = StreamMessage(
                        message_id=post.id,
                        timestamp=datetime.fromtimestamp(post.created_utc).isoformat(),
                        source=f"r/{sub_name}",
                        source_type="social_media",
                        content=post.title + (" - " + post.selftext[:200] if post.selftext else ""),
                        sentiment_score=sentiment,
                        metadata={
                            'platform': 'reddit',
                            'subreddit': sub_name,
                            'score': post.score,
                            'num_comments': post.num_comments,
                            'upvote_ratio': post.upvote_ratio,
                            'author': str(post.author),
                            'url': post.url,
                            'created_utc': post.created_utc,
                            'is_original_content': post.is_original_content
                        }
                    )
                    
                    self.send_message(message, key=f"reddit_{post.id}")
                    
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération Reddit: {e}")
    
    def get_sleep_interval(self) -> float:
        return random.uniform(2, 5)  # 2-5 secondes entre posts

class TwitterProducer(BaseProducer):
    """Producer pour les données Twitter/X"""
    
    def __init__(self, kafka_config: Dict, twitter_config: Dict):
        super().__init__(kafka_config, "twitter_stream", "Twitter")
        self.twitter_config = twitter_config
        self.api = None
        
        # Configuration simulée si pas d'API réelle
        self.simulation_mode = twitter_config.get('simulation', True)
        
        if not self.simulation_mode:
            try:
                # Twitter API v2
                self.api = tweepy.Client(
                    bearer_token=twitter_config['bearer_token'],
                    consumer_key=twitter_config['consumer_key'],
                    consumer_secret=twitter_config['consumer_secret'],
                    access_token=twitter_config['access_token'],
                    access_token_secret=twitter_config['access_token_secret']
                )
                self.logger.info("✅ Connexion Twitter API réussie")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur Twitter API, passage en mode simulation: {e}")
                self.simulation_mode = True
    
    def produce_data(self):
        """Génère des données Twitter"""
        if self.simulation_mode:
            self._simulate_twitter_data()
        else:
            self._fetch_real_twitter_data()
    
    def _simulate_twitter_data(self):
        """Simulation de tweets réalistes"""
        # Hashtags populaires simulés
        hashtags = [
            '#BreakingNews', '#ClimateChange', '#TechNews', '#AI', '#Innovation',
            '#Politics', '#Health', '#Science', '#Economy', '#SocialMedia'
        ]
        
        # Types de tweets
        tweet_types = ['news', 'opinion', 'retweet', 'reply']
        tweet_type = random.choice(tweet_types)
        
        # Génération de contenu
        hashtag = random.choice(hashtags)
        
        if tweet_type == 'news':
            content = f"{hashtag} {fake.sentence()[:120]}"
        elif tweet_type == 'opinion':
            content = f"I think {hashtag.lower()[1:]} is {fake.sentence()[:100]}"
        elif tweet_type == 'retweet':
            content = f"RT @{fake.user_name()}: {hashtag} {fake.sentence()[:100]}"
        else:
            content = f"@{fake.user_name()} {hashtag} {fake.sentence()[:110]}"
        
        # Métriques réalistes
        retweets = int(np.random.exponential(50))
        likes = int(np.random.exponential(100))
        replies = int(np.random.exponential(20))
        
        # Géolocalisation simulée
        locations = [
            {'country': 'US', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
            {'country': 'UK', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
            {'country': 'FR', 'city': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
            {'country': 'JP', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
        ]
        location = random.choice(locations)
        
        # Analyse de sentiment
        sentiment = TextBlob(content).sentiment.polarity
        
        message = StreamMessage(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source="Twitter",
            source_type="social_media",
            content=content,
            sentiment_score=sentiment,
            location=location,
            metadata={
                'platform': 'twitter',
                'tweet_type': tweet_type,
                'hashtags': [hashtag],
                'retweet_count': retweets,
                'like_count': likes,
                'reply_count': replies,
                'author': fake.user_name(),
                'author_followers': int(np.random.exponential(1000)),
                'language': 'en',
                'verified_user': random.choice([True, False]),
                'created_at': datetime.now().timestamp()
            }
        )
        
        self.send_message(message, key="twitter_general")
    
    def _fetch_real_twitter_data(self):
        """Récupération de vrais tweets"""
        try:
            # Recherche de tweets récents sur des sujets d'actualité
            queries = [
                "breaking news -is:retweet",
                "climate change -is:retweet",
                "technology innovation -is:retweet"
            ]
            
            for query in queries:
                tweets = self.api.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=['created_at', 'public_metrics', 'author_id', 'geo', 'lang']
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        sentiment = TextBlob(tweet.text).sentiment.polarity
                        
                        message = StreamMessage(
                            message_id=tweet.id,
                            timestamp=tweet.created_at.isoformat(),
                            source="Twitter",
                            source_type="social_media",
                            content=tweet.text,
                            sentiment_score=sentiment,
                            metadata={
                                'platform': 'twitter',
                                'author_id': tweet.author_id,
                                'language': tweet.lang,
                                'retweet_count': tweet.public_metrics['retweet_count'],
                                'like_count': tweet.public_metrics['like_count'],
                                'reply_count': tweet.public_metrics['reply_count'],
                                'quote_count': tweet.public_metrics['quote_count'],
                                'query_used': query
                            }
                        )
                        
                        self.send_message(message, key=f"twitter_{tweet.id}")
                        
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération Twitter: {e}")
    
    def get_sleep_interval(self) -> float:
        return random.uniform(1, 3)  # 1-3 secondes entre tweets

class IoTSensorProducer(BaseProducer):
    """Producer pour les données IoT (simulation)"""
    
    def __init__(self, kafka_config: Dict, sensor_config: Dict):
        super().__init__(kafka_config, "iot_sensors", "IoT-Sensors")
        self.sensor_config = sensor_config
        self.sensor_locations = self._generate_sensor_locations()
        
    def _generate_sensor_locations(self) -> List[Dict]:
        """Génère des emplacements de capteurs réalistes"""
        locations = [
            {'id': 'ENV_001', 'type': 'environmental', 'city': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
            {'id': 'ENV_002', 'type': 'environmental', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
            {'id': 'ENV_003', 'type': 'environmental', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
            {'id': 'TRAFFIC_001', 'type': 'traffic', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
            {'id': 'TRAFFIC_002', 'type': 'traffic', 'city': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437},
            {'id': 'ENERGY_001', 'type': 'energy', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
            {'id': 'ENERGY_002', 'type': 'energy', 'city': 'Madrid', 'lat': 40.4168, 'lon': -3.7038},
        ]
        return locations
    
    def produce_data(self):
        """Génère des données IoT réalistes"""
        sensor = random.choice(self.sensor_locations)
        
        # Génération de données selon le type de capteur
        if sensor['type'] == 'environmental':
            reading = self._generate_environmental_data(sensor)
        elif sensor['type'] == 'traffic':
            reading = self._generate_traffic_data(sensor)
        elif sensor['type'] == 'energy':
            reading = self._generate_energy_data(sensor)
        else:
            reading = self._generate_generic_data(sensor)
        
        # Détection d'anomalies simulées
        anomaly_prob = 0.05  # 5% de chance d'anomalie
        is_anomaly = random.random() < anomaly_prob
        
        if is_anomaly:
            reading['value'] *= random.uniform(1.5, 3.0)  # Multiplier par 1.5-3x
            reading['anomaly'] = True
            reading['anomaly_score'] = random.uniform(0.7, 1.0)
        else:
            reading['anomaly'] = False
            reading['anomaly_score'] = random.uniform(0.0, 0.3)
        
        message = StreamMessage(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source=sensor['id'],
            source_type="iot_sensor",
            content=f"Sensor reading: {reading['value']:.2f} {reading['unit']}",
            location={
                'city': sensor['city'],
                'lat': sensor['lat'],
                'lon': sensor['lon']
            },
            metadata={
                'sensor_id': sensor['id'],
                'sensor_type': sensor['type'],
                'measurement_type': reading['measurement_type'],
                'value': reading['value'],
                'unit': reading['unit'],
                'quality': reading['quality'],
                'anomaly': reading['anomaly'],
                'anomaly_score': reading['anomaly_score'],
                'calibration_date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                'battery_level': random.uniform(0.2, 1.0),
                'signal_strength': random.uniform(0.5, 1.0)
            }
        )
        
        self.send_message(message, key=sensor['id'])
    
    def _generate_environmental_data(self, sensor: Dict) -> Dict:
        """Données environnementales réalistes"""
        measurement_types = ['temperature', 'humidity', 'air_quality', 'noise_level']
        measurement = random.choice(measurement_types)
        
        if measurement == 'temperature':
            # Température avec variation saisonnière
            base_temp = 15 + 10 * np.sin(2 * np.pi * datetime.now().timetuple().tm_yday / 365)
            value = base_temp + random.uniform(-5, 5)
            unit = '°C'
        elif measurement == 'humidity':
            value = random.uniform(30, 80)
            unit = '%'
        elif measurement == 'air_quality':
            value = random.uniform(20, 150)  # AQI
            unit = 'AQI'
        else:  # noise_level
            value = random.uniform(30, 80)
            unit = 'dB'
        
        return {
            'measurement_type': measurement,
            'value': value,
            'unit': unit,
            'quality': random.choice(['excellent', 'good', 'fair', 'poor'])
        }
    
    def _generate_traffic_data(self, sensor: Dict) -> Dict:
        """Données de trafic avec patterns horaires"""
        hour = datetime.now().hour
        
        # Simulation de rush hours
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_traffic = 0.8
        elif 10 <= hour <= 16:
            base_traffic = 0.6
        elif 20 <= hour <= 23:
            base_traffic = 0.4
        else:
            base_traffic = 0.2
        
        traffic_density = base_traffic + random.uniform(-0.2, 0.2)
        traffic_density = max(0, min(1, traffic_density))  # Clamp entre 0 et 1
        
        vehicles_count = int(traffic_density * 100 + random.uniform(-10, 10))
        avg_speed = 50 * (1 - traffic_density) + random.uniform(-5, 5)
        
        measurement = random.choice(['vehicle_count', 'average_speed', 'traffic_density'])
        
        if measurement == 'vehicle_count':
            return {'measurement_type': measurement, 'value': vehicles_count, 'unit': 'vehicles/hour', 'quality': 'good'}
        elif measurement == 'average_speed':
            return {'measurement_type': measurement, 'value': avg_speed, 'unit': 'km/h', 'quality': 'good'}
        else:
            return {'measurement_type': measurement, 'value': traffic_density * 100, 'unit': '%', 'quality': 'good'}
    
    def _generate_energy_data(self, sensor: Dict) -> Dict:
        """Données énergétiques"""
        measurement_types = ['power_consumption', 'solar_generation', 'grid_frequency']
        measurement = random.choice(measurement_types)
        
        if measurement == 'power_consumption':
            # Consommation avec patterns journaliers
            hour = datetime.now().hour
            base_consumption = 50 + 30 * np.sin(2 * np.pi * (hour - 6) / 24)
            value = max(10, base_consumption + random.uniform(-10, 10))
            unit = 'kW'
        elif measurement == 'solar_generation':
            # Génération solaire selon l'heure
            hour = datetime.now().hour
            if 6 <= hour <= 18:
                solar_factor = np.sin(np.pi * (hour - 6) / 12)
                value = 20 * solar_factor + random.uniform(-2, 2)
            else:
                value = 0
            unit = 'kW'
        else:  # grid_frequency
            value = 50 + random.uniform(-0.5, 0.5)  # 50Hz ± 0.5Hz
            unit = 'Hz'
        
        return {
            'measurement_type': measurement,
            'value': max(0, value),
            'unit': unit,
            'quality': random.choice(['excellent', 'good', 'fair'])
        }
    
    def _generate_generic_data(self, sensor: Dict) -> Dict:
        """Données génériques pour autres types de capteurs"""
        return {
            'measurement_type': 'generic_reading',
            'value': random.uniform(0, 100),
            'unit': 'units',
            'quality': 'good'
        }
    
    def get_sleep_interval(self) -> float:
        return random.uniform(0.5, 2.0)  # 0.5-2 secondes entre lectures

class NewsProducer(BaseProducer):
    """Producer pour les flux d'actualités (GDELT, Reuters, etc.)"""
    
    def __init__(self, kafka_config: Dict, news_config: Dict):
        super().__init__(kafka_config, "news_feed", "News")
        self.news_config = news_config
        self.simulation_mode = news_config.get('simulation', True)
        
    def produce_data(self):
        """Génère des actualités"""
        if self.simulation_mode:
            self._simulate_news_data()
        else:
            self._fetch_real_news_data()
    
    def _simulate_news_data(self):
        """Simulation d'actualités réalistes"""
        categories = [
            'politics', 'technology', 'science', 'health', 'environment',
            'business', 'sports', 'entertainment', 'world', 'economy'
        ]
        
        sources = [
            {'name': 'Reuters', 'country': 'UK', 'credibility': 0.9},
            {'name': 'AP News', 'country': 'US', 'credibility': 0.95},
            {'name': 'BBC', 'country': 'UK', 'credibility': 0.9},
            {'name': 'France24', 'country': 'FR', 'credibility': 0.85},
            {'name': 'CNN', 'country': 'US', 'credibility': 0.8},
            {'name': 'Bloomberg', 'country': 'US', 'credibility': 0.85}
        ]
        
        category = random.choice(categories)
        source = random.choice(sources)
        
        # Génération de titre et contenu
        if category == 'technology':
            headlines = [
                "Major tech company announces breakthrough in AI",
                "New smartphone technology revolutionizes industry",
                "Cybersecurity threat affects millions of users",
                "Tech startup raises record funding round"
            ]
        elif category == 'environment':
            headlines = [
                "Climate summit reaches historic agreement",
                "Renewable energy adoption hits new milestone",
                "Environmental scientists warn of ecosystem threat",
                "Green technology innovation shows promise"
            ]
        elif category == 'politics':
            headlines = [
                "International leaders meet for diplomatic talks",
                "New policy announcement sparks debate",
                "Election results shift political landscape",
                "Trade agreement negotiations continue"
            ]
        else:
            headlines = [
                f"{category.title()} sector sees significant development",
                f"Breaking: Important {category} announcement",
                f"Analysis: {category.title()} trends and implications",
                f"Update: {category.title()} situation evolves"
            ]
        
        headline = random.choice(headlines)
        content = f"{headline}. {fake.paragraph()[:300]}"
        
        # Analyse de sentiment
        sentiment = TextBlob(content).sentiment.polarity
        
        # Métadonnées journalistiques
        urgency = random.choice(['low', 'medium', 'high', 'breaking'])
        
        message = StreamMessage(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            source=source['name'],
            source_type="news_feed",
            content=content,
            sentiment_score=sentiment,
            metadata={
                'headline': headline,
                'category': category,
                'source_country': source['country'],
                'credibility_score': source['credibility'],
                'urgency': urgency,
                'word_count': len(content.split()),
                'language': 'en',
                'author': fake.name(),
                'publication_time': datetime.now().isoformat(),
                'tags': [category, urgency],
                'estimated_reach': int(np.random.exponential(10000))
            }
        )
        
        self.send_message(message, key=f"news_{category}")
    
    def _fetch_real_news_data(self):
        """Récupération de vraies actualités via APIs"""
        # Implementation pour vraies APIs (NewsAPI, GDELT, etc.)
        pass
    
    def get_sleep_interval(self) -> float:
        return random.uniform(5, 15)  # 5-15 secondes entre actualités

class MultiSourceProducerManager:
    """Gestionnaire pour tous les producers"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.producers = []
        self.threads = []
        self.running = False
        self.logger = logging.getLogger("ProducerManager")
        
    def _load_config(self, config_file: str) -> Dict:
        """Charge la configuration depuis un fichier ou utilise les valeurs par défaut"""
        default_config = {
            'kafka': {
                'bootstrap_servers': ['localhost:9092'],
                'topics': {
                    'reddit_stream': 3,  # 3 partitions
                    'twitter_stream': 3,
                    'iot_sensors': 5,
                    'news_feed': 2
                }
            },
            'reddit': {
                'simulation': True,
                'client_id': os.getenv('REDDIT_CLIENT_ID'),
                'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                'user_agent': 'MultiSourceAnalytics/1.0'
            },
            'twitter': {
                'simulation': True,
                'bearer_token': os.getenv('TWITTER_BEARER_TOKEN'),
                'consumer_key': os.getenv('TWITTER_CONSUMER_KEY'),
                'consumer_secret': os.getenv('TWITTER_CONSUMER_SECRET'),
                'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
                'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            },
            'iot': {
                'simulation': True,
                'sensor_count': 10,
                'update_frequency': 2.0
            },
            'news': {
                'simulation': True,
                'api_key': os.getenv('NEWS_API_KEY')
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge configurations
                    for key, value in user_config.items():
                        if key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur lecture config: {e}, utilisation config par défaut")
        
        return default_config
    
    def setup_producers(self):
        """Configure tous les producers"""
        kafka_config = self.config['kafka']
        
        # Reddit Producer
        reddit_producer = RedditProducer(kafka_config, self.config['reddit'])
        self.producers.append(('Reddit', reddit_producer))
        
        # Twitter Producer
        twitter_producer = TwitterProducer(kafka_config, self.config['twitter'])
        self.producers.append(('Twitter', twitter_producer))
        
        # IoT Sensors Producer
        iot_producer = IoTSensorProducer(kafka_config, self.config['iot'])
        self.producers.append(('IoT', iot_producer))
        
        # News Producer
        news_producer = NewsProducer(kafka_config, self.config['news'])
        self.producers.append(('News', news_producer))
        
        self.logger.info(f"✅ {len(self.producers)} producers configurés")
    
    def start_all_producers(self):
        """Démarre tous les producers en parallèle"""
        if self.running:
            self.logger.warning("⚠️ Producers déjà en cours d'exécution")
            return
        
        self.running = True
        self.logger.info("🚀 Démarrage de tous les producers...")
        
        for name, producer in self.producers:
            thread = threading.Thread(
                target=producer.start_producing,
                name=f"Producer-{name}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            self.logger.info(f"▶️ Producer {name} démarré")
        
        self.logger.info("✅ Tous les producers sont actifs")
    
    def stop_all_producers(self):
        """Arrête tous les producers"""
        if not self.running:
            return
        
        self.logger.info("🛑 Arrêt de tous les producers...")
        
        # Arrêter les producers
        for _, producer in self.producers:
            producer.stop_producing()
        
        # Attendre la fin des threads
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.running = False
        self.logger.info("✅ Tous les producers arrêtés")
    
    def get_status(self) -> Dict:
        """Retourne le status de tous les producers"""
        status = {
            'running': self.running,
            'producers': {}
        }
        
        for name, producer in self.producers:
            status['producers'][name] = {
                'messages_sent': producer.messages_sent,
                'errors_count': producer.errors_count,
                'running': producer.running
            }
        
        return status

def main():
    """Fonction principale pour lancer les producers"""
    print("🚀 KAFKA MULTI-SOURCE PRODUCERS")
    print("=" * 50)
    print("Sources configurées:")
    print("• 📱 Reddit - Posts et discussions")
    print("• 🐦 Twitter/X - Tweets en temps réel")
    print("• 🌡️ IoT Sensors - Capteurs environnementaux")
    print("• 📰 News Feeds - Actualités GDELT/Reuters")
    print()
    
    # Créer et configurer le gestionnaire
    manager = MultiSourceProducerManager()
    manager.setup_producers()
    
    try:
        # Démarrer tous les producers
        manager.start_all_producers()
        
        # Maintenir le programme en vie et afficher le status
        while True:
            time.sleep(30)  # Attendre 30 secondes
            status = manager.get_status()
            
            print(f"\n📊 STATUS - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            for name, stats in status['producers'].items():
                print(f"{name:12}: {stats['messages_sent']:>6} msgs, {stats['errors_count']:>3} errors")
            
    except KeyboardInterrupt:
        print("\n⏹️ Interruption détectée...")
    finally:
        manager.stop_all_producers()
        print("✅ Arrêt complet des producers")

if __name__ == "__main__":
    main()