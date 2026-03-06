"""RecurrenceRule database model for recurring tasks."""
from sqlmodel import SQLModel, Field, Relationship, Index
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .todo import Todo


class RecurrencePattern(str, Enum):
    """Recurrence pattern types."""
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class RecurrenceRule(SQLModel, table=True):
    """Recurrence rule model for defining how tasks repeat."""

    __tablename__ = "recurrence_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(
        default=None,
        foreign_key="todos.id",
        unique=True,
        nullable=False,
        index=True,
        ondelete="CASCADE"
    )
    pattern: RecurrencePattern = Field(nullable=False)
    interval: int = Field(default=1, ge=1, nullable=False)
    start_date: date = Field(nullable=False)
    end_date: Optional[date] = Field(default=None, nullable=True)
    by_weekday: Optional[str] = Field(
        default=None,
        max_length=50,
        nullable=True,
        description="Comma-separated weekdays (MO,TU,WE,TH,FR,SA,SU)"
    )
    by_monthday: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        nullable=True,
        description="Day of month (1-31)"
    )
    last_generated: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to task
    task: Optional["Todo"] = Relationship(back_populates="recurrence_rule")

    # Indexes
    __table_args__ = (
        Index("idx_recurrence_rules_pattern", "pattern"),
        Index("idx_recurrence_rules_last_generated", "last_generated"),
    )

    class Config:
        table = True
        schema_extra = {
            "example": {
                "id": 1,
                "task_id": 123,
                "pattern": "weekly",
                "interval": 1,
                "start_date": "2026-02-23",
                "end_date": None,
                "by_weekday": "MO",
                "by_monthday": None,
                "last_generated": None,
                "created_at": "2026-02-23T10:00:00Z"
            }
        }

    def is_active(self) -> bool:
        """Check if recurrence rule is still active."""
        if self.end_date and datetime.utcnow().date() > self.end_date:
            return False
        return True
