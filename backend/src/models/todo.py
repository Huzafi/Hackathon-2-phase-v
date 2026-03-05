"""Todo database model."""
from sqlmodel import SQLModel, Field, Relationship, Index
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from enum import Enum
from .task_tag import TaskTag

if TYPE_CHECKING:
    from .user import User
    from .tag import Tag
    from .recurrence import RecurrenceRule
    from .reminder import Reminder


class PriorityEnum(str, Enum):
    """Priority levels for tasks."""
    high = "high"
    medium = "medium"
    low = "low"


class Todo(SQLModel, table=True):
    """Todo model for task management."""

    __tablename__ = "todos"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, nullable=False)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_completed: bool = Field(default=False, nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    due_date: Optional[datetime] = Field(default=None, index=True)
    priority: PriorityEnum = Field(default=PriorityEnum.medium, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to user (many todos belong to one user)
    user: Optional["User"] = Relationship(back_populates="todos")
    
    # Relationship to tags (many-to-many)
    tags: List["Tag"] = Relationship(back_populates="todos", link_model=TaskTag)
    
    # Relationship to recurrence rule (one-to-one)
    recurrence_rule: Optional["RecurrenceRule"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"uselist": False}
    )
    
    # Relationship to reminders (one-to-many)
    reminders: List["Reminder"] = Relationship(back_populates="task")

    # Composite index for efficient user-scoped queries
    __table_args__ = (
        Index("ix_todos_user_created", "user_id", "created_at"),
        Index("ix_todos_due_date", "due_date"),
        Index("ix_todos_priority", "priority"),
    )
