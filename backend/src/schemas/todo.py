"""Todo request and response schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from ..models.todo import PriorityEnum


class TodoCreate(BaseModel):
    """Request schema for creating a new todo."""
    title: str = Field(..., min_length=1, max_length=200, description="Todo title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    due_date: Optional[datetime] = Field(None, description="Due date and time")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Priority level")
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs")


class TodoUpdate(BaseModel):
    """Request schema for full todo update (PUT)."""
    title: str = Field(..., min_length=1, max_length=200, description="Todo title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    is_completed: Optional[bool] = Field(None, description="Completion status")
    due_date: Optional[datetime] = Field(None, description="Due date and time")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Priority level")
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs")


class TodoPatch(BaseModel):
    """Request schema for partial todo update (PATCH)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Todo title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    is_completed: Optional[bool] = Field(None, description="Completion status")
    due_date: Optional[datetime] = Field(None, description="Due date and time")
    priority: Optional[PriorityEnum] = Field(None, description="Priority level")
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs")


class TagResponse(BaseModel):
    """Response schema for tag data."""
    id: int
    name: str
    color: str
    
    class Config:
        from_attributes = True


class TodoResponse(BaseModel):
    """Response schema for todo data."""
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    user_id: int
    due_date: Optional[datetime]
    priority: PriorityEnum
    tags: Optional[List[TagResponse]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    """Response schema for list of todos."""
    todos: List[TodoResponse]
    total: int
    page: int
    limit: int
