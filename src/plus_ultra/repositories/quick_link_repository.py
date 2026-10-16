"""Data access operations for QuickLink entities."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from plus_ultra.database.connection import transaction
from plus_ultra.models import QuickLink
from plus_ultra.repositories.base import _now_utc


def _row_to_quick_link(row: sqlite3.Row) -> QuickLink:
    """Convert an SQLite row to a QuickLink model."""
    return QuickLink(
        id=row["id"],
        name=row["name"],
        target_uri=row["target_uri"],
        category=row["category"],
        click_count=row["click_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class QuickLinkRepository:
    """Data access operations for QuickLink entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_links(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[QuickLink]:
        """List active quick links."""
        query = ["SELECT * FROM quick_links WHERE is_deleted = 0"]
        params: list[Any] = []

        if category and category != "All":
            query.append("AND category = ?")
            params.append(category)

        if search_query:
            query.append("AND (name LIKE ? OR target_uri LIKE ?)")
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard])

        query.append("ORDER BY click_count DESC, created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_quick_link(row) for row in cur.fetchall()]

    def get(self, link_id: str) -> QuickLink | None:
        """Fetch quick link by ID."""
        cur = self.conn.execute(
            "SELECT * FROM quick_links WHERE id = ? AND is_deleted = 0",
            (link_id,),
        )
        row = cur.fetchone()
        return _row_to_quick_link(row) if row else None

    def create(
        self,
        name: str,
        target_uri: str,
        category: str = "Web",
    ) -> QuickLink:
        """Create a new quick link."""
        now = _now_utc()
        link_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO quick_links (
                    id, name, target_uri, category, click_count,
                    created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, 0, ?, ?, 0)
                """,
                (link_id, name, target_uri, category, now, now),
            )
        return QuickLink(
            id=link_id,
            name=name,
            target_uri=target_uri,
            category=category,
            click_count=0,
            created_at=now,
            updated_at=now,
        )

    def increment_click(self, link_id: str) -> bool:
        """Increment click count."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE quick_links
                SET click_count = click_count + 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, link_id),
            )
            return cur.rowcount > 0

    def update(
        self,
        link_id: str,
        name: str | None = None,
        target_uri: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Update quick link fields."""
        fields: list[str] = []
        params: list[Any] = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if target_uri is not None:
            fields.append("target_uri = ?")
            params.append(target_uri)
        if category is not None:
            fields.append("category = ?")
            params.append(category)
        if not fields:
            return False
        fields.append("updated_at = ?")
        params.extend([_now_utc(), link_id])
        with transaction(self.conn) as cur:
            cur.execute(
                f"UPDATE quick_links SET {', '.join(fields)} "
                "WHERE id = ? AND is_deleted = 0",
                params,
            )
            return cur.rowcount > 0

    def soft_delete(self, link_id: str) -> bool:
        """Soft delete a quick link."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE quick_links
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, link_id),
            )
            return cur.rowcount > 0
