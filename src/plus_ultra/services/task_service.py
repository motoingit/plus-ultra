"""Business operations for task management."""

from __future__ import annotations

import logging

from plus_ultra.models import Task
from plus_ultra.repositories import CategoryRepository, TaskRepository

logger = logging.getLogger(__name__)

VALID_STATUSES = ("Pending", "In Progress", "Completed", "Overdue")
VALID_CRITICAL_LEVELS = ("High", "Medium", "Low")
VALID_PACE_LEVELS = ("Long-term", "Short-term")


class TaskService:
    """Business operations for task management."""

    def __init__(
        self,
        task_repo: TaskRepository,
        category_repo: CategoryRepository,
    ) -> None:
        self.task_repo = task_repo
        self.category_repo = category_repo

    def create_task(
        self,
        title: str,
        category_id: str | None = None,
        description: str = "",
        due_date: str | None = None,
        status: str = "Pending",
        task_label: str = "College",
        critical_level: str = "Medium",
        pace_level: str = "Short-term",
        is_google_task: bool = False,
    ) -> Task:
        """Validate input and create a new active task."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty or whitespace-only.")

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {status}. Expected {VALID_STATUSES}"
            )

        if critical_level not in VALID_CRITICAL_LEVELS:
            raise ValueError(
                f"Invalid critical level: {critical_level}. Expected "
                f"{VALID_CRITICAL_LEVELS}"
            )

        if pace_level not in VALID_PACE_LEVELS:
            raise ValueError(
                f"Invalid pace level: {pace_level}. Expected "
                f"{VALID_PACE_LEVELS}"
            )

        # Verify category exists if provided
        if category_id is not None:
            cat = self.category_repo.get_by_id(category_id)
            if not cat or cat.is_deleted:
                raise ValueError(f"Category '{category_id}' does not exist.")

        return self.task_repo.create(
            title=clean_title,
            category_id=category_id,
            description=description.strip(),
            due_date=due_date,
            status=status,
            task_label=task_label.strip(),
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=is_google_task,
        )

    def get_task(self, task_id: str) -> Task | None:
        """Fetch task by ID if not deleted."""
        task = self.task_repo.get_by_id(task_id)
        return task if task and not task.is_deleted else None

    def update_task(
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
        """Validate updates and persist changes."""
        clean_title = title.strip() if title is not None else None
        if clean_title is not None and not clean_title:
            raise ValueError("Task title cannot be empty.")

        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}.")

        if (
            critical_level is not None
            and critical_level not in VALID_CRITICAL_LEVELS
        ):
            raise ValueError(f"Invalid critical level: {critical_level}.")

        if pace_level is not None and pace_level not in VALID_PACE_LEVELS:
            raise ValueError(f"Invalid pace level: {pace_level}.")

        if category_id is not None:
            cat = self.category_repo.get_by_id(category_id)
            if not cat or cat.is_deleted:
                raise ValueError(f"Category '{category_id}' does not exist.")

        return self.task_repo.update(
            task_id=task_id,
            title=clean_title,
            category_id=category_id,
            description=description.strip() if description else None,
            due_date=due_date,
            status=status,
            task_label=task_label.strip() if task_label else None,
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=is_google_task,
        )

    def toggle_status(self, task_id: str) -> Task | None:
        """Toggle task status between Pending and Completed."""
        task = self.get_task(task_id)
        if not task:
            return None

        new_status = "Pending" if task.status == "Completed" else "Completed"
        return self.update_task(task_id, status=new_status)

    def soft_delete_task(self, task_id: str) -> bool:
        """Soft delete a task and cascade to its reminders."""
        return self.task_repo.soft_delete(task_id)

    def list_tasks(
        self,
        category_id: str | None = None,
        status: str | None = None,
        critical_level: str | None = None,
        search_query: str | None = None,
    ) -> list[Task]:
        """List active tasks with filters and search query."""
        tasks = self.task_repo.list_active(
            category_id=category_id, status=status
        )

        if critical_level:
            tasks = [t for t in tasks if t.critical_level == critical_level]

        if search_query:
            query = search_query.strip().lower()
            tasks = [
                t
                for t in tasks
                if query in t.title.lower() or query in t.description.lower()
            ]

        return tasks
