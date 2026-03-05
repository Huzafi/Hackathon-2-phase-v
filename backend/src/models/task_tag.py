"""TaskTag junction table for many-to-many relationship between tasks and tags."""
from sqlmodel import SQLModel, Field, Relationship, Index
from datetime import datetime
from typing import Optional


class TaskTag(SQLModel, table=True):
    """Junction table for task-tag many-to-many relationship."""

    __tablename__ = "task_tags"

    task_id: int = Field(default=None, foreign_key="todos.id", primary_key=True, ondelete="CASCADE")
    tag_id: int = Field(default=None, foreign_key="tags.id", primary_key=True, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Composite primary key prevents duplicate associations
    __table_args__ = (
        Index("ix_task_tags_task_id", "task_id"),
        Index("ix_task_tags_tag_id", "tag_id"),
    )

    class Config:
        table = True
        schema_extra = {
            "example": {
                "task_id": 123,
                "tag_id": 5,
                "created_at": "2026-02-23T10:00:00Z"
            }
        }
