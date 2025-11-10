"""
Simple Kafka sanity test for this workspace.
- Produces one JSON message to topic `test_topic`.
- Then creates a consumer that polls for up to `--timeout` seconds and prints received messages.

Run from PowerShell: python test_kafka_client.py
"""
import argparse
import json
import time
from datetime import datetime
import uuid

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError


def produce_message(bootstrap_servers, topic):
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    payload = {
        'ping': 'ok',
        't': time.time(),
        'iso': datetime.utcnow().isoformat() + 'Z'
    }
    try:
        fut = producer.send(topic, payload)
        record_metadata = fut.get(timeout=10)
        print(f"Produced to {record_metadata.topic} partition={record_metadata.partition} offset={record_metadata.offset}")
    except KafkaError as e:
        print("Failed to send message:", e)
    finally:
        try:
            producer.flush()
            producer.close()
        except Exception:
            pass


def consume_messages(bootstrap_servers, topic, timeout_s=5, auto_offset='earliest'):
    # Use a unique group id so this consumer doesn't have committed offsets
    group_id = f"test_kafka_client_{uuid.uuid4().hex}"
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset=auto_offset,
        group_id=group_id,
        consumer_timeout_ms=int(timeout_s * 1000),
        value_deserializer=lambda b: json.loads(b.decode('utf-8'))
    )
    print(f"Polling topic '{topic}' for up to {timeout_s} seconds...")
    got = 0
    try:
        for msg in consumer:
            got += 1
            print(f"Received msg partition={msg.partition} offset={msg.offset} value={msg.value}")
    except Exception as e:
        print("Consumer error:", e)
    finally:
        consumer.close()
    if got == 0:
        print("No messages received (within timeout).")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Kafka produce/consume test')
    parser.add_argument('--bootstrap', '-b', nargs='+', default=['localhost:9092'], help='Kafka bootstrap servers')
    parser.add_argument('--topic', '-t', default='test_topic', help='Topic to use')
    parser.add_argument('--timeout', type=float, default=5.0, help='Consumer poll timeout in seconds')
    parser.add_argument('--auto-offset', choices=['earliest', 'latest'], default='earliest',
                        help='auto_offset_reset for the consumer (earliest will read newly produced messages)')
    parser.add_argument('--produce-only', action='store_true', help='Only produce a message and exit')
    args = parser.parse_args()

    print('Kafka sanity test - bootstrap servers:', args.bootstrap)
    produce_message(args.bootstrap, args.topic)
    if not args.produce_only:
    # give a small delay to allow the broker to persist the message
    time.sleep(0.5)
    consume_messages(args.bootstrap, args.topic, timeout_s=args.timeout, auto_offset=args.auto_offset)
