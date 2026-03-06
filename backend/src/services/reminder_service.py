"""Reminder service for managing task reminders."""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlmodel import Session, select
import logging

from ..models.reminder import Reminder
from ..models.todo import Todo
from ..models.event_log import EventType
from ..services.event_producer import get_event_producer


logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing task reminders."""
    
    def __init__(self, session: Session):
        self.session = session
        self.event_producer = get_event_producer(session)
    
    async def create_reminder(
        self,
        task_id: int,
        trigger_time: datetime
    ) -> Reminder:
        """Create a new reminder for a task.
        
        Args:
            task_id: Task ID
            trigger_time: When to trigger the reminder
        
        Returns:
            Created Reminder
        
        Raises:
            ValueError: If validation fails
        """
        # Validate trigger time is not in past
        if trigger_time <= datetime.utcnow():
            raise ValueError("trigger_time must be in the future")
        
        # Validate task exists
        task = self.session.get(Todo, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Validate task is not completed
        if task.is_completed:
            raise ValueError("Cannot create reminder for completed task")
        
        # Create reminder
        reminder = Reminder(
            task_id=task_id,
            trigger_time=trigger_time,
            delivered=False
        )
        
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        
        # Emit event
        try:
            await self.event_producer.publish(
                event_type=EventType.REMINDER_SET,
                payload={
                    "reminder_id": reminder.id,
                    "task_id": task_id,
                    "trigger_time": trigger_time.isoformat()
                },
                user_id=task.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit reminder.set event: {e}")
        
        logger.info(f"Created reminder: id={reminder.id}, task_id={task_id}, trigger_time={trigger_time}")
        return reminder
    
    def get_reminder(self, reminder_id: int) -> Optional[Reminder]:
        """Get reminder by ID.
        
        Args:
            reminder_id: Reminder ID
        
        Returns:
            Reminder if found, None otherwise
        """
        return self.session.get(Reminder, reminder_id)
    
    def get_reminders_for_task(self, task_id: int) -> List[Reminder]:
        """Get all reminders for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            List of Reminder objects
        """
        statement = select(Reminder).where(Reminder.task_id == task_id)
        return list(self.session.exec(statement).all())
    
    def get_pending_reminders(self, window_minutes: int = 5) -> List[Reminder]:
        """Get reminders due within the specified time window.
        
        Args:
            window_minutes: Time window in minutes (default: 5)
        
        Returns:
            List of pending Reminder objects
        """
        now = datetime.utcnow()
        window_end = now + timedelta(minutes=window_minutes)
        
        statement = select(Reminder).where(
            Reminder.trigger_time <= window_end,
            Reminder.trigger_time >= now,
            Reminder.delivered == False
        )
        return list(self.session.exec(statement).all())
    
    async def mark_reminder_delivered(self, reminder_id: int) -> None:
        """Mark a reminder as delivered.
        
        Args:
            reminder_id: Reminder ID
        """
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder {reminder_id} not found")
        
        reminder.delivered = True
        self.session.add(reminder)
        self.session.commit()
        
        # Emit event
        try:
            task = self.session.get(Todo, reminder.task_id)
            if task:
                await self.event_producer.publish(
                    event_type=EventType.REMINDER_DELIVERED,
                    payload={
                        "reminder_id": reminder_id,
                        "task_id": reminder.task_id,
                        "delivered_at": datetime.utcnow().isoformat()
                    },
                    user_id=task.user_id
                )
        except Exception as e:
            logger.error(f"Failed to emit reminder.delivered event: {e}")
        
        logger.info(f"Marked reminder as delivered: id={reminder_id}")
    
    async def cancel_reminder(self, reminder_id: int) -> None:
        """Cancel (delete) a reminder.
        
        Args:
            reminder_id: Reminder ID
        """
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder {reminder_id} not found")
        
        task = self.session.get(Todo, reminder.task_id)
        user_id = task.user_id if task else None
        
        # Emit event before deletion
        try:
            await self.event_producer.publish(
                event_type=EventType.REMINDER_DELETED,
                payload={
                    "reminder_id": reminder_id,
                    "task_id": reminder.task_id
                },
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit reminder.deleted event: {e}")
        
        self.session.delete(reminder)
        self.session.commit()
        
        logger.info(f"Cancelled reminder: id={reminder_id}")
    
    async def cancel_reminders_for_task(self, task_id: int) -> int:
        """Cancel all reminders for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            Number of reminders cancelled
        """
        reminders = self.get_reminders_for_task(task_id)
        count = len(reminders)
        
        for reminder in reminders:
            self.session.delete(reminder)
        
        self.session.commit()
        
        logger.info(f"Cancelled {count} reminders for task: task_id={task_id}")
        return count
    
    async def update_reminder(
        self,
        reminder_id: int,
        trigger_time: Optional[datetime] = None
    ) -> Reminder:
        """Update a reminder.
        
        Args:
            reminder_id: Reminder ID
            trigger_time: New trigger time (optional)
        
        Returns:
            Updated Reminder
        
        Raises:
            ValueError: If validation fails
        """
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder {reminder_id} not found")
        
        # Update trigger time if provided
        if trigger_time is not None:
            if trigger_time <= datetime.utcnow():
                raise ValueError("trigger_time must be in the future")
            reminder.trigger_time = trigger_time
        
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        
        logger.info(f"Updated reminder: id={reminder_id}")
        return reminder


def get_reminder_service(session: Session) -> ReminderService:
    """Get a ReminderService instance."""
    return ReminderService(session)
