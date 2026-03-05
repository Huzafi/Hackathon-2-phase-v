"""Event schemas for API requests and responses."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
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


class EventCreate(BaseModel):
    """Schema for creating a new event."""
    
    event_type: EventType = Field(..., description="Type of event")
    payload: Dict[str, Any] = Field(..., description="Event data")
    correlation_id: Optional[str] = Field(None, max_length=36, description="Correlation ID for tracing")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class EventResponse(BaseModel):
    """Schema for event response."""
    
    id: int = Field(..., description="Event ID")
    user_id: int = Field(..., description="User ID")
    event_type: EventType = Field(..., description="Type of event")
    payload: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")
    processed: bool = Field(..., description="Processing status")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for list of events."""
    
    events: List[EventResponse] = Field(..., description="List of events")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")


class EventUpdate(BaseModel):
    """Schema for updating event processing status."""
    
    processed: bool = Field(..., description="Processing status")
