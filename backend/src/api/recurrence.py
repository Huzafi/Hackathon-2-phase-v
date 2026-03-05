"""Recurrence rule API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import date
from typing import Optional

from ..core.database import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..models.todo import Todo
from ..schemas.recurrence import (
    RecurrenceCreate,
    RecurrenceUpdate,
    RecurrenceResponse,
)
from ..services.recurrence_service import get_recurrence_service, RecurrenceService


router = APIRouter(prefix="/api/tasks", tags=["Recurrence"])


@router.post(
    "/{task_id}/recurrence",
    response_model=RecurrenceResponse,
    status_code=status.HTTP_201_CREATED
)
async def set_task_recurrence(
    task_id: int,
    recurrence_data: RecurrenceCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Set a recurrence rule for a task.
    
    - Requires authentication
    - Verifies task ownership (403 if not owned by user)
    - Returns 404 if task doesn't exist
    - Returns 400 if task already has recurrence rule
    """
    recurrence_service = get_recurrence_service(session)
    
    # Verify task exists and belongs to user
    task = session.get(Todo, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this task"
        )
    
    try:
        rule = await recurrence_service.create_recurrence_rule(
            task_id=task_id,
            pattern=recurrence_data.pattern,
            interval=recurrence_data.interval,
            start_date=recurrence_data.start_date,
            end_date=recurrence_data.end_date,
            by_weekday=recurrence_data.by_weekday,
            by_monthday=recurrence_data.by_monthday
        )
        
        return RecurrenceResponse(
            id=rule.id,
            task_id=rule.task_id,
            pattern=rule.pattern,
            interval=rule.interval,
            start_date=rule.start_date,
            end_date=rule.end_date,
            by_weekday=rule.by_weekday,
            by_monthday=rule.by_monthday,
            last_generated=rule.last_generated,
            created_at=rule.created_at,
            is_active=rule.is_active()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{task_id}/recurrence", response_model=RecurrenceResponse)
def get_task_recurrence(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get recurrence rule for a task.
    
    - Requires authentication
    - Returns 404 if task or recurrence rule doesn't exist
    """
    recurrence_service = get_recurrence_service(session)
    
    # Verify task exists and belongs to user
    task = session.get(Todo, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this task"
        )
    
    rule = recurrence_service.get_recurrence_rule(task_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recurrence rule found for task {task_id}"
        )
    
    return RecurrenceResponse(
        id=rule.id,
        task_id=rule.task_id,
        pattern=rule.pattern,
        interval=rule.interval,
        start_date=rule.start_date,
        end_date=rule.end_date,
        by_weekday=rule.by_weekday,
        by_monthday=rule.by_monthday,
        last_generated=rule.last_generated,
        created_at=rule.created_at,
        is_active=rule.is_active()
    )


@router.delete("/{task_id}/recurrence", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_recurrence(
    task_id: int,
    delete_future_instances: bool = False,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Remove recurrence rule from a task.
    
    - Requires authentication
    - Returns 404 if task or recurrence rule doesn't exist
    - delete_future_instances: If true, delete future recurring instances
    """
    recurrence_service = get_recurrence_service(session)
    
    # Verify task exists and belongs to user
    task = session.get(Todo, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this task"
        )
    
    try:
        await recurrence_service.remove_recurrence_rule(
            task_id=task_id,
            delete_future_instances=delete_future_instances
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return None
