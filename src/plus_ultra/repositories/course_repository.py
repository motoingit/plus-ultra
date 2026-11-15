"""Course repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.workspace import Course
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyCourseRepository as CourseRepository,
)


def _row_to_course(row: Any) -> Course:
    """Backward compatibility helper converting row/model to Course entity."""
    if hasattr(row, "id"):
        return Course(
            id=row.id,
            title=row.title,
            platform=getattr(row, "platform", "Coursera"),
            instructor=getattr(row, "instructor", ""),
            total_modules=getattr(row, "total_modules", 10),
            completed_modules=getattr(row, "completed_modules", 0),
            url=getattr(row, "url", ""),
            notes=getattr(row, "notes", ""),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return Course(
        id=row["id"],
        title=row["title"],
        platform=row.get("platform", "Coursera"),
        instructor=row.get("instructor", ""),
        total_modules=row.get("total_modules", 10),
        completed_modules=row.get("completed_modules", 0),
        url=row.get("url", ""),
        notes=row.get("notes", ""),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["CourseRepository", "_row_to_course"]
