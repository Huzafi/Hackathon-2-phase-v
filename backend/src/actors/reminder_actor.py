"""Dapr Actor for reminder scheduling and delivery."""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from dapr.actor import Actor, ActorProxy
from dapr.actor.runtime.context import ActorRuntimeContext


logger = logging.getLogger(__name__)


class ReminderActor(Actor):
    """Dapr Actor for managing task reminders.
    
    This actor uses Dapr's timer functionality to schedule and deliver
    reminders at specified times.
    """
    
    def __init__(self, ctx: ActorRuntimeContext, actor_id: str):
        super().__init__(ctx, actor_id)
        self._reminder_data: Optional[Dict[str, Any]] = None
        self._timer_registered = False
    
    async def on_activate(self):
        """Called when actor is activated."""
        logger.info(f"ReminderActor activated: {self.id}")
        # Load reminder data from state
        self._reminder_data = await self._state_manager.try_get_state("reminder_data")
    
    async def on_deactivate(self):
        """Called when actor is deactivated."""
        logger.info(f"ReminderActor deactivated: {self.id}")
    
    async def set_reminder(
        self,
        task_id: int,
        user_id: int,
        trigger_time: str,
        task_title: str
    ) -> None:
        """Set a reminder to be delivered at trigger_time.
        
        Args:
            task_id: Task ID
            user_id: User ID
            trigger_time: ISO 8601 datetime string
            task_title: Task title for notification
        """
        # Parse trigger time
        trigger_dt = datetime.fromisoformat(trigger_time.replace('Z', '+00:00'))
        now = datetime.utcnow()
        
        # Calculate due time (time until trigger)
        due_time = trigger_dt - now
        
        if due_time.total_seconds() <= 0:
            logger.warning(f"Trigger time is in the past: {trigger_time}")
            # Deliver immediately
            await self._deliver_reminder(task_id, user_id, task_title)
            return
        
        # Store reminder data
        self._reminder_data = {
            "task_id": task_id,
            "user_id": user_id,
            "trigger_time": trigger_time,
            "task_title": task_title,
            "created_at": now.isoformat()
        }
        await self._state_manager.set_state("reminder_data", self._reminder_data)
        await self._state_manager.save_state()
        
        # Register timer with Dapr
        # Due time: when to first fire
        # Period: empty string for one-time timer
        timer_name = f"reminder-{self.id}"
        due_time_str = self._format_timedelta(due_time)
        
        await self.register_timer(
            timer_name,
            "deliver_reminder_callback",
            [task_id, user_id, task_title],
            due_time_str,
            ""  # Empty period = one-time timer
        )
        
        self._timer_registered = True
        logger.info(f"Registered reminder timer: actor={self.id}, due_in={due_time_str}")
    
    async def deliver_reminder_callback(
        self,
        task_id: int,
        user_id: int,
        task_title: str
    ) -> None:
        """Callback method invoked by Dapr timer when reminder is due."""
        await self._deliver_reminder(task_id, user_id, task_title)
    
    async def _deliver_reminder(
        self,
        task_id: int,
        user_id: int,
        task_title: str
    ) -> None:
        """Deliver the reminder notification.
        
        This method would typically:
        1. Send in-app notification via WebSocket/SSE
        2. Send email notification (if configured)
        3. Send push notification (if mobile app)
        
        For now, we just log the delivery.
        """
        logger.info(
            f"REMINDER DELIVERED: user={user_id}, task={task_id}, "
            f"title={task_title}, time={datetime.utcnow().isoformat()}"
        )
        
        # Mark reminder as delivered in database
        # This would be done via a service call
        # For now, we just log it
        
        # Clear timer flag
        self._timer_registered = False
        
        # Optionally deactivate actor after delivery
        # await self._hint_deactivate()
    
    async def cancel_reminder(self) -> None:
        """Cancel the scheduled reminder."""
        if self._timer_registered:
            timer_name = f"reminder-{self.id}"
            await self.unregister_timer(timer_name)
            self._timer_registered = False
        
        # Clear state
        self._reminder_data = None
        await self._state_manager.delete_state("reminder_data")
        
        logger.info(f"Cancelled reminder: actor={self.id}")
    
    def _format_timedelta(self, td: timedelta) -> str:
        """Format timedelta as Dapr timer duration string.
        
        Dapr expects duration in format: "1h", "30m", "90s", etc.
        """
        total_seconds = int(td.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h{minutes}m"
            return f"{hours}h"


# Actor type name for registration
ACTOR_TYPE_NAME = "ReminderActor"
