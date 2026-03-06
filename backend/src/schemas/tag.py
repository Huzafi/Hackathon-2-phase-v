"""Tag request and response schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TagCreate(BaseModel):
    """Request schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field(default="#3B82F6", pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")


class TagUpdate(BaseModel):
    """Request schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")


class TagResponse(BaseModel):
    """Response schema for tag data."""
    id: int
    user_id: int
    name: str
    color: str
    created_at: datetime
    task_count: Optional[int] = Field(None, description="Number of tasks with this tag")

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """Response schema for list of tags."""
    tags: List[TagResponse]
    total: int
    page: int
    limit: int
