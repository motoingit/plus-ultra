"""SQLAlchemy implementation of TaskRepositoryContract."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from plus_ultra.domain.entities.task import Task
from plus_ultra.domain.repositories.task_repository import (
    TaskRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    task_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    ReminderModel,
    TaskModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyTaskRepository(
    SqlAlchemyRepositoryBase, TaskRepositoryContract
):
    """SQLAlchemy repository for tasks."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

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
        """Create and persist a new task record."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty or whitespace-only.")

        task_id = str(uuid.uuid4())
        now = _now_utc()
        google_flag = 1 if is_google_task else 0

        model = TaskModel(
            id=task_id,
            category_id=category_id,
            title=clean_title,
            description=description,
            due_date=due_date,
            status=status,
            task_label=task_label,
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=google_flag,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return task_to_domain(model)

    def get_by_id(self, task_id: str) -> Task | None:
        """Fetch task by ID."""
        model = self.session.get(TaskModel, task_id)
        return task_to_domain(model) if model else None

    def list_active(
        self,
        category_id: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        """List active non-deleted tasks with optional filters."""
        stmt = select(TaskModel).where(TaskModel.is_deleted == 0)

        if category_id is not None:
            stmt = stmt.where(TaskModel.category_id == category_id)
        if status is not None:
            stmt = stmt.where(TaskModel.status == status)

        stmt = stmt.order_by(TaskModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [task_to_domain(m) for m in models]

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
        """Update task fields; automatically bumps updated_at timestamp."""
        model = self.session.get(TaskModel, task_id)
        if model is None or model.is_deleted:
            return None

        now = _now_utc()
        if title is not None:
            clean_title = title.strip()
            if not clean_title:
                raise ValueError("Task title cannot be empty.")
            model.title = clean_title
        if category_id is not None:
            model.category_id = category_id
        if description is not None:
            model.description = description
        if due_date is not None:
            model.due_date = due_date
        if status is not None:
            model.status = status
        if task_label is not None:
            model.task_label = task_label
        if critical_level is not None:
            model.critical_level = critical_level
        if pace_level is not None:
            model.pace_level = pace_level
        if is_google_task is not None:
            model.is_google_task = 1 if is_google_task else 0

        model.updated_at = now
        self._commit_or_flush()
        return task_to_domain(model)

    def soft_delete(self, task_id: str) -> bool:
        """Soft-delete task and cascade soft-delete to its reminders."""
        model = self.session.get(TaskModel, task_id)
        if model is None or model.is_deleted:
            return False

        now = _now_utc()
        model.is_deleted = 1
        model.updated_at = now

        # Cascade soft-delete linked reminders
        self.session.execute(
            update(ReminderModel)
            .where(
                ReminderModel.task_id == task_id,
                ReminderModel.is_deleted == 0,
            )
            .values(is_deleted=1, updated_at=now)
        )
        self._commit_or_flush()
        return True
