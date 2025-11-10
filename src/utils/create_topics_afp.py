#!/usr/bin/env python3
"""
Script to create AFP-specific Kafka topics
Creates: afp_news_stream, reddit_comparison_stream, gdelt_comparison_stream
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TopicCreator")

def create_afp_topics():
    """Create all AFP-related Kafka topics"""
    
    print("=" * 70)
    print("📋 CREATING AFP KAFKA TOPICS")
    print("=" * 70)
    
    # Topic configurations
    topics_config = [
        {'name': 'afp_news_stream', 'partitions': 3, 'replication': 1},
        {'name': 'reddit_comparison_stream', 'partitions': 3, 'replication': 1},
        {'name': 'gdelt_comparison_stream', 'partitions': 3, 'replication': 1}
    ]
    
    # Try to connect to Kafka
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Connection attempt {attempt + 1}/{max_retries}...")
            
            admin_client = KafkaAdminClient(
                bootstrap_servers=['localhost:9092'],
                client_id='afp-topic-creator',
                request_timeout_ms=30000
            )
            
            logger.info("✅ Connected to Kafka successfully")
            break
            
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️  Kafka not available, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Failed to connect to Kafka after all retries")
                logger.error("Make sure Kafka is running on localhost:9092")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    # Create topics
    print("\n📝 Creating topics...")
    print("-" * 70)
    
    topics_to_create = []
    for topic_config in topics_config:
        topic = NewTopic(
            name=topic_config['name'],
            num_partitions=topic_config['partitions'],
            replication_factor=topic_config['replication']
        )
        topics_to_create.append(topic)
    
    try:
        # Create all topics
        admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
        
        # Wait for creation
        time.sleep(2)
        
        # Verify
        existing_topics = admin_client.list_topics()
        
        print("\n✅ RESULTS:")
        print("-" * 70)
        
        success_count = 0
        for topic_config in topics_config:
            topic_name = topic_config['name']
            if topic_name in existing_topics:
                logger.info(f"✅ {topic_name:30s} - Created ({topic_config['partitions']} partitions)")
                success_count += 1
            else:
                logger.error(f"❌ {topic_name:30s} - FAILED")
        
        print("-" * 70)
        print(f"📊 {success_count}/{len(topics_config)} topics created successfully")
        
        admin_client.close()
        return success_count == len(topics_config)
        
    except TopicAlreadyExistsError:
        logger.info("\nℹ️  Some topics already exist:")
        
        existing_topics = admin_client.list_topics()
        
        for topic_config in topics_config:
            topic_name = topic_config['name']
            if topic_name in existing_topics:
                logger.info(f"✅ {topic_name:30s} - Already exists")
        
        logger.info("\n✅ All topics are available!")
        admin_client.close()
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Error creating topics: {e}")
        return False

def verify_topics():
    """Verify that all topics exist"""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=['localhost:9092'],
            client_id='afp-topic-verifier'
        )
        
        existing_topics = admin_client.list_topics()
        required_topics = ['afp_news_stream', 'reddit_comparison_stream', 'gdelt_comparison_stream']
        
        print("\n🔍 VERIFICATION:")
        print("-" * 70)
        
        all_exist = True
        for topic in required_topics:
            if topic in existing_topics:
                logger.info(f"✅ {topic:30s} - Available")
            else:
                logger.error(f"❌ {topic:30s} - Missing")
                all_exist = False
        
        admin_client.close()
        return all_exist
        
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 AFP KAFKA TOPIC SETUP")
    print("=" * 70)
    print("This script creates the following topics:")
    print("  • afp_news_stream (3 partitions) - AFP official articles")
    print("  • reddit_comparison_stream (3 partitions) - Reddit discussions")
    print("  • gdelt_comparison_stream (3 partitions) - GDELT events")
    print()
    
    # Create topics
    success = create_afp_topics()
    
    if success:
        # Verify
        verify_topics()
        
        print("\n" + "=" * 70)
        print("✅ Configuration completed successfully!")
        print("=" * 70)
        print("\n📋 NEXT STEPS:")
        print("  1. Start producer: python afp_realtime_producer_complete.py")
        print("  2. Start consumer: python spark_afp_realtime_consumer.py")
        print("  3. Open dashboard: streamlit run dashboard_afp_realtime_complete.py")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Configuration incomplete")
        print("=" * 70)
        print("\nMake sure:")
        print("  • Zookeeper is running")
        print("  • Kafka is running on localhost:9092")
        print("=" * 70)
