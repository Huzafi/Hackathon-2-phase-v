"""Event consumer service for processing events from Kafka."""
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select
import asyncio

from ..models.event_log import EventLog, EventType
from ..core.kafka import get_consumer, get_producer
from ..core.database import get_session
from ..core.config import settings


logger = logging.getLogger(__name__)


class EventConsumer:
    """Service for consuming and processing events from Kafka.

    This service:
    1. Consumes events from Kafka topic
    2. Processes events based on event type
    3. Marks events as processed in EventLog
    4. Handles retries for failed events
    """

    def __init__(self):
        self.consumer = get_consumer()
        self._running = False
        self._reconnect_delay = 5  # seconds
        self._max_reconnect_delay = 60  # seconds

    async def start_consuming(self) -> None:
        """Start consuming events from Kafka in a background loop with reconnection logic."""
        self._running = True
        logger.info("Event consumer started")

        # Try to connect once at startup
        connected = await self.consumer.connect()
        if not connected:
            logger.warning("Kafka not available at startup. Will retry in background.")

        reconnect_delay = self._reconnect_delay

        try:
            while self._running:
                try:
                    # Only try to consume if connected
                    if self.consumer.is_connected:
                        async for event in self.consumer.consume_events():
                            if event:  # Ensure event is not None
                                await self._process_event(event)

                        # If we get here, consumer stopped gracefully
                        if self._running:
                            logger.info("Consumer iteration completed, restarting...")
                            await asyncio.sleep(1)
                    else:
                        # Not connected, try to reconnect
                        logger.info(f"Attempting to reconnect to Kafka in {reconnect_delay}s...")
                        await asyncio.sleep(reconnect_delay)

                        connected = await self.consumer.connect()
                        if connected:
                            reconnect_delay = self._reconnect_delay  # Reset delay on success
                        else:
                            # Exponential backoff
                            reconnect_delay = min(reconnect_delay * 2, self._max_reconnect_delay)

                except asyncio.CancelledError:
                    raise  # Re-raise to be caught by outer try/finally
                except Exception as e:
                    logger.error(f"Error in event consumer loop: {e}", exc_info=True)
                    # Wait before retrying to avoid tight loop on persistent errors
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, self._max_reconnect_delay)
        except asyncio.CancelledError:
            logger.info("Event consumer cancelled")
        finally:
            # Always disconnect the Kafka consumer to prevent resource leaks
            await self.consumer.disconnect()
            logger.info("Kafka consumer disconnected during shutdown")
    
    async def stop_consuming(self) -> None:
        """Stop consuming events."""
        self._running = False
        logger.info("Event consumer stopped")
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single event from Kafka.

        Args:
            event: Event data from Kafka
        """
        event_type = event.get("event_type")
        payload = event.get("payload")
        user_id = event.get("user_id")
        correlation_id = event.get("correlation_id")

        if not event_type or not payload or not user_id:
            logger.warning(f"Invalid event received: {event}")
            return

        logger.debug(f"Processing event: {event_type} for user {user_id}")

        try:
            # Route event to appropriate handler
            if event_type.startswith("task."):
                await self._handle_task_event(event_type, payload, user_id)
            elif event_type.startswith("tag."):
                await self._handle_tag_event(event_type, payload, user_id)
            elif event_type.startswith("reminder."):
                await self._handle_reminder_event(event_type, payload, user_id)
            elif event_type.startswith("recurrence."):
                await self._handle_recurrence_event(event_type, payload, user_id)
            else:
                logger.warning(f"Unknown event type: {event_type}")

            # Mark event as processed in database
            if correlation_id:
                self._mark_event_processed(correlation_id)

        except Exception as e:
            logger.error(f"Failed to process event {event_type}: {e}", exc_info=True)
            # Don't mark as processed - will be retried later
    
    async def _handle_task_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: int
    ) -> None:
        """Handle task-related events.

        Args:
            event_type: Specific task event type
            payload: Event payload
            user_id: User ID
        """
        logger.info(f"Handling task event: {event_type} for user {user_id}")

        # Example: Send notifications, update analytics, trigger workflows
        if event_type == "task.created":
            task_id = payload.get("task_id")
            logger.info(f"Task created: {task_id}")
        elif event_type == "task.completed":
            task_id = payload.get("task_id")
            logger.info(f"Task completed: {task_id}")
        # Add more handlers as needed

    async def _handle_tag_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: int
    ) -> None:
        """Handle tag-related events."""
        logger.info(f"Handling tag event: {event_type} for user {user_id}")

    async def _handle_reminder_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: int
    ) -> None:
        """Handle reminder-related events."""
        logger.info(f"Handling reminder event: {event_type} for user {user_id}")

    async def _handle_recurrence_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        user_id: int
    ) -> None:
        """Handle recurrence-related events."""
        logger.info(f"Handling recurrence event: {event_type} for user {user_id}")
    
    def _mark_event_processed(self, correlation_id: str) -> None:
        """Mark an event as processed in the database.

        Args:
            correlation_id: Correlation ID of the event
        """
        try:
            with next(get_session()) as session:
                statement = select(EventLog).where(
                    EventLog.correlation_id == correlation_id
                )
                event_log = session.exec(statement).first()

                if event_log:
                    event_log.processed = True
                    session.add(event_log)
                    session.commit()
                    logger.debug(f"Event marked as processed: {correlation_id}")
        except Exception as e:
            logger.error(f"Failed to mark event as processed: {e}")

    async def retry_unprocessed_events(self) -> int:
        """Retry unprocessed events from the database.

        Returns:
            Number of events retried
        """
        try:
            with next(get_session()) as session:
                # Get unprocessed events older than 5 minutes
                cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                statement = select(EventLog).where(
                    EventLog.processed == False,
                    EventLog.timestamp < cutoff_time
                ).limit(100)

                events = session.exec(statement).all()
                count = 0

                for event_log in events:
                    try:
                        # Reconstruct event and send to Kafka
                        producer = get_producer()

                        success = await producer.send_event(
                            event_type=event_log.event_type.value,
                            payload=event_log.payload,
                            user_id=event_log.user_id,
                            correlation_id=event_log.correlation_id
                        )

                        if success:
                            event_log.processed = True
                            session.add(event_log)
                            count += 1
                    except Exception as e:
                        logger.error(f"Failed to retry event {event_log.id}: {e}")

                if count > 0:
                    session.commit()
                    logger.info(f"Successfully retried {count} events")

                return count
        except Exception as e:
            logger.error(f"Error in retry_unprocessed_events: {e}")
            return 0


# Global instance
_event_consumer: Optional[EventConsumer] = None


def get_event_consumer() -> EventConsumer:
    """Get or create the EventConsumer instance."""
    global _event_consumer
    if _event_consumer is None:
        _event_consumer = EventConsumer()
    return _event_consumer


async def cleanup_event_consumer() -> None:
    """Stop and cleanup the event consumer."""
    global _event_consumer
    if _event_consumer:
        await _event_consumer.stop_consuming()
        _event_consumer = None
