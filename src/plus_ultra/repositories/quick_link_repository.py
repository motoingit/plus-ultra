"""QuickLink repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.workspace import QuickLink
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyQuickLinkRepository as QuickLinkRepository,
)


def _row_to_quick_link(row: Any) -> QuickLink:
    """Backward compatibility helper converting row/model to QuickLink."""
    if hasattr(row, "id"):
        return QuickLink(
            id=row.id,
            name=row.name,
            target_uri=row.target_uri,
            category=getattr(row, "category", "Web"),
            click_count=getattr(row, "click_count", 0),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return QuickLink(
        id=row["id"],
        name=row["name"],
        target_uri=row["target_uri"],
        category=row.get("category", "Web"),
        click_count=row.get("click_count", 0),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["QuickLinkRepository", "_row_to_quick_link"]
