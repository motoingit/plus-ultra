"""Data access operations for IdeaDoubt entities."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from plus_ultra.database.connection import transaction
from plus_ultra.models import IdeaDoubt
from plus_ultra.repositories.base import _now_utc


def _row_to_idea_doubt(row: sqlite3.Row) -> IdeaDoubt:
    """Convert an SQLite row to an IdeaDoubt model."""
    return IdeaDoubt(
        id=row["id"],
        kind=row["kind"],
        title=row["title"],
        description=row["description"],
        tech_stack_or_ref=row["tech_stack_or_ref"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class IdeaDoubtRepository:
    """Data access operations for IdeaDoubt entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_items(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[IdeaDoubt]:
        """List active ideas and doubts."""
        query = ["SELECT * FROM ideas_doubts WHERE is_deleted = 0"]
        params: list[Any] = []

        if kind and kind != "All":
            query.append("AND kind = ?")
            params.append(kind)

        if status and status != "All":
            query.append("AND status = ?")
            params.append(status)

        if search_query:
            query.append(
                "AND (title LIKE ? OR description LIKE ? OR "
                "tech_stack_or_ref LIKE ?)"
            )
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_idea_doubt(row) for row in cur.fetchall()]

    def get(self, item_id: str) -> IdeaDoubt | None:
        """Fetch item by ID."""
        cur = self.conn.execute(
            "SELECT * FROM ideas_doubts WHERE id = ? AND is_deleted = 0",
            (item_id,),
        )
        row = cur.fetchone()
        return _row_to_idea_doubt(row) if row else None

    def create(
        self,
        kind: str,
        title: str,
        description: str = "",
        tech_stack_or_ref: str = "",
        status: str = "Idea",
    ) -> IdeaDoubt:
        """Create a new idea or doubt."""
        now = _now_utc()
        item_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO ideas_doubts (
                    id, kind, title, description, tech_stack_or_ref,
                    status, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    item_id,
                    kind,
                    title,
                    description,
                    tech_stack_or_ref,
                    status,
                    now,
                    now,
                ),
            )
        return IdeaDoubt(
            id=item_id,
            kind=kind,
            title=title,
            description=description,
            tech_stack_or_ref=tech_stack_or_ref,
            status=status,
            created_at=now,
            updated_at=now,
        )

    def update_status(self, item_id: str, new_status: str) -> bool:
        """Update status of an idea or doubt."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE ideas_doubts
                SET status = ?, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (new_status, now, item_id),
            )
            return cur.rowcount > 0

    def update(
        self,
        item_id: str,
        title: str | None = None,
        kind: str | None = None,
        description: str | None = None,
        tech_stack_or_ref: str | None = None,
        status: str | None = None,
    ) -> bool:
        """Update idea/doubt fields."""
        fields: list[str] = []
        params: list[Any] = []
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if kind is not None:
            fields.append("kind = ?")
            params.append(kind)
        if description is not None:
            fields.append("description = ?")
            params.append(description)
        if tech_stack_or_ref is not None:
            fields.append("tech_stack_or_ref = ?")
            params.append(tech_stack_or_ref)
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if not fields:
            return False
        fields.append("updated_at = ?")
        params.extend([_now_utc(), item_id])
        with transaction(self.conn) as cur:
            cur.execute(
                f"UPDATE ideas_doubts SET {', '.join(fields)} "
                "WHERE id = ? AND is_deleted = 0",
                params,
            )
            return cur.rowcount > 0

    def soft_delete(self, item_id: str) -> bool:
        """Soft delete an idea or doubt."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE ideas_doubts
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, item_id),
            )
            return cur.rowcount > 0
