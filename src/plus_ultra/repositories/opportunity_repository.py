"""Opportunity repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from typing import Any

from plus_ultra.domain.entities.workspace import Opportunity
from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyOpportunityRepository as OpportunityRepository,
)


def _row_to_opportunity(row: Any) -> Opportunity:
    """Backward compatibility helper converting row/model to Opportunity."""
    if hasattr(row, "id"):
        return Opportunity(
            id=row.id,
            title=row.title,
            organization=row.organization,
            kind=getattr(row, "kind", "Internship"),
            url=getattr(row, "url", ""),
            deadline=getattr(row, "deadline", ""),
            status=getattr(row, "status", "Saved"),
            notes=getattr(row, "notes", ""),
            created_at=getattr(row, "created_at", ""),
            updated_at=getattr(row, "updated_at", ""),
            synced_at=getattr(row, "synced_at", None),
            is_deleted=getattr(row, "is_deleted", 0),
        )
    return Opportunity(
        id=row["id"],
        title=row["title"],
        organization=row["organization"],
        kind=row.get("kind", "Internship"),
        url=row.get("url", ""),
        deadline=row.get("deadline", ""),
        status=row.get("status", "Saved"),
        notes=row.get("notes", ""),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
        synced_at=row.get("synced_at"),
        is_deleted=row.get("is_deleted", 0),
    )


__all__ = ["OpportunityRepository", "_row_to_opportunity"]
