"""SQLAlchemy implementation of ReminderRepositoryContract."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from plus_ultra.datetime_utils import parse_flexible_datetime
from plus_ultra.domain.entities.reminder import Reminder
from plus_ultra.domain.repositories.reminder_repository import (
    ReminderRepositoryContract,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.mappers import (
    reminder_to_domain,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    ReminderFireModel,
    ReminderModel,
    TaskModel,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)


class SqlAlchemyReminderRepository(
    SqlAlchemyRepositoryBase, ReminderRepositoryContract
):
    """SQLAlchemy repository for reminders and device-local fires."""

    def __init__(self, session: Session, autocommit: bool = True) -> None:
        super().__init__(session=session, autocommit=autocommit)

    def create(self, task_id: str, remind_at: str) -> Reminder:
        """Create and schedule a reminder for an existing task."""
        rem_id = str(uuid.uuid4())
        now = _now_utc()
        model = ReminderModel(
            id=rem_id,
            task_id=task_id,
            remind_at=remind_at,
            created_at=now,
            updated_at=now,
            is_deleted=0,
        )
        self.session.add(model)
        self._commit_or_flush()
        return reminder_to_domain(model)

    def get_by_id(self, reminder_id: str) -> Reminder | None:
        """Fetch reminder by ID."""
        model = self.session.get(ReminderModel, reminder_id)
        return reminder_to_domain(model) if model else None

    def list_due(self, before_timestamp: str) -> list[Reminder]:
        """Query active reminders due at or before a cutoff timestamp."""
        stmt = (
            select(ReminderModel)
            .join(TaskModel, ReminderModel.task_id == TaskModel.id)
            .where(
                ReminderModel.is_deleted == 0,
                TaskModel.is_deleted == 0,
                ~ReminderModel.fires.any(),
            )
            .order_by(ReminderModel.remind_at.asc())
        )
        models = self.session.scalars(stmt).all()
        cutoff = parse_flexible_datetime(before_timestamp)

        due_list: list[Reminder] = []
        for m in models:
            try:
                rem_dt = parse_flexible_datetime(m.remind_at)
                if rem_dt <= cutoff:
                    due_list.append(reminder_to_domain(m))
            except Exception:
                continue
        return due_list

    def mark_fired(self, reminder_id: str, fired_at: str | None = None) -> None:
        """Record that a reminder alert has fired on this device."""
        existing = self.session.get(ReminderFireModel, reminder_id)
        if existing is None:
            now = fired_at or _now_utc()
            fire_record = ReminderFireModel(
                reminder_id=reminder_id, fired_at=now
            )
            self.session.add(fire_record)
            self._commit_or_flush()

    def is_fired(self, reminder_id: str) -> bool:
        """Check if reminder was already dispatched on this device."""
        model = self.session.get(ReminderFireModel, reminder_id)
        return model is not None

    def soft_delete(self, reminder_id: str) -> bool:
        """Soft-delete reminder."""
        model = self.session.get(ReminderModel, reminder_id)
        if model is None or model.is_deleted:
            return False

        now = _now_utc()
        model.is_deleted = 1
        model.updated_at = now
        self._commit_or_flush()
        return True
