"""Event producer service for publishing events to Kafka."""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from sqlmodel import Session
from ..models.event_log import EventLog, EventType
from ..core.kafka import get_producer
from ..core.config import settings


logger = logging.getLogger(__name__)


class EventProducer:
    """Service for producing events to both EventLog table and Kafka.
    
    This service implements the dual-write pattern:
    1. Store event in EventLog table (guaranteed persistence)
    2. Publish event to Kafka (real-time processing)
    
    If Kafka is unavailable, the event is still stored in the database
    and can be processed later.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.producer = get_producer()
    
    async def publish(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish an event to EventLog and Kafka.
        
        Args:
            event_type: Type of event (e.g., task.created)
            payload: Event payload data
            user_id: User who performed the action
            metadata: Optional additional context
        
        Returns:
            correlation_id: Unique correlation ID for tracing
        
        Raises:
            Exception: If database write fails (Kafka failures are logged but don't fail the operation)
        """
        # Generate correlation ID for tracing
        correlation_id = str(uuid.uuid4())
        
        # Step 1: Store in EventLog (guaranteed persistence)
        event_log = EventLog(
            user_id=user_id,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            extra_metadata=metadata,
            processed=False  # Will be marked True after Kafka publish
        )
        
        self.session.add(event_log)
        self.session.commit()
        self.session.refresh(event_log)
        
        logger.info(f"Event stored in EventLog: {event_type.value} (id={event_log.id})")
        
        # Step 2: Publish to Kafka (async, don't block on failure)
        if settings.enable_event_sourcing:
            try:
                await self._publish_to_kafka(
                    event_type=event_type.value,
                    payload=payload,
                    user_id=user_id,
                    correlation_id=correlation_id
                )
                # Mark as processed if Kafka publish succeeds
                event_log.processed = True
                self.session.add(event_log)
                self.session.commit()
                logger.info(f"Event published to Kafka: {event_type.value}")
            except Exception as e:
                # Log error but don't fail the operation
                # Event will be processed by background task later
                logger.error(f"Failed to publish event to Kafka: {e}")
                # Event remains in EventLog with processed=False for retry
        
        return correlation_id
    
    async def _publish_to_kafka(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: int,
        correlation_id: str
    ) -> None:
        """Publish event to Kafka topic.
        
        Args:
            event_type: Type of event
            payload: Event payload
            user_id: User ID (used as partition key)
            correlation_id: Correlation ID for tracing
        """
        # Ensure producer is connected
        if not self.producer.is_connected:
            await self.producer.connect()
        
        # Send event to Kafka
        await self.producer.send_event(
            event_type=event_type,
            payload=payload,
            user_id=user_id,
            correlation_id=correlation_id
        )
    
    def publish_sync(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synchronous wrapper for publish (for non-async contexts).
        
        Note: This should only be used when async is not available.
        Prefer the async publish() method.
        """
        import asyncio
        return asyncio.run(self.publish(event_type, payload, user_id, metadata))


# Convenience function for creating EventProducer
def get_event_producer(session: Session) -> EventProducer:
    """Get an EventProducer instance for the given session."""
    return EventProducer(session)
