"""Category repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.category import Category
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyCategoryRepository as CategoryRepository,
)


def _row_to_category(row: Any) -> Category:
    """Backward compatibility helper converting row/model to Category entity."""
    if hasattr(row, "id"):
        return Category(
            id=row.id,
            name=row.name,
            color=getattr(row, "color", "#4a5568"),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return Category(
        id=row["id"],
        name=row["name"],
        color=row.get("color", "#4a5568"),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["CategoryRepository", "_row_to_category"]
