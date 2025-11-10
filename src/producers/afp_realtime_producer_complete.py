#!/usr/bin/env python3
"""
📡 AFP REAL-TIME PRODUCER - COMPLETE SYSTEM
Produces AFP articles, Reddit discussions, and GDELT events in real-time
Simulates information propagation across multiple sources
"""

import json
import time
import logging
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import random
import numpy as np
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('afp_realtime_producer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AFPProducer")

# AFP Article Templates (Realistic news)
AFP_ARTICLES = [
    {
        "category": "politique",
        "title": "UE adopte nouvelles sanctions contre Russie - Embargo pétrolier renforcé",
        "content": "BRUXELLES - Le Conseil européen a approuvé un 12e paquet de sanctions contre la Russie, incluant un embargo total sur le pétrole russe et de nouvelles restrictions bancaires.",
        "keywords": ["sanctions", "russie", "union européenne", "pétrole", "embargo"],
        "location": "Bruxelles, Belgique",
        "journalist": "Marie Dubois"
    },
    {
        "category": "environnement",
        "title": "COP29 Dubai - Accord historique 100 milliards pour le climat",
        "content": "DUBAI - Les 197 pays participants à la COP29 ont signé un accord historique prévoyant 100 milliards d'euros pour lutter contre le changement climatique.",
        "keywords": ["climat", "cop29", "emissions", "accord", "environnement"],
        "location": "Dubai, Émirats Arabes Unis",
        "journalist": "Pierre Martin"
    },
    {
        "category": "technologie",
        "title": "EUROPA-AI révolutionne l'IA - 150 langues maîtrisées à 96%",
        "content": "PARIS - Une équipe de chercheurs européens dévoile EUROPA-AI, un modèle d'intelligence artificielle capable de traiter 150 langues avec une précision de 96%.",
        "keywords": ["intelligence artificielle", "europa-ai", "multilingue", "recherche"],
        "location": "Paris, France",
        "journalist": "Dr. Sophie Chen"
    },
    {
        "category": "santé",
        "title": "OMS évite nouvelle pandémie grâce au système d'alerte précoce",
        "content": "GENÈVE - L'Organisation mondiale de la santé annonce avoir détecté et contenu un nouveau virus en Asie du Sud-Est avant sa propagation internationale.",
        "keywords": ["pandémie", "oms", "virus", "alerte précoce", "santé"],
        "location": "Genève, Suisse",
        "journalist": "Dr. Ahmed Hassan"
    },
    {
        "category": "économie",
        "title": "BCE réforme système bancaire européen - Nouvelles règles prudentielles",
        "content": "FRANCFORT - La Banque centrale européenne met en place de nouvelles règles prudentielles pour renforcer la stabilité financière.",
        "keywords": ["bce", "bancaire", "réforme", "prudentiel", "stabilité"],
        "location": "Francfort, Allemagne",
        "journalist": "François Leclerc"
    }
]

class AFPRealtimeProducer:
    """Producer for AFP, Reddit, and GDELT real-time data"""
    
    def __init__(self):
        self.producer = None
        self.afp_counter = 0
        self.reddit_counter = 0
        self.gdelt_counter = 0
        self.published_afp = {}  # Track published AFP articles
        
    def connect_kafka(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info("✅ Connected to Kafka successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            return False
    
    def generate_afp_article(self):
        """Generate AFP article"""
        template = random.choice(AFP_ARTICLES)
        self.afp_counter += 1
        
        article_id = f"AFP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.afp_counter}"
        timestamp = datetime.now()
        
        article = {
            "message_id": article_id,
            "timestamp": timestamp.isoformat(),
            "source": "AFP",
            "source_type": "official_news_agency",
            "title": template["title"],
            "content": template["content"] + f" L'AFP a vérifié ces informations auprès de sources officielles. Article #{self.afp_counter} publié le {timestamp.strftime('%d/%m/%Y à %H:%M')}.",
            "category": template["category"],
            "metadata": {
                "journalist": template["journalist"],
                "location": template["location"],
                "keywords": template["keywords"],
                "reliability_score": 0.98,
                "is_official": True,
                "word_count": len(template["content"].split()),
                "priority": random.choice(["URGENT", "FLASH", "NORMAL"])
            }
        }
        
        # Store for Reddit/GDELT comparison
        self.published_afp[article_id] = article
        
        return article, template
    
    def generate_reddit_discussion(self, afp_article, template):
        """Generate Reddit discussion based on AFP article"""
        self.reddit_counter += 1
        
        # Add delay (Reddit reacts after AFP)
        delay_hours = random.uniform(0.5, 6.0)
        timestamp = datetime.fromisoformat(afp_article['timestamp']) + timedelta(hours=delay_hours)
        
        # Modify content (simulate deformation)
        deformation_level = random.choice(['low', 'medium', 'high'])
        
        if deformation_level == 'low':
            content = afp_article['content'] + " Discussion on this topic."
            title_prefix = "Breaking: "
        elif deformation_level == 'medium':
            content = f"Just heard about {template['keywords'][0]}. {afp_article['content'][:100]}... What are your thoughts?"
            title_prefix = "Discussion: "
        else:  # high
            content = f"SHOCKING: {template['keywords'][0]}!!! This is HUGE!!! Source says {afp_article['content'][:80]}..."
            title_prefix = "🚨 ALERT: "
        
        subreddits = {
            'politique': ['r/europe', 'r/worldnews', 'r/politics'],
            'environnement': ['r/environment', 'r/climate', 'r/sustainability'],
            'technologie': ['r/technology', 'r/artificial', 'r/futurology'],
            'santé': ['r/health', 'r/medicine', 'r/science'],
            'économie': ['r/economics', 'r/investing', 'r/business']
        }
        
        subreddit = random.choice(subreddits.get(template['category'], ['r/news']))
        
        reddit_post = {
            "message_id": f"REDDIT_{timestamp.strftime('%Y%m%d%H%M%S')}_{self.reddit_counter}",
            "timestamp": timestamp.isoformat(),
            "source": "Reddit",
            "source_type": "social_media",
            "title": title_prefix + template['title'][:60] + "...",
            "content": content,
            "category": template['category'],
            "metadata": {
                "subreddit": subreddit,
                "upvotes": random.randint(500, 5000),
                "comments": random.randint(50, 1200),
                "deformation_level": deformation_level,
                "afp_reference": afp_article['message_id'],
                "delay_hours": delay_hours,
                "engagement_rate": round(random.uniform(0.15, 0.50), 3),
                "verification_status": random.choice(['verified', 'unverified', 'disputed'])
            }
        }
        
        return reddit_post
    
    def generate_gdelt_event(self, afp_article, template):
        """Generate GDELT event based on AFP article"""
        self.gdelt_counter += 1
        
        # Add delay (GDELT aggregates after publication)
        delay_hours = random.uniform(0.2, 4.0)
        timestamp = datetime.fromisoformat(afp_article['timestamp']) + timedelta(hours=delay_hours)
        
        event_types = {
            'politique': ['DIPLOMATIC_MEETING', 'POLICY_ANNOUNCEMENT', 'INTERNATIONAL_AGREEMENT'],
            'environnement': ['CLIMATE_AGREEMENT', 'ENVIRONMENTAL_POLICY', 'SUSTAINABILITY_SUMMIT'],
            'technologie': ['TECH_INNOVATION', 'DIGITAL_POLICY', 'AI_DEVELOPMENT'],
            'santé': ['HEALTH_POLICY', 'MEDICAL_BREAKTHROUGH', 'PUBLIC_HEALTH'],
            'économie': ['ECON_POLICY', 'TRADE_AGREEMENT', 'FINANCIAL_REFORM']
        }
        
        event_type = random.choice(event_types.get(template['category'], ['GENERAL_NEWS']))
        
        gdelt_event = {
            "message_id": f"GDELT_{timestamp.strftime('%Y%m%d%H%M%S')}_{self.gdelt_counter}",
            "timestamp": timestamp.isoformat(),
            "source": "GDELT",
            "source_type": "event_database",
            "title": f"GDELT: {event_type} - {template['location']}",
            "content": afp_article['content'] + f" Event documented by GDELT with {random.randint(8, 35)} global sources.",
            "category": template['category'],
            "metadata": {
                "event_type": event_type,
                "location": template['location'],
                "tone": round(random.uniform(-5, 5), 1),
                "coverage_score": round(random.uniform(0.7, 0.98), 2),
                "source_count": random.randint(8, 35),
                "impact_score": round(random.uniform(0.6, 0.95), 2),
                "afp_reference": afp_article['message_id'],
                "delay_hours": delay_hours
            }
        }
        
        return gdelt_event
    
    def send_message(self, topic, message):
        """Send message to Kafka topic"""
        try:
            future = self.producer.send(topic, value=message)
            future.get(timeout=10)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message to {topic}: {e}")
            return False
    
    def start_producing(self):
        """Start producing real-time data"""
        if not self.connect_kafka():
            logger.error("❌ Cannot start without Kafka connection")
            return
        
        logger.info("🚀 Starting AFP Real-Time Producer")
        logger.info("📡 Producing to topics: afp_news_stream, reddit_comparison_stream, gdelt_comparison_stream")
        
        try:
            cycle = 0
            while True:
                cycle += 1
                logger.info(f"\n{'='*70}")
                logger.info(f"🔄 Cycle #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'='*70}")
                
                # 1. Generate AFP article
                afp_article, template = self.generate_afp_article()
                
                if self.send_message('afp_news_stream', afp_article):
                    logger.info(f"📰 AFP Article sent: {afp_article['title'][:60]}...")
                
                # Wait a bit
                time.sleep(2)
                
                # 2. Generate Reddit discussions (2-3 per AFP article)
                num_reddit = random.randint(2, 3)
                for i in range(num_reddit):
                    reddit_post = self.generate_reddit_discussion(afp_article, template)
                    
                    if self.send_message('reddit_comparison_stream', reddit_post):
                        delay = reddit_post['metadata']['delay_hours']
                        logger.info(f"💬 Reddit post sent (delay: {delay:.1f}h, deformation: {reddit_post['metadata']['deformation_level']})")
                    
                    time.sleep(1)
                
                # 3. Generate GDELT events (1-2 per AFP article)
                num_gdelt = random.randint(1, 2)
                for i in range(num_gdelt):
                    gdelt_event = self.generate_gdelt_event(afp_article, template)
                    
                    if self.send_message('gdelt_comparison_stream', gdelt_event):
                        delay = gdelt_event['metadata']['delay_hours']
                        logger.info(f"🌍 GDELT event sent (delay: {delay:.1f}h, sources: {gdelt_event['metadata']['source_count']})")
                    
                    time.sleep(1)
                
                logger.info(f"✅ Cycle #{cycle} complete: 1 AFP + {num_reddit} Reddit + {num_gdelt} GDELT")
                logger.info(f"📊 Total: AFP={self.afp_counter}, Reddit={self.reddit_counter}, GDELT={self.gdelt_counter}")
                
                # Wait before next cycle
                wait_time = random.randint(10, 20)
                logger.info(f"⏳ Waiting {wait_time}s before next cycle...\n")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            logger.info("\n⏹️  Producer stopped by user")
        finally:
            if self.producer:
                self.producer.flush()
                self.producer.close()
                logger.info("✅ Producer closed cleanly")

def main():
    print("=" * 70)
    print("📡 AFP REAL-TIME DATA PRODUCER")
    print("=" * 70)
    print("This producer simulates:")
    print("  • AFP official news articles (trusted source)")
    print("  • Reddit discussions (with varying deformation levels)")
    print("  • GDELT global events (multi-source aggregation)")
    print()
    print("Information flow: AFP → Reddit → GDELT")
    print("=" * 70)
    print()
    
    producer = AFPRealtimeProducer()
    producer.start_producing()

if __name__ == "__main__":
    main()
