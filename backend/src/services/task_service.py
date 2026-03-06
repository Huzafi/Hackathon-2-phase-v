"""Task service for business logic and validation."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import Session, select
from sqlalchemy import func, case
from ..models.todo import Todo, PriorityEnum
from ..models.tag import Tag
from ..models.task_tag import TaskTag
from ..models.event_log import EventType
from ..services.event_producer import get_event_producer
import logging


logger = logging.getLogger(__name__)


class TaskService:
    """Service layer for task business logic."""
    
    def __init__(self, session: Session):
        self.session = session
        self.event_producer = get_event_producer(session)
    
    async def create_task(
        self,
        title: str,
        user_id: int,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: PriorityEnum = PriorityEnum.medium,
        tag_ids: Optional[List[int]] = None
    ) -> Todo:
        """Create a new task with validation.
        
        Args:
            title: Task title (1-200 chars)
            user_id: Owner user ID
            description: Optional description (0-1000 chars)
            due_date: Optional due date
            priority: Priority level (default: medium)
            tag_ids: Optional list of tag IDs
        
        Returns:
            Created Todo instance
        
        Raises:
            ValueError: If validation fails
        """
        # Validate title
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        if len(title.strip()) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        
        # Validate description
        if description and len(description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        
        # Validate due date (cannot be in past)
        if due_date and due_date < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        
        # Validate tags if provided
        if tag_ids:
            self._validate_tags(tag_ids, user_id)
        
        # Create task
        task = Todo(
            title=title.strip(),
            description=description,
            user_id=user_id,
            due_date=due_date,
            priority=priority
        )
        
        self.session.add(task)
        self.session.flush()  # Get task ID
        
        # Associate tags if provided
        if tag_ids:
            for tag_id in tag_ids:
                task_tag = TaskTag(task_id=task.id, tag_id=tag_id)
                self.session.add(task_tag)
        
        self.session.commit()
        self.session.refresh(task)
        
        # Load tags for response
        self.session.refresh(task, ["tags"])
        
        # Emit event
        await self._emit_task_created_event(task)
        
        logger.info(f"Task created: id={task.id}, user_id={user_id}")
        return task
    
    async def update_task(
        self,
        task_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: Optional[PriorityEnum] = None,
        tag_ids: Optional[List[int]] = None,
        is_completed: Optional[bool] = None
    ) -> Todo:
        """Update an existing task.
        
        Args:
            task_id: Task ID to update
            user_id: Owner user ID (for ownership check)
            title: New title (optional)
            description: New description (optional)
            due_date: New due date (optional)
            priority: New priority (optional)
            tag_ids: New tag IDs (replaces existing, optional)
            is_completed: Completion status (optional)
        
        Returns:
            Updated Todo instance
        
        Raises:
            ValueError: If validation fails
            HTTPException: If task not found or wrong owner
        """
        task = self._get_task_or_raise(task_id, user_id)
        
        # Update fields if provided
        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty")
            if len(title.strip()) > 200:
                raise ValueError("Title cannot exceed 200 characters")
            task.title = title.strip()
        
        if description is not None:
            if len(description) > 1000:
                raise ValueError("Description cannot exceed 1000 characters")
            task.description = description
        
        if due_date is not None:
            if due_date < datetime.utcnow():
                raise ValueError("Due date cannot be in the past")
            task.due_date = due_date
        
        if priority is not None:
            task.priority = priority
        
        if is_completed is not None:
            task.is_completed = is_completed
        
        # Update tags if provided (replace existing)
        if tag_ids is not None:
            self._update_task_tags(task, tag_ids, user_id)
        
        task.updated_at = datetime.utcnow()
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        # Load tags for response
        self.session.refresh(task, ["tags"])
        
        # Emit event
        await self._emit_task_updated_event(task)
        
        logger.info(f"Task updated: id={task_id}, user_id={user_id}")
        return task
    
    def get_task(self, task_id: int, user_id: int) -> Todo:
        """Get a task by ID with ownership check.
        
        Args:
            task_id: Task ID
            user_id: Owner user ID
        
        Returns:
            Todo instance
        
        Raises:
            HTTPException: If not found or wrong owner
        """
        task = self._get_task_or_raise(task_id, user_id)
        self.session.refresh(task, ["tags"])
        return task
    
    def list_tasks(
        self,
        user_id: int,
        priority: Optional[PriorityEnum] = None,
        status: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List tasks with filters, search, and pagination.
        
        Args:
            user_id: Owner user ID
            priority: Filter by priority
            status: Filter by status (completed, incomplete, overdue)
            tag_ids: Filter by tag IDs
            due_date_from: Filter tasks due on or after this date
            due_date_to: Filter tasks due on or before this date
            search_query: Search keyword in title/description
            sort_by: Sort field (due_date, priority, created_at, title)
            sort_order: Sort order (asc, desc)
            page: Page number
            limit: Items per page
        
        Returns:
            Dict with tasks list and pagination info
        """
        # Build query
        statement = select(Todo).where(Todo.user_id == user_id)
        
        # Apply filters
        if priority:
            statement = statement.where(Todo.priority == priority)
        
        if status == "completed":
            statement = statement.where(Todo.is_completed == True)
        elif status == "incomplete":
            statement = statement.where(Todo.is_completed == False)
        elif status == "overdue":
            statement = statement.where(
                (Todo.due_date < datetime.utcnow()) & (Todo.is_completed == False)
            )
        
        if tag_ids:
            statement = statement.join(Todo.tags).where(Tag.id.in_(tag_ids))
        
        if due_date_from:
            statement = statement.where(Todo.due_date >= due_date_from)
        if due_date_to:
            statement = statement.where(Todo.due_date <= due_date_to)
        
        # Apply search
        if search_query:
            # Full-text search would be implemented here
            # For now, simple LIKE search
            statement = statement.where(
                (Todo.title.ilike(f"%{search_query}%")) |
                (Todo.description.ilike(f"%{search_query}%"))
            )
        
        # Apply sorting
        if sort_by == "due_date":
            if sort_order == "asc":
                statement = statement.order_by(Todo.due_date.asc())
            else:
                statement = statement.order_by(Todo.due_date.desc())
        elif sort_by == "priority":
            # Custom ordering: high=1, medium=2, low=3
            if sort_order == "asc":
                statement = statement.order_by(
                    case(
                        (Todo.priority == PriorityEnum.high, 1),
                        (Todo.priority == PriorityEnum.medium, 2),
                        (Todo.priority == PriorityEnum.low, 3),
                    ).asc()
                )
            else:
                statement = statement.order_by(
                    case(
                        (Todo.priority == PriorityEnum.high, 1),
                        (Todo.priority == PriorityEnum.medium, 2),
                        (Todo.priority == PriorityEnum.low, 3),
                    ).desc()
                )
        elif sort_by == "title":
            if sort_order == "asc":
                statement = statement.order_by(Todo.title.asc())
            else:
                statement = statement.order_by(Todo.title.desc())
        else:  # created_at
            if sort_order == "asc":
                statement = statement.order_by(Todo.created_at.asc())
            else:
                statement = statement.order_by(Todo.created_at.desc())
        
        # Get total count
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.session.exec(count_statement).one()
        
        # Apply pagination
        offset = (page - 1) * limit
        statement = statement.offset(offset).limit(limit)
        
        # Execute query
        tasks = self.session.exec(statement).all()
        
        # Load tags for each task
        for task in tasks:
            self.session.refresh(task, ["tags"])
        
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    async def complete_task(self, task_id: int, user_id: int) -> Todo:
        """Mark a task as complete and generate next recurring instance if applicable.
        
        Args:
            task_id: Task ID
            user_id: Owner user ID
        
        Returns:
            Updated Todo instance
        
        Raises:
            HTTPException: If not found or wrong owner
        """
        task = self._get_task_or_raise(task_id, user_id)
        task.is_completed = True
        task.updated_at = datetime.utcnow()
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        # Check if task has recurrence rule and generate next instance
        if task.recurrence_rule:
            try:
                from ..services.recurrence_service import get_recurrence_service
                recurrence_service = get_recurrence_service(self.session)
                recurrence_service.generate_next_instance(task)
            except Exception as e:
                logger.error(f"Failed to generate recurring task instance: {e}")
                # Don't fail the completion, just log the error
        
        # Emit event
        await self._emit_task_completed_event(task)

        logger.info(f"Task completed: id={task_id}, user_id={user_id}")
        return task

    async def delete_task(self, task_id: int, user_id: int) -> None:
        """Delete a task.
        
        Args:
            task_id: Task ID
            user_id: Owner user ID

        Raises:
            HTTPException: If not found or wrong owner
        """
        task = self._get_task_or_raise(task_id, user_id)

        self.session.delete(task)
        self.session.commit()

        # Emit event
        await self._emit_task_deleted_event(task)

        logger.info(f"Task deleted: id={task_id}, user_id={user_id}")
    
    def is_task_overdue(self, task: Todo) -> bool:
        """Check if a task is overdue."""
        return (
            task.due_date is not None and
            task.due_date < datetime.utcnow() and
            not task.is_completed
        )
    
    def is_task_due_soon(self, task: Todo, hours: int = 24) -> bool:
        """Check if a task is due within specified hours."""
        if not task.due_date or task.is_completed:
            return False
        return task.due_date <= datetime.utcnow() + timedelta(hours=hours)
    
    def get_priority_color(self, priority: PriorityEnum) -> str:
        """Get color hex code for priority level."""
        colors = {
            PriorityEnum.high: "#EF4444",  # Red
            PriorityEnum.medium: "#F59E0B",  # Amber
            PriorityEnum.low: "#10B981"  # Green
        }
        return colors.get(priority, "#3B82F6")
    
    def _validate_tags(self, tag_ids: List[int], user_id: int) -> None:
        """Validate that all tag IDs exist and belong to the user."""
        statement = select(Tag.id).where(
            (Tag.id.in_(tag_ids)) & (Tag.user_id == user_id)
        )
        valid_tag_ids = set(self.session.exec(statement).all())
        
        invalid_ids = set(tag_ids) - valid_tag_ids
        if invalid_ids:
            raise ValueError(f"Invalid tag IDs: {invalid_ids}")
    
    def _update_task_tags(self, task: Todo, tag_ids: List[int], user_id: int) -> None:
        """Update task tags (replace existing)."""
        # Validate tags
        self._validate_tags(tag_ids, user_id)
        
        # Remove existing associations
        statement = select(TaskTag).where(TaskTag.task_id == task.id)
        existing_tags = self.session.exec(statement).all()
        for task_tag in existing_tags:
            self.session.delete(task_tag)
        
        # Add new associations
        for tag_id in tag_ids:
            task_tag = TaskTag(task_id=task.id, tag_id=tag_id)
            self.session.add(task_tag)
    
    def _get_task_or_raise(self, task_id: int, user_id: int) -> Todo:
        """Get task by ID with ownership check."""
        from fastapi import HTTPException, status
        
        statement = select(Todo).where(Todo.id == task_id)
        task = self.session.exec(statement).first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this task"
            )
        
        return task
    
    async def _emit_task_created_event(self, task: Todo) -> None:
        """Emit task.created event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TASK_CREATED,
                payload={
                    "task_id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority.value
                },
                user_id=task.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit task.created event: {e}")
    
    async def _emit_task_updated_event(self, task: Todo) -> None:
        """Emit task.updated event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TASK_UPDATED,
                payload={
                    "task_id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority.value
                },
                user_id=task.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit task.updated event: {e}")
    
    async def _emit_task_deleted_event(self, task: Todo) -> None:
        """Emit task.deleted event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TASK_DELETED,
                payload={
                    "task_id": task.id,
                    "title": task.title
                },
                user_id=task.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit task.deleted event: {e}")

    async def _emit_task_completed_event(self, task: Todo) -> None:
        """Emit task.completed event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TASK_COMPLETED,
                payload={
                    "task_id": task.id,
                    "title": task.title,
                    "completed_at": datetime.utcnow().isoformat()
                },
                user_id=task.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit task.completed event: {e}")


def get_task_service(session: Session) -> TaskService:
    """Get a TaskService instance."""
    return TaskService(session)
