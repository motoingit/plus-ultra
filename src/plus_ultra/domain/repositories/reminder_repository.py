"""Abstract repository contract for Reminder entities."""

from __future__ import annotations

from typing import Protocol

from plus_ultra.domain.entities.reminder import Reminder


class ReminderRepositoryContract(Protocol):
    """Abstract contract for Reminder repository operations."""

    def create(self, task_id: str, remind_at: str) -> Reminder:
        """Create and schedule a new reminder for an existing task."""
        ...

    def get_by_id(self, reminder_id: str) -> Reminder | None:
        """Fetch reminder by its unique identifier."""
        ...

    def list_due(self, before_timestamp: str) -> list[Reminder]:
        """Query active reminders due at or before a cutoff timestamp."""
        ...

    def mark_fired(self, reminder_id: str) -> None:
        """Record device-local dispatch of reminder alert."""
        ...

    def is_fired(self, reminder_id: str) -> bool:
        """Check if reminder alert was already fired."""
        ...

    def soft_delete(self, reminder_id: str) -> bool:
        """Soft-delete reminder record."""
        ...

