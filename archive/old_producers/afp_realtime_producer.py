#!/usr/bin/env python3
"""
AFP Real-Time Producer - Fetches real AFP news via RSS/API
Compares with Reddit and GDELT for information propagation analysis
"""

import json
import time
import logging
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import feedparser
import requests
from typing import Dict, List, Optional
import hashlib
from textblob import TextBlob
import praw
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)

class AFPRealTimeProducer:
    """Producer for real AFP news articles"""
    
    def __init__(self, kafka_config: Dict):
        self.logger = logging.getLogger("AFP-Producer")
        self.kafka_config = kafka_config
        self.producer = None
        self.seen_articles = set()  # Prevent duplicates
        
        # AFP RSS feeds (public)
        self.afp_rss_feeds = [
            'https://www.afp.com/en/news/general',
            'https://www.afp.com/en/news/politics',
            'https://www.afp.com/en/news/economy',
            'https://www.afp.com/en/news/science',
            'https://www.afp.com/en/news/environment'
        ]
        
        self.connect_kafka()
    
    def connect_kafka(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            self.logger.info("✅ Connected to Kafka")
        except Exception as e:
            self.logger.error(f"❌ Kafka connection failed: {e}")
    
    def fetch_afp_articles(self) -> List[Dict]:
        """Fetch real AFP articles from RSS feeds"""
        articles = []
        
        for feed_url in self.afp_rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Get latest 5 per feed
                    article_id = hashlib.md5(entry.link.encode()).hexdigest()
                    
                    if article_id in self.seen_articles:
                        continue
                    
                    self.seen_articles.add(article_id)
                    
                    # Extract article data
                    article = {
                        'message_id': article_id,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'AFP',
                        'source_type': 'news_agency',
                        'title': entry.title,
                        'content': entry.get('summary', entry.title),
                        'url': entry.link,
                        'published': entry.get('published', datetime.now().isoformat()),
                        'category': self._extract_category(feed_url),
                        'metadata': {
                            'platform': 'AFP',
                            'reliability_score': 0.98,
                            'is_verified': True,
                            'language': 'en',
                            'word_count': len(entry.get('summary', '').split())
                        }
                    }
                    
                    # Sentiment analysis
                    sentiment = TextBlob(article['content']).sentiment
                    article['sentiment_score'] = sentiment.polarity
                    
                    articles.append(article)
                    
            except Exception as e:
                self.logger.error(f"❌ Error fetching RSS {feed_url}: {e}")
        
        return articles
    
    def _extract_category(self, feed_url: str) -> str:
        """Extract category from feed URL"""
        if 'politics' in feed_url:
            return 'politics'
        elif 'economy' in feed_url:
            return 'economy'
        elif 'science' in feed_url:
            return 'science'
        elif 'environment' in feed_url:
            return 'environment'
        return 'general'
    
    def send_article(self, article: Dict):
        """Send article to Kafka"""
        try:
            future = self.producer.send('afp_news_stream', value=article)
            future.get(timeout=10)
            self.logger.info(f"📰 AFP article sent: {article['title'][:50]}...")
        except Exception as e:
            self.logger.error(f"❌ Error sending article: {e}")
    
    def start_producing(self, interval_seconds: int = 60):
        """Start producing AFP articles"""
        self.logger.info("🚀 Starting AFP producer...")
        
        try:
            while True:
                articles = self.fetch_afp_articles()
                
                for article in articles:
                    self.send_article(article)
                    time.sleep(2)  # Avoid overwhelming
                
                self.logger.info(f"✅ Sent {len(articles)} AFP articles")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ Stopping AFP producer")
        finally:
            if self.producer:
                self.producer.close()


class RedditComparisonProducer:
    """Producer for Reddit discussions related to AFP articles"""
    
    def __init__(self, kafka_config: Dict, reddit_config: Dict):
        self.logger = logging.getLogger("Reddit-Producer")
        self.kafka_config = kafka_config
        self.producer = None
        
        # Initialize Reddit API
        try:
            self.reddit = praw.Reddit(
                client_id=reddit_config.get('client_id', 'your_client_id'),
                client_secret=reddit_config.get('client_secret', 'your_secret'),
                user_agent=reddit_config.get('user_agent', 'AFP-Comparator/1.0')
            )
            self.logger.info("✅ Reddit API connected")
        except Exception as e:
            self.logger.warning(f"⚠️ Reddit API failed, using simulation: {e}")
            self.reddit = None
        
        self.connect_kafka()
    
    def connect_kafka(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all'
            )
            self.logger.info("✅ Connected to Kafka")
        except Exception as e:
            self.logger.error(f"❌ Kafka connection failed: {e}")
    
    def search_related_discussions(self, keywords: List[str]) -> List[Dict]:
        """Search Reddit for discussions related to AFP keywords"""
        discussions = []
        
        if not self.reddit:
            return discussions
        
        subreddits = ['worldnews', 'news', 'politics', 'environment', 'technology']
        
        for keyword in keywords[:3]:  # Top 3 keywords
            try:
                for subreddit_name in subreddits:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    for submission in subreddit.search(keyword, limit=3, time_filter='day'):
                        discussion = {
                            'message_id': submission.id,
                            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'source': f'r/{subreddit_name}',
                            'source_type': 'social_media',
                            'title': submission.title,
                            'content': submission.selftext or submission.title,
                            'url': f'https://reddit.com{submission.permalink}',
                            'keyword_matched': keyword,
                            'metadata': {
                                'platform': 'reddit',
                                'upvotes': submission.score,
                                'comments': submission.num_comments,
                                'upvote_ratio': submission.upvote_ratio,
                                'author': str(submission.author),
                                'is_verified': False
                            }
                        }
                        
                        # Sentiment
                        sentiment = TextBlob(discussion['content']).sentiment
                        discussion['sentiment_score'] = sentiment.polarity
                        
                        discussions.append(discussion)
                        
            except Exception as e:
                self.logger.error(f"❌ Error searching Reddit for '{keyword}': {e}")
        
        return discussions
    
    def send_discussion(self, discussion: Dict):
        """Send discussion to Kafka"""
        try:
            future = self.producer.send('reddit_comparison_stream', value=discussion)
            future.get(timeout=10)
            self.logger.info(f"💬 Reddit discussion sent: {discussion['title'][:50]}...")
        except Exception as e:
            self.logger.error(f"❌ Error sending discussion: {e}")


class GDELTComparisonProducer:
    """Producer for GDELT events related to AFP articles"""
    
    def __init__(self, kafka_config: Dict):
        self.logger = logging.getLogger("GDELT-Producer")
        self.kafka_config = kafka_config
        self.producer = None
        self.gdelt_api_base = "https://api.gdeltproject.org/api/v2"
        
        self.connect_kafka()
    
    def connect_kafka(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all'
            )
            self.logger.info("✅ Connected to Kafka")
        except Exception as e:
            self.logger.error(f"❌ Kafka connection failed: {e}")
    
    def fetch_gdelt_events(self, keywords: List[str]) -> List[Dict]:
        """Fetch GDELT events related to keywords"""
        events = []
        
        for keyword in keywords[:3]:
            try:
                # GDELT DOC 2.0 API
                url = f"{self.gdelt_api_base}/doc/doc"
                params = {
                    'query': keyword,
                    'mode': 'ArtList',
                    'maxrecords': 10,
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', [])[:5]:
                        event = {
                            'message_id': str(uuid.uuid4()),
                            'timestamp': datetime.now().isoformat(),
                            'source': 'GDELT',
                            'source_type': 'news_aggregator',
                            'title': article.get('title', ''),
                            'content': article.get('seendate', ''),
                            'url': article.get('url', ''),
                            'keyword_matched': keyword,
                            'metadata': {
                                'platform': 'GDELT',
                                'domain': article.get('domain', ''),
                                'language': article.get('language', 'en'),
                                'tone': article.get('tone', 0),
                                'is_verified': True,
                                'source_count': 1
                            }
                        }
                        
                        events.append(event)
                        
            except Exception as e:
                self.logger.error(f"❌ Error fetching GDELT for '{keyword}': {e}")
        
        return events
    
    def send_event(self, event: Dict):
        """Send event to Kafka"""
        try:
            future = self.producer.send('gdelt_comparison_stream', value=event)
            future.get(timeout=10)
            self.logger.info(f"🌍 GDELT event sent: {event['title'][:50]}...")
        except Exception as e:
            self.logger.error(f"❌ Error sending event: {e}")


def main():
    """Main orchestrator for all producers"""
    print("🚀 AFP REAL-TIME COMPARISON SYSTEM")
    print("=" * 60)
    
    kafka_config = {
        'bootstrap_servers': ['localhost:9092']
    }
    
    reddit_config = {
        'client_id': 'your_reddit_client_id',
        'client_secret': 'your_reddit_secret',
        'user_agent': 'AFP-Comparator/1.0'
    }
    
    # Start producers
    afp_producer = AFPRealTimeProducer(kafka_config)
    reddit_producer = RedditComparisonProducer(kafka_config, reddit_config)
    gdelt_producer = GDELTComparisonProducer(kafka_config)
    
    try:
        # Main loop
        while True:
            # 1. Fetch AFP articles
            afp_articles = afp_producer.fetch_afp_articles()
            
            for article in afp_articles:
                afp_producer.send_article(article)
                
                # Extract keywords from AFP article
                keywords = article['title'].split()[:5]
                
                # 2. Search related Reddit discussions
                reddit_discussions = reddit_producer.search_related_discussions(keywords)
                for discussion in reddit_discussions:
                    reddit_producer.send_discussion(discussion)
                
                # 3. Fetch related GDELT events
                gdelt_events = gdelt_producer.fetch_gdelt_events(keywords)
                for event in gdelt_events:
                    gdelt_producer.send_event(event)
            
            time.sleep(300)  # Every 5 minutes
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping producers...")


if __name__ == "__main__":
    main()
