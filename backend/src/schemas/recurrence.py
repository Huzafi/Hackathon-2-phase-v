"""Recurrence rule request and response schemas."""
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from ..models.recurrence import RecurrencePattern


class RecurrenceCreate(BaseModel):
    """Request schema for creating a recurrence rule."""
    pattern: RecurrencePattern = Field(..., description="Recurrence pattern")
    interval: int = Field(default=1, ge=1, description="Repeat every N periods")
    start_date: date = Field(..., description="Start date for recurrence")
    end_date: Optional[date] = Field(None, description="Optional end date")
    by_weekday: Optional[str] = Field(
        None,
        max_length=50,
        description="Comma-separated weekdays (MO,TU,WE,TH,FR,SA,SU)"
    )
    by_monthday: Optional[int] = Field(None, ge=1, le=31, description="Day of month")

    @validator('by_weekday')
    def validate_by_weekday(cls, v):
        """Validate weekday format."""
        if v:
            valid_days = {'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'}
            days = [d.strip().upper() for d in v.split(',')]
            if not all(day in valid_days for day in days):
                raise ValueError('Invalid weekday. Use MO,TU,WE,TH,FR,SA,SU')
        return v


class RecurrenceUpdate(BaseModel):
    """Request schema for updating a recurrence rule."""
    pattern: Optional[RecurrencePattern] = None
    interval: Optional[int] = Field(None, ge=1)
    end_date: Optional[date] = None
    by_weekday: Optional[str] = None
    by_monthday: Optional[int] = Field(None, ge=1, le=31)


class RecurrenceResponse(BaseModel):
    """Response schema for recurrence rule data."""
    id: int
    task_id: int
    pattern: RecurrencePattern
    interval: int
    start_date: date
    end_date: Optional[date]
    by_weekday: Optional[str]
    by_monthday: Optional[int]
    last_generated: Optional[datetime]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class RecurrenceListResponse(BaseModel):
    """Response schema for list of recurrence rules."""
    recurrence_rules: List[RecurrenceResponse]
    total: int
