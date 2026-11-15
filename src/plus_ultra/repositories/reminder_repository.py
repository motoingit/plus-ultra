"""Reminder repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.reminder import Reminder
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyReminderRepository as ReminderRepository,
)


def _row_to_reminder(row: Any) -> Reminder:
    """Backward compatibility helper converting row/model to Reminder entity."""
    if hasattr(row, "id"):
        return Reminder(
            id=row.id,
            task_id=row.task_id,
            remind_at=row.remind_at,
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return Reminder(
        id=row["id"],
        task_id=row["task_id"],
        remind_at=row["remind_at"],
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["ReminderRepository", "_row_to_reminder"]
