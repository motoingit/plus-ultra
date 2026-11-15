"""Code repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.workspace import CodeItem
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyCodeRepository as CodeRepository,
)


def _row_to_code_item(row: Any) -> CodeItem:
    """Backward compatibility helper converting row/model to CodeItem entity."""
    if hasattr(row, "id"):
        return CodeItem(
            id=row.id,
            category=row.category,
            title=row.title,
            content=getattr(row, "content", ""),
            language=getattr(row, "language", "python"),
            difficulty=getattr(row, "difficulty", "Easy"),
            is_done=getattr(row, "is_done", 0),
            url=getattr(row, "url", ""),
            notes=getattr(row, "notes", ""),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return CodeItem(
        id=row["id"],
        category=row["category"],
        title=row["title"],
        content=row.get("content", ""),
        language=row.get("language", "python"),
        difficulty=row.get("difficulty", "Easy"),
        is_done=row.get("is_done", 0),
        url=row.get("url", ""),
        notes=row.get("notes", ""),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["CodeRepository", "_row_to_code_item"]
