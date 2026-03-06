"""Reminder database model for task reminders."""
from sqlmodel import SQLModel, Field, Relationship, Index
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .todo import Todo


class Reminder(SQLModel, table=True):
    """Reminder model for task notifications."""

    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(
        default=None,
        foreign_key="todos.id",
        nullable=False,
        index=True,
        ondelete="CASCADE"
    )
    trigger_time: datetime = Field(nullable=False, index=True)
    delivered: bool = Field(default=False, nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to task
    task: Optional["Todo"] = Relationship(back_populates="reminders")

    # Indexes
    __table_args__ = (
        Index("idx_reminders_trigger_time", "trigger_time"),
        Index("idx_reminders_delivered", "delivered"),
        Index("idx_reminders_pending", "trigger_time", "delivered"),
    )

    class Config:
        table = True
        schema_extra = {
            "example": {
                "id": 1,
                "task_id": 123,
                "trigger_time": "2026-02-28T09:00:00Z",
                "delivered": False,
                "created_at": "2026-02-23T10:00:00Z"
            }
        }

    def is_overdue(self) -> bool:
        """Check if reminder is overdue (trigger time passed and not delivered)."""
        return datetime.utcnow() > self.trigger_time and not self.delivered
