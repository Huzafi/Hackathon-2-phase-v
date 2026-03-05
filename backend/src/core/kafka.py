"""Kafka client configuration for event-driven architecture.

This module provides async Kafka producer and consumer clients
using aiokafka for high-throughput, reliable event processing.
"""
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaConnectionError
import logging
import json
import asyncio
from ..core.config import settings


logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """Async Kafka producer client with retry logic and graceful degradation."""

    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None
        self._brokers = settings.kafka_brokers
        self._topic = settings.kafka_topic_events
        self._connection_failed = False
        self._retry_count = 0
        self._max_retries = 3

    async def connect(self) -> None:
        """Initialize and start the Kafka producer with retry logic."""
        if self._producer is not None:
            return

        # Reset connection_failed flag to allow reconnection attempts
        self._connection_failed = False

        for attempt in range(self._max_retries):
            producer = None
            try:
                producer = AIOKafkaProducer(
                    bootstrap_servers=self._brokers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3,
                    retry_backoff_ms=100,
                    request_timeout_ms=10000,
                    connections_max_idle_ms=540000,
                )
                await producer.start()
                self._producer = producer
                logger.info(f"Kafka producer connected to {self._brokers}")
                self._connection_failed = False
                self._retry_count = 0
                return
            except (KafkaError, KafkaConnectionError, Exception) as e:
                # Close the failed producer to prevent "Unclosed" warnings
                if producer is not None:
                    try:
                        await producer.stop()
                    except Exception:
                        pass
                self._retry_count = attempt + 1
                logger.warning(f"Kafka producer connection attempt {attempt + 1}/{self._max_retries} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self._connection_failed = True
                    logger.error(f"Kafka producer failed to connect after {self._max_retries} attempts. Running in degraded mode.")

    async def disconnect(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            try:
                await self._producer.stop()
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
            finally:
                self._producer = None
                logger.info("Kafka producer disconnected")

    async def send_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: int,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Send an event to Kafka with retry logic.

        Args:
            event_type: Type of event (e.g., 'task.created')
            payload: Event payload data
            user_id: User ID for partitioning (ensures ordering per user)
            correlation_id: Optional correlation ID for tracing

        Returns:
            bool: True if sent successfully, False if Kafka unavailable
        """
        # If connection previously failed, don't retry on every call
        if self._connection_failed:
            logger.debug(f"Kafka unavailable, skipping event: {event_type}")
            return False

        if not self._producer:
            await self.connect()

        if self._connection_failed:
            return False

        event = {
            "event_type": event_type,
            "payload": payload,
            "user_id": user_id,
            "correlation_id": correlation_id,
        }

        try:
            await self._producer.send_and_wait(
                topic=self._topic,
                key=str(user_id),
                value=event
            )
            logger.debug(f"Event sent: {event_type} for user {user_id}")
            return True
        except (KafkaError, Exception) as e:
            logger.error(f"Failed to send event {event_type}: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._producer is not None and not self._connection_failed


class KafkaConsumerClient:
    """Async Kafka consumer client with graceful error handling."""

    def __init__(self):
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._brokers = settings.kafka_brokers
        self._topic = settings.kafka_topic_events
        self._group_id = settings.kafka_consumer_group
        self._connection_failed = False
        self._retry_count = 0
        self._max_retries = 3

    async def connect(self) -> bool:
        """Initialize and start the Kafka consumer with retry logic.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self._consumer is not None:
            return True

        # Reset connection_failed flag to allow reconnection attempts
        self._connection_failed = False

        for attempt in range(self._max_retries):
            consumer = None
            try:
                consumer = AIOKafkaConsumer(
                    self._topic,
                    bootstrap_servers=self._brokers,
                    group_id=self._group_id,
                    auto_offset_reset=settings.kafka_auto_offset_reset,
                    enable_auto_commit=True,
                    auto_commit_interval_ms=1000,
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
                    key_deserializer=lambda k: k.decode('utf-8') if k else None,
                    consumer_timeout_ms=1000,
                    request_timeout_ms=10000,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=3000,
                )
                await consumer.start()
                self._consumer = consumer
                logger.info(f"Kafka consumer connected to {self._brokers}")
                self._connection_failed = False
                self._retry_count = 0
                return True
            except (KafkaError, KafkaConnectionError, Exception) as e:
                # Close the failed consumer to prevent "Unclosed AIOKafkaConsumer" warnings
                if consumer is not None:
                    try:
                        await consumer.stop()
                    except Exception:
                        pass
                self._retry_count = attempt + 1
                logger.warning(f"Kafka consumer connection attempt {attempt + 1}/{self._max_retries} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self._connection_failed = True
                    logger.error(f"Kafka consumer failed to connect after {self._max_retries} attempts. Event processing disabled.")
                    return False
        return False

    async def disconnect(self) -> None:
        """Stop the Kafka consumer."""
        if self._consumer:
            try:
                await self._consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")
            finally:
                self._consumer = None
                logger.info("Kafka consumer disconnected")

    async def consume_events(self):
        """Consume events from Kafka topic with error handling.

        Yields:
            Dict containing event data (only valid events)
        """
        if not self._consumer:
            connected = await self.connect()
            if not connected:
                return

        try:
            async for message in self._consumer:
                if message.value is None:
                    logger.warning("Received message with None value, skipping")
                    continue

                event = message.value
                if not isinstance(event, dict):
                    logger.warning(f"Received non-dict event: {type(event)}, skipping")
                    continue

                logger.debug(f"Event received: {event.get('event_type')} for user {event.get('user_id')}")
                yield event
        except (KafkaError, KafkaConnectionError, Exception) as e:
            logger.error(f"Error consuming events: {e}")
            # Clean up the broken consumer so reconnect logic can create a fresh one
            await self.disconnect()
            # Don't raise - let the consumer loop handle reconnection

    @property
    def is_connected(self) -> bool:
        """Check if consumer is connected."""
        return self._consumer is not None and not self._connection_failed


# Global instances
_producer: Optional[KafkaProducerClient] = None
_consumer: Optional[KafkaConsumerClient] = None


def get_producer() -> KafkaProducerClient:
    """Get or create the Kafka producer client."""
    global _producer
    if _producer is None:
        _producer = KafkaProducerClient()
    return _producer


def get_consumer() -> KafkaConsumerClient:
    """Get or create the Kafka consumer client."""
    global _consumer
    if _consumer is None:
        _consumer = KafkaConsumerClient()
    return _consumer


async def cleanup_kafka_clients() -> None:
    """Disconnect all Kafka clients."""
    global _producer, _consumer
    if _producer:
        await _producer.disconnect()
    if _consumer:
        await _consumer.disconnect()
