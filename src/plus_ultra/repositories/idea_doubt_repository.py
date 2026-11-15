"""IdeaDoubt repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.workspace import IdeaDoubt
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyIdeaDoubtRepository as IdeaDoubtRepository,
)


def _row_to_idea_doubt(row: Any) -> IdeaDoubt:
    """Backward compatibility helper converting row/model to IdeaDoubt."""
    if hasattr(row, "id"):
        return IdeaDoubt(
            id=row.id,
            kind=row.kind,
            title=row.title,
            description=getattr(row, "description", ""),
            tech_stack_or_ref=getattr(row, "tech_stack_or_ref", ""),
            status=getattr(row, "status", "Idea"),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return IdeaDoubt(
        id=row["id"],
        kind=row["kind"],
        title=row["title"],
        description=row.get("description", ""),
        tech_stack_or_ref=row.get("tech_stack_or_ref", ""),
        status=row.get("status", "Idea"),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["IdeaDoubtRepository", "_row_to_idea_doubt"]
