"""Task search API endpoint."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from datetime import datetime
from typing import Optional, List

from ..core.database import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..models.todo import PriorityEnum
from ..services.search_service import get_search_service, SearchService


router = APIRouter(prefix="/api/tasks/search", tags=["Search"])


@router.get("", response_model=dict)
def search_tasks(
    q: Optional[str] = Query(None, description="Search keyword"),
    priority: Optional[PriorityEnum] = Query(None, description="Filter by priority"),
    task_status: Optional[str] = Query(None, alias="status", description="Filter by status (completed, incomplete, overdue)"),
    tags: Optional[str] = Query(None, description="Filter by tag IDs (comma-separated)"),
    due_date_from: Optional[datetime] = Query(None, description="Filter tasks due on or after this date"),
    due_date_to: Optional[datetime] = Query(None, description="Filter tasks due on or before this date"),
    sort_by: str = Query("created_at", description="Sort field (due_date, priority, created_at, title)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Search and filter tasks.
    
    - **q**: Search keyword (searches title and description)
    - **priority**: Filter by priority level (high, medium, low)
    - **status**: Filter by status (completed, incomplete, overdue)
    - **tags**: Filter by tag IDs (comma-separated)
    - **due_date_from**: Filter tasks due on or after this date
    - **due_date_to**: Filter tasks due on or before this date
    - **sort_by**: Sort field (due_date, priority, created_at, title)
    - **sort_order**: Sort order (asc, desc)
    - **page**: Page number (1-indexed)
    - **limit**: Items per page (max 100)
    
    Returns tasks matching all specified criteria (AND logic).
    """
    search_service = get_search_service(session)
    
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
    
    try:
        result = search_service.search_tasks(
            user_id=current_user.id,
            query=q,
            priority=priority,
            status=task_status,
            tag_ids=tag_ids,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        
        return {
            "tasks": result["tasks"],
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "total_pages": result["total_pages"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/suggestions", response_model=dict)
def get_search_suggestions(
    prefix: str = Query(..., min_length=1, description="Search prefix"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get search suggestions based on prefix.
    
    Returns matching task titles and tags.
    """
    search_service = get_search_service(session)
    
    try:
        suggestions = search_service.get_search_suggestions(
            user_id=current_user.id,
            prefix=prefix,
            limit=5
        )
        
        return {
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )
