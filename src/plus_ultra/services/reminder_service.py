"""Business operations for reminder scheduling and due evaluation."""

from __future__ import annotations

import logging

from plus_ultra.models import Reminder, Task
from plus_ultra.repositories import ReminderRepository, TaskRepository

logger = logging.getLogger(__name__)


class ReminderService:
    """Business operations for reminder scheduling and due evaluation."""

    def __init__(
        self,
        reminder_repo: ReminderRepository,
        task_repo: TaskRepository,
    ) -> None:
        self.reminder_repo = reminder_repo
        self.task_repo = task_repo

    def create_reminder(self, task_id: str, remind_at: str) -> Reminder:
        """Create and schedule a reminder for an active task."""
        clean_task_id = task_id.strip()
        task = self.task_repo.get_by_id(clean_task_id)
        if not task or task.is_deleted:
            raise ValueError(f"Task '{task_id}' does not exist or is deleted.")

        clean_remind_at = remind_at.strip()
        if not clean_remind_at:
            raise ValueError("remind_at timestamp cannot be empty.")

        rem = self.reminder_repo.create(clean_task_id, clean_remind_at)
        logger.info(
            "Reminder created: [id=%s, task_id=%s, remind_at=%s]",
            rem.id,
            clean_task_id,
            clean_remind_at,
        )
        return rem

    def get_due_reminders(
        self, before_timestamp: str
    ) -> list[tuple[Reminder, Task]]:
        """Query active due reminders and pair with active tasks.

        Excludes reminders where the linked task is deleted or the reminder
        has already been dispatched in reminder_fires.
        """
        reminders = self.reminder_repo.list_due(before_timestamp)
        result: list[tuple[Reminder, Task]] = []
        for rem in reminders:
            task = self.task_repo.get_by_id(rem.task_id)
            if task and not task.is_deleted:
                result.append((rem, task))
        return result

    def mark_fired(self, reminder_id: str) -> None:
        """Record reminder dispatch in reminder_fires table."""
        self.reminder_repo.mark_fired(reminder_id)
        logger.info("Reminder marked as fired: [id=%s]", reminder_id)

    def is_fired(self, reminder_id: str) -> bool:
        """Check if reminder was already dispatched on this device."""
        return self.reminder_repo.is_fired(reminder_id)

    def soft_delete_reminder(self, reminder_id: str) -> bool:
        """Soft delete a reminder."""
        deleted = self.reminder_repo.soft_delete(reminder_id)
        logger.info(
            "Reminder deleted: [id=%s, success=%s]", reminder_id, deleted
        )
        return deleted
