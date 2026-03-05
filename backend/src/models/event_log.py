"""EventLog model for event sourcing and audit trail."""
from sqlalchemy import Column, JSON
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Enumeration of all event types in the system."""
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    
    # Tag events
    TAG_CREATED = "tag.created"
    TAG_UPDATED = "tag.updated"
    TAG_DELETED = "tag.deleted"
    
    # Reminder events
    REMINDER_SET = "reminder.set"
    REMINDER_DELIVERED = "reminder.delivered"
    REMINDER_DELETED = "reminder.deleted"
    
    # Recurrence events
    RECURRENCE_SET = "recurrence.set"
    RECURRENCE_REMOVED = "recurrence.removed"
    RECURRENCE_GENERATED = "recurrence.generated"
    
    # Search events
    SEARCH_PERFORMED = "search.performed"


class EventLog(SQLModel, table=True):
    """Event log entry for audit trail and event sourcing.
    
    This model stores all state changes in the system as immutable events.
    Events are append-only and can be used for:
    - Audit trail
    - Debugging
    - Event replay
    - Analytics
    """
    
    __tablename__ = "event_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    event_type: EventType = Field(index=True)
    payload: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=False))
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    processed: bool = Field(default=False, index=True)
    correlation_id: Optional[str] = Field(default=None, max_length=36, index=True)
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column("metadata", JSON, nullable=True))
