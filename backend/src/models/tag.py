"""Tag database model for task categorization."""
from sqlmodel import SQLModel, Field, Relationship, Index
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from .task_tag import TaskTag

if TYPE_CHECKING:
    from .todo import Todo
    from .user import User


class Tag(SQLModel, table=True):
    """Tag model for categorizing tasks."""

    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    name: str = Field(max_length=50, nullable=False, index=True)
    color: str = Field(default="#3B82F6", max_length=7, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to user (many tags belong to one user)
    user: Optional["User"] = Relationship(back_populates="tags")
    
    # Relationship to tasks (many-to-many)
    todos: List["Todo"] = Relationship(back_populates="tags", link_model=TaskTag)

    # Unique constraint per user (case-insensitive)
    __table_args__ = (
        Index("ix_tags_user_name", "user_id", "name", unique=True),
    )

    class Config:
        table = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "name": "work",
                "color": "#3B82F6",
                "created_at": "2026-02-23T10:00:00Z"
            }
        }
