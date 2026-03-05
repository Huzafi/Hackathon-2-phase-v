"""Reminder API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from datetime import datetime
from typing import List

from ..core.database import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..models.todo import Todo
from ..models.reminder import Reminder
from ..schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderListResponse,
)
from ..services.reminder_service import get_reminder_service, ReminderService


router = APIRouter(prefix="/api/reminders", tags=["Reminders"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new reminder for a task.
    
    - Requires authentication
    - Verifies task ownership (403 if not owned by user)
    - Returns 400 if trigger_time is in the past
    - Returns 400 if task is completed
    """
    reminder_service = get_reminder_service(session)
    
    # Verify task exists and belongs to user
    task = session.get(Todo, reminder_data.task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {reminder_data.task_id} not found"
        )
    
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create reminders for this task"
        )
    
    try:
        reminder = await reminder_service.create_reminder(
            task_id=reminder_data.task_id,
            trigger_time=reminder_data.trigger_time
        )
        
        return ReminderResponse(
            id=reminder.id,
            task_id=reminder.task_id,
            trigger_time=reminder.trigger_time,
            delivered=reminder.delivered,
            created_at=reminder.created_at,
            task_title=task.title
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=ReminderListResponse)
def list_reminders(
    task_id: int = Query(None, description="Filter by task ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List reminders for the authenticated user.
    
    - Requires authentication
    - Can filter by task_id
    - Returns reminders with task information
    """
    reminder_service = get_reminder_service(session)
    
    if task_id:
        # Verify task belongs to user
        task = session.get(Todo, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        if task.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access reminders for this task"
            )
        
        reminders = reminder_service.get_reminders_for_task(task_id)
    else:
        # Get all reminders for user (via their tasks)
        # This would need a more complex query in a real implementation
        reminders = []
    
    # Calculate pagination
    total = len(reminders)
    offset = (page - 1) * limit
    paginated_reminders = reminders[offset:offset + limit]
    
    return ReminderListResponse(
        reminders=[
            ReminderResponse(
                id=r.id,
                task_id=r.task_id,
                trigger_time=r.trigger_time,
                delivered=r.delivered,
                created_at=r.created_at,
                task_title=session.get(Todo, r.task_id).title if session.get(Todo, r.task_id) else None
            )
            for r in paginated_reminders
        ],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific reminder by ID.
    
    - Requires authentication
    - Verifies reminder ownership (403 if not owned by user)
    - Returns 404 if reminder doesn't exist
    """
    reminder_service = get_reminder_service(session)
    
    reminder = reminder_service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    # Verify task belongs to user
    task = session.get(Todo, reminder.task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this reminder"
        )
    
    return ReminderResponse(
        id=reminder.id,
        task_id=reminder.task_id,
        trigger_time=reminder.trigger_time,
        delivered=reminder.delivered,
        created_at=reminder.created_at,
        task_title=task.title
    )


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Cancel (delete) a reminder.
    
    - Requires authentication
    - Verifies reminder ownership (403 if not owned by user)
    - Returns 404 if reminder doesn't exist
    """
    reminder_service = get_reminder_service(session)
    
    reminder = reminder_service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    # Verify task belongs to user
    task = session.get(Todo, reminder.task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this reminder"
        )
    
    await reminder_service.cancel_reminder(reminder_id)
    return None


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update a reminder.
    
    - Requires authentication
    - Verifies reminder ownership (403 if not owned by user)
    - Returns 400 if new trigger_time is in the past
    """
    reminder_service = get_reminder_service(session)
    
    reminder = reminder_service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder with id {reminder_id} not found"
        )
    
    # Verify task belongs to user
    task = session.get(Todo, reminder.task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this reminder"
        )
    
    try:
        updated_reminder = await reminder_service.update_reminder(
            reminder_id=reminder_id,
            trigger_time=reminder_data.trigger_time
        )
        
        return ReminderResponse(
            id=updated_reminder.id,
            task_id=updated_reminder.task_id,
            trigger_time=updated_reminder.trigger_time,
            delivered=updated_reminder.delivered,
            created_at=updated_reminder.created_at,
            task_title=task.title
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
