"""
AFP API Producer - Real AFP News Ingestion
Récupère les vraies actualités AFP via API et les envoie vers Kafka
"""

import json
import time
import logging
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import requests
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('afp_producer.log'),
        logging.StreamHandler()
    ]
)

class AFPNewsProducer:
    """Producer pour récupérer et diffuser les actualités AFP"""
    
    def __init__(self, kafka_config: Dict, afp_config: Dict):
        self.kafka_config = kafka_config
        self.afp_config = afp_config
        self.producer = None
        self.logger = logging.getLogger("AFPProducer")
        
        # API AFP ou alternative (NewsAPI avec filtre AFP)
        self.api_key = afp_config.get('api_key', os.getenv('NEWS_API_KEY'))
        self.base_url = afp_config.get('base_url', 'https://newsapi.org/v2/everything')
        
        # Catégories AFP à suivre
        self.categories = [
            'politics', 'economy', 'technology', 'health', 
            'environment', 'international', 'science'
        ]
        
        # Tracking des articles déjà publiés
        self.published_articles = set()
        
    def connect_kafka(self):
        """Connexion au broker Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            self.logger.info("✅ Connexion Kafka réussie")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur connexion Kafka: {e}")
            return False
    
    def fetch_afp_news(self, category: str = None) -> List[Dict]:
        """Récupère les actualités AFP via API"""
        try:
            # NewsAPI avec filtre AFP
            params = {
                'apiKey': self.api_key,
                'sources': 'afp',  # Source AFP
                'language': 'fr',
                'sortBy': 'publishedAt',
                'pageSize': 100
            }
            
            if category:
                params['q'] = category
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            self.logger.info(f"📰 {len(articles)} articles AFP récupérés")
            return articles
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération AFP: {e}")
            return []
    
    def normalize_afp_article(self, article: Dict) -> Dict:
        """Normalise un article AFP au format standard"""
        return {
            'message_id': f"AFP_{article['publishedAt']}_{hash(article['title'])}",
            'timestamp': article['publishedAt'],
            'source': 'AFP',
            'source_type': 'official_news_agency',
            'title': article['title'],
            'content': article.get('description', '') + ' ' + article.get('content', ''),
            'url': article.get('url', ''),
            'category': self._detect_category(article),
            'author': article.get('author', 'AFP'),
            'metadata': {
                'published_at': article['publishedAt'],
                'url_to_image': article.get('urlToImage', ''),
                'source_name': article.get('source', {}).get('name', 'AFP'),
                'reliability_score': 0.98,  # AFP = haute fiabilité
                'is_official': True
            }
        }
    
    def _detect_category(self, article: Dict) -> str:
        """Détecte la catégorie d'un article"""
        content = (article.get('title', '') + ' ' + article.get('description', '')).lower()
        
        # Mots-clés par catégorie
        category_keywords = {
            'politics': ['politique', 'gouvernement', 'président', 'ministre', 'élection'],
            'economy': ['économie', 'marché', 'bourse', 'commerce', 'finance'],
            'technology': ['technologie', 'innovation', 'ia', 'numérique', 'tech'],
            'health': ['santé', 'médical', 'hôpital', 'maladie', 'traitement'],
            'environment': ['climat', 'environnement', 'écologie', 'co2', 'pollution'],
            'international': ['international', 'monde', 'pays', 'diplomatique'],
            'science': ['science', 'recherche', 'étude', 'découverte', 'scientifique']
        }
        
        # Scoring
        scores = {}
        for category, keywords in category_keywords.items():
            scores[category] = sum(1 for kw in keywords if kw in content)
        
        # Retourner la catégorie avec le score le plus élevé
        best_category = max(scores, key=scores.get)
        return best_category if scores[best_category] > 0 else 'general'
    
    def send_to_kafka(self, article: Dict):
        """Envoie un article vers Kafka"""
        try:
            normalized = self.normalize_afp_article(article)
            
            # Éviter les doublons
            if normalized['message_id'] in self.published_articles:
                return False
            
            # Envoi vers le topic afp_stream
            self.producer.send(
                'afp_stream',
                key=normalized['message_id'].encode('utf-8'),
                value=normalized
            )
            
            self.published_articles.add(normalized['message_id'])
            self.logger.info(f"📤 Article AFP envoyé: {normalized['title'][:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi Kafka: {e}")
            return False
    
    def start_streaming(self, interval: int = 300):
        """Démarre le streaming AFP (toutes les 5 minutes par défaut)"""
        if not self.connect_kafka():
            return
        
        self.logger.info(f"🚀 Démarrage streaming AFP (intervalle: {interval}s)")
        
        try:
            while True:
                # Récupérer les actualités pour chaque catégorie
                for category in self.categories:
                    articles = self.fetch_afp_news(category)
                    
                    for article in articles:
                        self.send_to_kafka(article)
                        time.sleep(0.1)  # Rate limiting
                
                # Attendre l'intervalle
                self.logger.info(f"⏳ Prochaine récupération dans {interval}s")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Arrêt streaming AFP")
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()

def main():
    config = {
        'kafka': {
            'bootstrap_servers': ['localhost:9092']
        },
        'afp': {
            'api_key': os.getenv('NEWS_API_KEY'),
            'base_url': 'https://newsapi.org/v2/everything'
        }
    }
    
    producer = AFPNewsProducer(config['kafka'], config['afp'])
    producer.start_streaming(interval=300)  # 5 minutes

if __name__ == "__main__":
    main()
