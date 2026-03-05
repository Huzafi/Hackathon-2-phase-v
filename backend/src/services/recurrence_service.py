"""Recurrence service for managing recurring tasks."""
from typing import Optional, List
from datetime import datetime, date, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from sqlmodel import Session, select
import logging

from ..models.recurrence import RecurrenceRule, RecurrencePattern
from ..models.todo import Todo
from ..models.event_log import EventType
from ..services.event_producer import get_event_producer


logger = logging.getLogger(__name__)


class RecurrenceService:
    """Service for managing recurring task generation."""
    
    def __init__(self, session: Session):
        self.session = session
        self.event_producer = get_event_producer(session)
    
    def calculate_next_occurrence(
        self,
        rule: RecurrenceRule,
        after_date: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate the next occurrence date based on recurrence rule.
        
        Args:
            rule: Recurrence rule
            after_date: Date to calculate next occurrence after (defaults to now)
        
        Returns:
            Next occurrence datetime, or None if no more occurrences
        """
        if after_date is None:
            after_date = datetime.utcnow()
        
        # Map pattern to dateutil frequency
        pattern_map = {
            RecurrencePattern.daily: DAILY,
            RecurrencePattern.weekly: WEEKLY,
            RecurrencePattern.monthly: MONTHLY,
            RecurrencePattern.yearly: YEARLY,
        }
        
        freq = pattern_map[rule.pattern]
        
        # Parse weekdays if specified
        weekday_list = None
        if rule.by_weekday:
            weekday_map = {
                'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3,
                'FR': 4, 'SA': 5, 'SU': 6
            }
            weekday_list = [weekday_map[day.strip().upper()] 
                          for day in rule.by_weekday.split(',')]
        
        # Create rrule
        rrule_obj = rrule(
            freq=freq,
            interval=rule.interval,
            dtstart=rule.start_date,
            until=rule.end_date,
            byweekday=weekday_list if weekday_list else None,
            bymonthday=rule.by_monthday,
        )
        
        # Get next occurrence after the specified date
        # If this is the first occurrence, use start_date
        after = after_date if after_date > datetime.combine(rule.start_date, datetime.min.time()) else rule.start_date
        next_occurrence = rrule_obj.after(after)
        
        return next_occurrence
    
    async def generate_next_instance(self, task: Todo) -> Optional[Todo]:
        """Generate the next instance of a recurring task.
        
        Args:
            task: The completed task with recurrence rule
        
        Returns:
            Newly created task, or None if no more occurrences
        """
        if not task.recurrence_rule:
            return None
        
        rule = task.recurrence_rule
        
        # Check if rule is still active
        if not rule.is_active():
            logger.info(f"Recurrence rule {rule.id} is no longer active")
            return None
        
        # Calculate next occurrence
        next_date = self.calculate_next_occurrence(rule, task.created_at)
        
        if not next_date:
            logger.info(f"No more occurrences for recurrence rule {rule.id}")
            return None
        
        # Handle month-end edge case
        if rule.by_monthday:
            # If original was on last day of month, keep it on last day
            if task.due_date and task.due_date.day == 31:
                # Adjust to last valid day of next month
                next_month_last_day = (next_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                next_date = next_date.replace(day=next_month_last_day.day)
        
        # Create new task as copy of original
        new_task = Todo(
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            due_date=next_date,
            priority=task.priority,
            is_completed=False,
        )
        
        self.session.add(new_task)
        self.session.flush()  # Get new task ID
        
        # Copy tags from original task
        if task.tags:
            from ..models.task_tag import TaskTag
            for task_tag in task.tags:
                new_task_tag = TaskTag(
                    task_id=new_task.id,
                    tag_id=task_tag.id
                )
                self.session.add(new_task_tag)
        
        self.session.commit()
        self.session.refresh(new_task)
        
        # Update recurrence rule's last_generated
        rule.last_generated = datetime.utcnow()
        self.session.add(rule)
        self.session.commit()
        
        # Emit event
        try:
            await self.event_producer.publish(
                event_type=EventType.RECURRENCE_GENERATED,
                payload={
                    "parent_task_id": task.id,
                    "new_task_id": new_task.id,
                    "recurrence_pattern": rule.pattern.value,
                    "next_due_date": next_date.isoformat()
                },
                user_id=task.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit recurrence.generated event: {e}")
        
        logger.info(f"Generated recurring task instance: new_task_id={new_task.id}, due_date={next_date}")
        return new_task
    
    def get_recurrence_rule(self, task_id: int) -> Optional[RecurrenceRule]:
        """Get recurrence rule for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            RecurrenceRule if exists, None otherwise
        """
        statement = select(RecurrenceRule).where(RecurrenceRule.task_id == task_id)
        return self.session.exec(statement).first()
    
    async def create_recurrence_rule(
        self,
        task_id: int,
        pattern: RecurrencePattern,
        interval: int = 1,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        by_weekday: Optional[str] = None,
        by_monthday: Optional[int] = None
    ) -> RecurrenceRule:
        """Create a recurrence rule for a task.
        
        Args:
            task_id: Task ID
            pattern: Recurrence pattern
            interval: Repeat interval
            start_date: Start date (defaults to today)
            end_date: Optional end date
            by_weekday: Weekdays for weekly pattern
            by_monthday: Day of month for monthly pattern
        
        Returns:
            Created RecurrenceRule
        """
        if start_date is None:
            start_date = date.today()
        
        # Validate: end_date must be after start_date
        if end_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        
        # Check if task already has recurrence rule
        existing = self.get_recurrence_rule(task_id)
        if existing:
            raise ValueError("Task already has a recurrence rule")
        
        rule = RecurrenceRule(
            task_id=task_id,
            pattern=pattern,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            by_weekday=by_weekday,
            by_monthday=by_monthday,
        )
        
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        
        # Emit event
        try:
            await self.event_producer.publish(
                event_type=EventType.RECURRENCE_SET,
                payload={
                    "task_id": task_id,
                    "pattern": pattern.value,
                    "interval": interval,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat() if end_date else None
                },
                user_id=rule.task.user_id if rule.task else task_id
            )
        except Exception as e:
            logger.error(f"Failed to emit recurrence.set event: {e}")
        
        logger.info(f"Created recurrence rule: task_id={task_id}, pattern={pattern.value}")
        return rule
    
    async def remove_recurrence_rule(
        self,
        task_id: int,
        delete_future_instances: bool = False
    ) -> None:
        """Remove recurrence rule from a task.
        
        Args:
            task_id: Task ID
            delete_future_instances: If True, delete future recurring instances
        """
        rule = self.get_recurrence_rule(task_id)
        if not rule:
            raise ValueError("Task has no recurrence rule")
        
        # Get user_id before deletion
        user_id = rule.task.user_id if rule.task else task_id
        
        # Delete future instances if requested
        if delete_future_instances:
            from ..models.todo import Todo
            now = datetime.utcnow()
            statement = select(Todo).where(
                Todo.user_id == user_id,
                Todo.due_date > now
            )
            # Note: In a real implementation, you'd need a way to link child tasks
            # For now, we just remove the rule
            logger.info("Future instances would be deleted (implementation pending)")
        
        # Delete the rule
        self.session.delete(rule)
        self.session.commit()
        
        # Emit event
        try:
            await self.event_producer.publish(
                event_type=EventType.RECURRENCE_REMOVED,
                payload={
                    "task_id": task_id,
                    "delete_future_instances": delete_future_instances
                },
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit recurrence.removed event: {e}")
        
        logger.info(f"Removed recurrence rule: task_id={task_id}")
    
    def get_all_active_rules(self) -> List[RecurrenceRule]:
        """Get all active recurrence rules.
        
        Returns:
            List of active RecurrenceRule objects
        """
        statement = select(RecurrenceRule).where(
            RecurrenceRule.end_date == None,  # No end date
            RecurrenceRule.is_active() == True
        )
        return list(self.session.exec(statement).all())


def get_recurrence_service(session: Session) -> RecurrenceService:
    """Get a RecurrenceService instance."""
    return RecurrenceService(session)
