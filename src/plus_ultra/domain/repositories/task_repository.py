"""Abstract repository contract for Task entities."""

from __future__ import annotations

from typing import Protocol

from plus_ultra.domain.entities.task import Task


class TaskRepositoryContract(Protocol):
    """Abstract contract for Task repository operations."""

    def create(
        self,
        title: str,
        category_id: str | None = None,
        description: str = "",
        due_date: str | None = None,
        status: str = "Pending",
        task_label: str = "General",
        critical_level: str = "Medium",
        pace_level: str = "Short-term",
        is_google_task: bool = False,
    ) -> Task:
        """Create and persist a new Task entity."""
        ...

    def get_by_id(self, task_id: str) -> Task | None:
        """Fetch a task by ID."""
        ...

    def list_active(
        self,
        category_id: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        """List active non-deleted tasks matching optional filter criteria."""
        ...

    def update(
        self,
        task_id: str,
        title: str | None = None,
        category_id: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        status: str | None = None,
        task_label: str | None = None,
        critical_level: str | None = None,
        pace_level: str | None = None,
        is_google_task: bool | None = None,
    ) -> Task | None:
        """Update task fields and bump updated timestamp."""
        ...

    def soft_delete(self, task_id: str) -> bool:
        """Soft-delete task and cascade soft-deletion to linked reminders."""
        ...

