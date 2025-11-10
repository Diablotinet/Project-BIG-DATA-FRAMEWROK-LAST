#!/usr/bin/env python3
"""
Script pour créer les topics Kafka nécessaires
Contourne le problème "La ligne entrée est trop longue" de Windows
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import time

def create_topics():
    """Crée tous les topics Kafka nécessaires"""
    
    print("📋 CRÉATION DES TOPICS KAFKA")
    print("=" * 50)
    
    # Configuration Kafka
    kafka_config = {
        'bootstrap_servers': ['localhost:9092'],
        'client_id': 'topic-creator',
        'request_timeout_ms': 30000,
        'api_version': (3, 6, 0)
    }
    
    # Définition des topics
    topics_config = [
        {'name': 'reddit_stream', 'partitions': 3, 'replication': 1},
        {'name': 'twitter_stream', 'partitions': 3, 'replication': 1},
        {'name': 'iot_sensors', 'partitions': 5, 'replication': 1},
        {'name': 'news_feed', 'partitions': 2, 'replication': 1}
    ]
    
    # Tentative de connexion avec retry
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            print(f"\n🔌 Tentative de connexion à Kafka ({attempt + 1}/{max_retries})...")
            admin_client = KafkaAdminClient(**kafka_config)
            print(" Connexion réussie à Kafka!")
            break
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                print(f"  Kafka non disponible, nouvelle tentative dans {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("\n ERREUR: Impossible de se connecter à Kafka")
                print("Vérifiez que Kafka est démarré sur localhost:9092")
                return False
        except Exception as e:
            print(f" Erreur de connexion: {e}")
            return False
    
    # Création des topics
    print("\n📝 Création des topics...")
    print("-" * 50)
    
    topics_to_create = []
    for topic_config in topics_config:
        topic = NewTopic(
            name=topic_config['name'],
            num_partitions=topic_config['partitions'],
            replication_factor=topic_config['replication']
        )
        topics_to_create.append(topic)
    
    try:
        # Créer tous les topics
        admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
        
        # Vérifier la création
        time.sleep(2)
        existing_topics = admin_client.list_topics()
        
        print("\n✅ RÉSULTATS:")
        print("-" * 50)
        
        success_count = 0
        for topic_config in topics_config:
            topic_name = topic_config['name']
            if topic_name in existing_topics:
                print(f"✅ {topic_name:20s} - {topic_config['partitions']} partitions")
                success_count += 1
            else:
                print(f"❌ {topic_name:20s} - Échec")
        
        print("-" * 50)
        print(f"📊 {success_count}/{len(topics_config)} topics créés avec succès")
        
        admin_client.close()
        return success_count == len(topics_config)
        
    except TopicAlreadyExistsError as e:
        print("\nℹ️  Certains topics existent déjà:")
        existing_topics = admin_client.list_topics()
        
        for topic_config in topics_config:
            topic_name = topic_config['name']
            if topic_name in existing_topics:
                print(f"  ✓ {topic_name}")
        
        print("\n✅ Tous les topics sont disponibles!")
        admin_client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création des topics: {e}")
        return False

def verify_topics():
    """Vérifie que tous les topics existent"""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=['localhost:9092'],
            client_id='topic-verifier'
        )
        
        existing_topics = admin_client.list_topics()
        required_topics = ['reddit_stream', 'twitter_stream', 'iot_sensors', 'news_feed']
        
        print("\n🔍 VÉRIFICATION DES TOPICS:")
        print("-" * 50)
        
        all_exist = True
        for topic in required_topics:
            if topic in existing_topics:
                print(f"{topic}")
            else:
                print(f" {topic} - MANQUANT")
                all_exist = False
        
        admin_client.close()
        return all_exist
        
    except Exception as e:
        print(f" Erreur de vérification: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 CONFIGURATION DES TOPICS KAFKA")
    print("=" * 50)
    print("Ce script va créer les topics nécessaires pour le projet:")
    print("  • reddit_stream (3 partitions)")
    print("  • twitter_stream (3 partitions)")
    print("  • iot_sensors (5 partitions)")
    print("  • news_feed (2 partitions)")
    print()
    
    # Créer les topics
    success = create_topics()
    
    if success:
        # Vérifier
        verify_topics()
        print("\n Configuration terminée avec succès!")
        print("\n PROCHAINES ÉTAPES:")
        print("  1. Lancer les producers: python kafka_producers.py")
        print("  2. Lancer le consumer: python spark_streaming_consumer.py")
    else:
        print("\n  Configuration incomplète")
        print("\nAssurez-vous que:")
        print("  1. Zookeeper est démarré")
        print("  2. Kafka est démarré")
        print("  3. Les services sont accessibles sur localhost:9092")
