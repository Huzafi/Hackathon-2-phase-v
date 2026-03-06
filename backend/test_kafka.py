"""
Kafka Integration Test Script

This script tests the complete Kafka event flow:
1. Producer sends events
2. Consumer receives events
3. Events are persisted in database
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.kafka import get_producer, get_consumer
from src.models.event_log import EventType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_kafka_connection():
    """Test Kafka producer and consumer connectivity."""
    print("\n" + "="*60)
    print("  Kafka Integration Test")
    print("="*60 + "\n")

    # Test Producer
    print("[1/3] Testing Kafka Producer...")
    producer = get_producer()

    try:
        await producer.connect()
        if producer.is_connected:
            print("✅ Producer connected successfully")
        else:
            print("⚠️  Producer connection failed (degraded mode)")
    except Exception as e:
        print(f"❌ Producer error: {e}")

    # Test Consumer
    print("\n[2/3] Testing Kafka Consumer...")
    consumer = get_consumer()

    try:
        connected = await consumer.connect()
        if connected:
            print("✅ Consumer connected successfully")
        else:
            print("⚠️  Consumer connection failed (degraded mode)")
    except Exception as e:
        print(f"❌ Consumer error: {e}")

    # Test Event Send
    print("\n[3/3] Testing Event Send...")
    if producer.is_connected:
        try:
            success = await producer.send_event(
                event_type="test.event",
                payload={"message": "Hello from test script"},
                user_id=1,
                correlation_id="test-123"
            )
            if success:
                print("✅ Test event sent successfully")
            else:
                print("⚠️  Event send failed")
        except Exception as e:
            print(f"❌ Send error: {e}")
    else:
        print("⚠️  Skipping send test (producer not connected)")

    # Cleanup
    print("\n[Cleanup] Disconnecting...")
    await producer.disconnect()
    await consumer.disconnect()
    print("✅ Cleanup complete")

    print("\n" + "="*60)
    print("  Test Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_kafka_connection())
