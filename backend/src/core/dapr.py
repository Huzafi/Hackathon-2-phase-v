"""Dapr client configuration for distributed application runtime.

This module provides Dapr client initialization for:
- State management (reminder storage)
- Pub/Sub (event publishing)
- Actor runtime (reminder scheduling)
"""
from typing import Optional, Dict, Any
from dapr.clients import DaprClient
from dapr.clients.grpc._response import StateResponse
import logging
import json
from ..core.config import settings


logger = logging.getLogger(__name__)


class DaprClientWrapper:
    """Wrapper for Dapr client with state management and pub/sub."""
    
    def __init__(self):
        self._client: Optional[DaprClient] = None
        self._state_store_name = "statestore"
        self._pubsub_name = "pubsub"
    
    def get_client(self) -> DaprClient:
        """Get or create the Dapr client."""
        if self._client is None:
            self._client = DaprClient()
            logger.info("Dapr client initialized")
        return self._client
    
    def close(self) -> None:
        """Close the Dapr client."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Dapr client closed")
    
    # State Management Methods
    
    def save_state(
        self,
        key: str,
        value: Dict[str, Any],
        state_store_name: Optional[str] = None
    ) -> None:
        """Save state to Dapr state store.
        
        Args:
            key: State key
            value: State value (will be JSON serialized)
            state_store_name: Optional state store name (defaults to taskstatestore)
        """
        client = self.get_client()
        store_name = state_store_name or self._state_store_name
        
        try:
            client.save_state(
                store_name=store_name,
                key=key,
                value=json.dumps(value)
            )
            logger.debug(f"State saved: {key}")
        except Exception as e:
            logger.error(f"Failed to save state {key}: {e}")
            raise
    
    def get_state(
        self,
        key: str,
        state_store_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get state from Dapr state store.
        
        Args:
            key: State key
            state_store_name: Optional state store name
            
        Returns:
            State value as dict, or None if not found
        """
        client = self.get_client()
        store_name = state_store_name or self._state_store_name
        
        try:
            response: StateResponse = client.get_state(
                store_name=store_name,
                key=key
            )
            if response.data:
                return json.loads(response.data.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Failed to get state {key}: {e}")
            raise
    
    def delete_state(
        self,
        key: str,
        state_store_name: Optional[str] = None
    ) -> None:
        """Delete state from Dapr state store.
        
        Args:
            key: State key
            state_store_name: Optional state store name
        """
        client = self.get_client()
        store_name = state_store_name or self._state_store_name
        
        try:
            client.delete_state(
                store_name=store_name,
                key=key
            )
            logger.debug(f"State deleted: {key}")
        except Exception as e:
            logger.error(f"Failed to delete state {key}: {e}")
            raise
    
    # Pub/Sub Methods
    
    def publish_event(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        pubsub_name: Optional[str] = None
    ) -> None:
        """Publish an event to Dapr pub/sub.
        
        Args:
            topic: Topic to publish to
            event_type: Type of event
            data: Event data
            pubsub_name: Optional pubsub name (defaults to taskpubsub)
        """
        client = self.get_client()
        pubsub_name = pubsub_name or self._pubsub_name
        
        try:
            client.publish_event(
                pubsub_name=pubsub_name,
                topic_name=topic,
                data=json.dumps({
                    "event_type": event_type,
                    "data": data
                }),
                data_content_type='application/json'
            )
            logger.debug(f"Event published to {topic}: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} to {topic}: {e}")
            raise
    
    # Actor Timer Methods (for reminders)
    
    def register_reminder(
        self,
        actor_type: str,
        actor_id: str,
        reminder_name: str,
        due_time: str,
        period: str,
        data: Dict[str, Any]
    ) -> None:
        """Register a reminder for an actor.
        
        Args:
            actor_type: Type of actor
            actor_id: Actor ID
            reminder_name: Name of the reminder
            due_time: When to trigger the reminder (e.g., "1h", "30m", "2026-02-28T09:00:00")
            period: How often to repeat (empty for one-time)
            data: Reminder data to pass to callback
        """
        client = self.get_client()
        
        try:
            client.register_actor_reminder(
                actor_type=actor_type,
                actor_id=actor_id,
                name=reminder_name,
                due_time=due_time,
                period=period,
                data=json.dumps(data)
            )
            logger.debug(f"Reminder registered: {reminder_name} for {actor_type}:{actor_id}")
        except Exception as e:
            logger.error(f"Failed to register reminder {reminder_name}: {e}")
            raise
    
    def unregister_reminder(
        self,
        actor_type: str,
        actor_id: str,
        reminder_name: str
    ) -> None:
        """Unregister a reminder for an actor.
        
        Args:
            actor_type: Type of actor
            actor_id: Actor ID
            reminder_name: Name of the reminder
        """
        client = self.get_client()
        
        try:
            client.unregister_actor_reminder(
                actor_type=actor_type,
                actor_id=actor_id,
                name=reminder_name
            )
            logger.debug(f"Reminder unregistered: {reminder_name} for {actor_type}:{actor_id}")
        except Exception as e:
            logger.error(f"Failed to unregister reminder {reminder_name}: {e}")
            raise


# Global instance
_dapr_client: Optional[DaprClientWrapper] = None


def get_dapr_client() -> Optional[DaprClientWrapper]:
    """Get or create the Dapr client wrapper. Returns None if Dapr is disabled."""
    global _dapr_client
    if not settings.enable_dapr:
        logger.debug("Dapr is disabled, returning None")
        return None
    if _dapr_client is None:
        _dapr_client = DaprClientWrapper()
    return _dapr_client


def cleanup_dapr_client() -> None:
    """Close the Dapr client."""
    global _dapr_client
    if _dapr_client:
        _dapr_client.close()
        _dapr_client = None
