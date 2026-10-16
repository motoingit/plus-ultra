"""Data access operations for CodeItem entities."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from plus_ultra.database.connection import transaction
from plus_ultra.models import CodeItem
from plus_ultra.repositories.base import _now_utc


def _row_to_code_item(row: sqlite3.Row) -> CodeItem:
    """Convert an SQLite row to a CodeItem model."""
    return CodeItem(
        id=row["id"],
        category=row["category"],
        title=row["title"],
        content=row["content"],
        language=row["language"],
        difficulty=row["difficulty"],
        is_done=row["is_done"],
        url=row["url"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class CodeRepository:
    """Data access operations for CodeItem entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_items(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[CodeItem]:
        """Query active code items with optional category and search filters."""
        query = ["SELECT * FROM code_items WHERE is_deleted = 0"]
        params: list[Any] = []

        if category and category != "All":
            query.append("AND category = ?")
            params.append(category)

        if search_query:
            query.append("AND (title LIKE ? OR content LIKE ? OR notes LIKE ?)")
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_code_item(row) for row in cur.fetchall()]

    def get(self, item_id: str) -> CodeItem | None:
        """Fetch a single code item by ID."""
        cur = self.conn.execute(
            "SELECT * FROM code_items WHERE id = ? AND is_deleted = 0",
            (item_id,),
        )
        row = cur.fetchone()
        return _row_to_code_item(row) if row else None

    def create(
        self,
        category: str,
        title: str,
        content: str = "",
        language: str = "python",
        difficulty: str = "Easy",
        is_done: int = 0,
        url: str = "",
        notes: str = "",
    ) -> CodeItem:
        """Create a new code item."""
        now = _now_utc()
        item_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO code_items (
                    id, category, title, content, language, difficulty,
                    is_done, url, notes, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    item_id,
                    category,
                    title,
                    content,
                    language,
                    difficulty,
                    is_done,
                    url,
                    notes,
                    now,
                    now,
                ),
            )
        return CodeItem(
            id=item_id,
            category=category,
            title=title,
            content=content,
            language=language,
            difficulty=difficulty,
            is_done=is_done,
            url=url,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def toggle_done(self, item_id: str) -> bool:
        """Toggle is_done status for a DSA item."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE code_items
                SET is_done = CASE WHEN is_done = 1 THEN 0 ELSE 1 END,
                    updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, item_id),
            )
            return cur.rowcount > 0

    def update(
        self,
        item_id: str,
        category: str | None = None,
        title: str | None = None,
        content: str | None = None,
        language: str | None = None,
        difficulty: str | None = None,
        url: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update code item fields."""
        fields: list[str] = []
        params: list[Any] = []
        if category is not None:
            fields.append("category = ?")
            params.append(category)
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if content is not None:
            fields.append("content = ?")
            params.append(content)
        if language is not None:
            fields.append("language = ?")
            params.append(language)
        if difficulty is not None:
            fields.append("difficulty = ?")
            params.append(difficulty)
        if url is not None:
            fields.append("url = ?")
            params.append(url)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        if not fields:
            return False
        fields.append("updated_at = ?")
        params.extend([_now_utc(), item_id])
        with transaction(self.conn) as cur:
            cur.execute(
                f"UPDATE code_items SET {', '.join(fields)} "
                "WHERE id = ? AND is_deleted = 0",
                params,
            )
            return cur.rowcount > 0

    def soft_delete(self, item_id: str) -> bool:
        """Soft delete a code item."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE code_items
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, item_id),
            )
            return cur.rowcount > 0
