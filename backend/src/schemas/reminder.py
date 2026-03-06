"""Reminder request and response schemas."""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class ReminderCreate(BaseModel):
    """Request schema for creating a reminder."""
    task_id: int = Field(..., description="Task ID to remind")
    trigger_time: datetime = Field(..., description="When to trigger the reminder")

    @validator('trigger_time')
    def validate_trigger_time(cls, v):
        """Validate trigger time is not in the past."""
        if v <= datetime.utcnow():
            raise ValueError('trigger_time must be in the future')
        return v


class ReminderUpdate(BaseModel):
    """Request schema for updating a reminder."""
    trigger_time: Optional[datetime] = None


class ReminderResponse(BaseModel):
    """Response schema for reminder data."""
    id: int
    task_id: int
    trigger_time: datetime
    delivered: bool
    created_at: datetime
    task_title: Optional[str] = None  # Optional: include task title for convenience

    class Config:
        from_attributes = True


class ReminderListResponse(BaseModel):
    """Response schema for list of reminders."""
    reminders: List[ReminderResponse]
    total: int
    page: int
    limit: int
