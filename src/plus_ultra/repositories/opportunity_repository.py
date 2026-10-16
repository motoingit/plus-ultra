"""Data access operations for Opportunity entities."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from plus_ultra.database.connection import transaction
from plus_ultra.models import Opportunity
from plus_ultra.repositories.base import _now_utc


def _row_to_opportunity(row: sqlite3.Row) -> Opportunity:
    """Convert an SQLite row to an Opportunity model."""
    return Opportunity(
        id=row["id"],
        title=row["title"],
        organization=row["organization"],
        kind=row["kind"],
        url=row["url"],
        deadline=row["deadline"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class OpportunityRepository:
    """Data access operations for Opportunity entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_opportunities(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[Opportunity]:
        """List active opportunities with filters."""
        query = ["SELECT * FROM opportunities WHERE is_deleted = 0"]
        params: list[Any] = []

        if kind and kind != "All":
            query.append("AND kind = ?")
            params.append(kind)

        if status and status != "All":
            query.append("AND status = ?")
            params.append(status)

        if search_query:
            query.append(
                "AND (title LIKE ? OR organization LIKE ? OR notes LIKE ?)"
            )
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_opportunity(row) for row in cur.fetchall()]

    def get(self, opp_id: str) -> Opportunity | None:
        """Fetch opportunity by ID."""
        cur = self.conn.execute(
            "SELECT * FROM opportunities WHERE id = ? AND is_deleted = 0",
            (opp_id,),
        )
        row = cur.fetchone()
        return _row_to_opportunity(row) if row else None

    def create(
        self,
        title: str,
        organization: str,
        kind: str = "Internship",
        url: str = "",
        deadline: str = "",
        status: str = "Saved",
        notes: str = "",
    ) -> Opportunity:
        """Create a new opportunity."""
        now = _now_utc()
        opp_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO opportunities (
                    id, title, organization, kind, url, deadline,
                    status, notes, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    opp_id,
                    title,
                    organization,
                    kind,
                    url,
                    deadline,
                    status,
                    notes,
                    now,
                    now,
                ),
            )
        return Opportunity(
            id=opp_id,
            title=title,
            organization=organization,
            kind=kind,
            url=url,
            deadline=deadline,
            status=status,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def update_status(self, opp_id: str, new_status: str) -> bool:
        """Update opportunity status."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE opportunities
                SET status = ?, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (new_status, now, opp_id),
            )
            return cur.rowcount > 0

    def update(
        self,
        opp_id: str,
        title: str | None = None,
        organization: str | None = None,
        kind: str | None = None,
        url: str | None = None,
        deadline: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update opportunity fields."""
        fields: list[str] = []
        params: list[Any] = []
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if organization is not None:
            fields.append("organization = ?")
            params.append(organization)
        if kind is not None:
            fields.append("kind = ?")
            params.append(kind)
        if url is not None:
            fields.append("url = ?")
            params.append(url)
        if deadline is not None:
            fields.append("deadline = ?")
            params.append(deadline)
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        if not fields:
            return False
        fields.append("updated_at = ?")
        params.extend([_now_utc(), opp_id])
        with transaction(self.conn) as cur:
            cur.execute(
                f"UPDATE opportunities SET {', '.join(fields)} "
                "WHERE id = ? AND is_deleted = 0",
                params,
            )
            return cur.rowcount > 0

    def soft_delete(self, opp_id: str) -> bool:
        """Soft delete an opportunity."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE opportunities
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, opp_id),
            )
            return cur.rowcount > 0
