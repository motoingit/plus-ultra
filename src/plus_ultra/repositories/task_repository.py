"""Task repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.task import Task
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyTaskRepository as TaskRepository,
)


def _row_to_task(row: Any) -> Task:
    """Backward compatibility helper converting row/model to Task entity."""
    if hasattr(row, "id"):
        return Task(
            id=row.id,
            title=row.title,
            category_id=getattr(row, "category_id", None),
            description=getattr(row, "description", ""),
            due_date=getattr(row, "due_date", None),
            status=getattr(row, "status", "Pending"),
            task_label=getattr(row, "task_label", "College"),
            critical_level=getattr(row, "critical_level", "Medium"),
            pace_level=getattr(row, "pace_level", "Short-term"),
            is_google_task=bool(getattr(row, "is_google_task", False)),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return Task(
        id=row["id"],
        title=row["title"],
        category_id=row.get("category_id"),
        description=row.get("description", ""),
        due_date=row.get("due_date"),
        status=row.get("status", "Pending"),
        task_label=row.get("task_label", "College"),
        critical_level=row.get("critical_level", "Medium"),
        pace_level=row.get("pace_level", "Short-term"),
        is_google_task=bool(row.get("is_google_task", 0)),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["TaskRepository", "_row_to_task"]
