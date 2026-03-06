"""Todo API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from datetime import datetime
from typing import Optional, List
import asyncio

from ..core.database import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..models.todo import PriorityEnum
from ..schemas.todo import TodoCreate, TodoUpdate, TodoPatch, TodoResponse, TodoListResponse
from ..services.task_service import get_task_service, TaskService
from ..services.search_service import get_search_service


router = APIRouter(prefix="/api/todos", tags=["Todos"])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new todo for the authenticated user.
    
    - Title is required (1-200 characters)
    - Description is optional (max 1000 characters)
    - Due date is optional
    - Priority defaults to 'medium' (high/medium/low)
    - Tag IDs are optional (must belong to user)
    - User ID is automatically set from JWT token
    - Returns created todo with timestamps and tags
    """
    task_service = get_task_service(session)
    
    try:
        task = await task_service.create_task(
            title=todo_data.title,
            user_id=current_user.id,
            description=todo_data.description,
            due_date=todo_data.due_date,
            priority=todo_data.priority,
            tag_ids=todo_data.tag_ids
        )
        return TodoResponse.model_validate(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=TodoListResponse)
def list_todos(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    priority: Optional[PriorityEnum] = Query(None, description="Filter by priority"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (completed, incomplete, overdue)"),
    tags: Optional[str] = Query(None, description="Filter by tag IDs (comma-separated)"),
    due_date_from: Optional[datetime] = Query(None, description="Filter tasks due on or after this date"),
    due_date_to: Optional[datetime] = Query(None, description="Filter tasks due on or before this date"),
    q: Optional[str] = Query(None, description="Search keyword"),
    sort_by: str = Query("created_at", description="Sort field (due_date, priority, created_at, title)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List all todos for the authenticated user with filters, search, and pagination.
    
    - Returns todos in reverse chronological order by default
    - Supports filtering by priority, status, tags, due date range
    - Supports search by keyword in title/description
    - Supports sorting by due_date, priority, created_at, title
    - Only returns todos belonging to the authenticated user
    - User isolation enforced at query level
    """
    task_service = get_task_service(session)
    
    # Parse tag IDs
    tag_ids = None
    if tags:
        try:
            tag_ids = [int(id.strip()) for id in tags.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag IDs. Use comma-separated integers."
            )
    
    result = task_service.list_tasks(
        user_id=current_user.id,
        priority=priority,
        status=status_filter,
        tag_ids=tag_ids,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        search_query=q,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )
    
    return TodoListResponse(
        tasks=[TodoResponse.model_validate(task) for task in result["tasks"]],
        total=result["total"],
        page=result["page"],
        limit=result["limit"]
    )


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific todo by ID.
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Returns 404 if todo doesn't exist
    - Includes tags in response
    """
    task_service = get_task_service(session)
    
    try:
        task = task_service.get_task(todo_id, current_user.id)
        return TodoResponse.model_validate(task)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update a todo (full update - replaces all fields).
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Updates all provided fields
    - Tag IDs replace existing tags
    - Automatically updates updated_at timestamp
    """
    task_service = get_task_service(session)
    
    try:
        task = await task_service.update_task(
            task_id=todo_id,
            user_id=current_user.id,
            title=todo_data.title,
            description=todo_data.description,
            due_date=todo_data.due_date,
            priority=todo_data.priority,
            tag_ids=todo_data.tag_ids,
            is_completed=todo_data.is_completed
        )
        return TodoResponse.model_validate(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )


@router.patch("/{todo_id}", response_model=TodoResponse)
async def patch_todo(
    todo_id: int,
    todo_data: TodoPatch,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Partially update a todo (only updates provided fields).
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Updates only the fields provided in request
    - Tag IDs replace existing tags if provided
    - Automatically updates updated_at timestamp
    """
    task_service = get_task_service(session)
    
    try:
        task = await task_service.update_task(
            task_id=todo_id,
            user_id=current_user.id,
            title=todo_data.title,
            description=todo_data.description,
            due_date=todo_data.due_date,
            priority=todo_data.priority,
            tag_ids=todo_data.tag_ids,
            is_completed=todo_data.is_completed
        )
        return TodoResponse.model_validate(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Permanently delete a todo.
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Hard delete (cannot be recovered)
    - Returns 204 No Content on success
    """
    task_service = get_task_service(session)
    
    try:
        await task_service.delete_task(todo_id, current_user.id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    
    return None
