#!/usr/bin/env python3
"""
Script de monitoring du système Multi-Source Analytics
Affiche l'état de tous les composants en temps réel
"""

from kafka import KafkaConsumer, KafkaAdminClient
from kafka.errors import NoBrokersAvailable
import json
from datetime import datetime
import time

def check_kafka_status():
    """Vérifie l'état de Kafka et des topics"""
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=['localhost:9092'],
            client_id='status-checker',
            request_timeout_ms=5000
        )
        
        topics = admin.list_topics()
        print("✅ Kafka: ONLINE")
        print(f"   Topics disponibles: {len(topics)}")
        
        required_topics = ['reddit_stream', 'twitter_stream', 'iot_sensors', 'news_feed']
        for topic in required_topics:
            if topic in topics:
                print(f"   ✓ {topic}")
            else:
                print(f"   ✗ {topic} (MANQUANT)")
        
        admin.close()
        return True
        
    except NoBrokersAvailable:
        print("❌ Kafka: OFFLINE")
        return False
    except Exception as e:
        print(f"❌ Kafka: ERREUR ({e})")
        return False

def check_messages_in_topics():
    """Compte les messages dans chaque topic"""
    topics = ['reddit_stream', 'twitter_stream', 'iot_sensors', 'news_feed']
    
    print("\n📊 MESSAGES DANS LES TOPICS:")
    print("-" * 50)
    
    try:
        for topic in topics:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=['localhost:9092'],
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                consumer_timeout_ms=2000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            # Compter les messages
            message_count = 0
            last_timestamp = None
            
            for message in consumer:
                message_count += 1
                try:
                    last_timestamp = message.value.get('timestamp', 'N/A')
                except:
                    pass
            
            consumer.close()
            
            if message_count > 0:
                print(f"✅ {topic:20s}: {message_count:4d} messages (dernier: {last_timestamp})")
            else:
                print(f"⚠️  {topic:20s}: Aucun message")
        
    except Exception as e:
        print(f"❌ Erreur lecture topics: {e}")

def monitor_realtime(duration_seconds=30):
    """Monitore les messages en temps réel"""
    topics = ['reddit_stream', 'twitter_stream', 'iot_sensors', 'news_feed']
    
    print(f"\n📡 MONITORING EN TEMPS RÉEL ({duration_seconds}s)")
    print("=" * 50)
    
    try:
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='realtime-monitor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        start_time = time.time()
        message_counts = {topic: 0 for topic in topics}
        
        print("En attente de messages... (Ctrl+C pour arrêter)\n")
        
        for message in consumer:
            if time.time() - start_time > duration_seconds:
                break
            
            topic = message.topic
            message_counts[topic] += 1
            
            # Afficher le message
            timestamp = message.value.get('timestamp', 'N/A')
            source = message.value.get('source', 'N/A')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"{topic:20s} | Source: {source:10s} | TS: {timestamp}")
        
        consumer.close()
        
        # Statistiques
        print("\n" + "=" * 50)
        print("📊 STATISTIQUES:")
        total = sum(message_counts.values())
        for topic, count in message_counts.items():
            print(f"   {topic:20s}: {count:4d} messages")
        print(f"   {'TOTAL':20s}: {total:4d} messages")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur monitoring: {e}")

def display_system_status():
    """Affiche le statut complet du système"""
    print("=" * 60)
    print("🚀 MULTI-SOURCE ANALYTICS SYSTEM - STATUS")
    print("=" * 60)
    print(f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Kafka status
    print("🔍 ÉTAT DES SERVICES:")
    print("-" * 60)
    kafka_ok = check_kafka_status()
    
    if kafka_ok:
        # Messages dans les topics
        check_messages_in_topics()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Afficher le statut initial
    display_system_status()
    
    # Demander si on veut monitorer en temps réel
    print("\nOptions:")
    print("  1. Monitoring temps réel (30s)")
    print("  2. Monitoring temps réel (60s)")
    print("  3. Quitter")
    
    try:
        choice = input("\nVotre choix (1-3): ").strip()
        
        if choice == "1":
            monitor_realtime(30)
        elif choice == "2":
            monitor_realtime(60)
        else:
            print("👋 Au revoir!")
    except:
        print("\n👋 Au revoir!")
