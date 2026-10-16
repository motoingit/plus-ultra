"""Data access operations for Category entities."""

from __future__ import annotations

import sqlite3
import uuid

from plus_ultra.database.connection import transaction
from plus_ultra.models import Category
from plus_ultra.repositories.base import _now_utc


def _row_to_category(row: sqlite3.Row) -> Category:
    """Convert an SQLite row to a Category model."""
    return Category(
        id=row["id"],
        name=row["name"],
        color=row["color"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class CategoryRepository:
    """Data access operations for Category entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, name: str, color: str = "#4a5568") -> Category:
        """Create a new category.

        Raises:
            sqlite3.IntegrityError: If active category name already exists.
        """
        cat_id = str(uuid.uuid4())
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO categories (
                    id, name, color, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, 0)
                """,
                (cat_id, name.strip(), color, now, now),
            )
        return Category(
            id=cat_id,
            name=name.strip(),
            color=color,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, category_id: str) -> Category | None:
        """Fetch category by ID, including soft-deleted ones."""
        cur = self.conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        )
        row = cur.fetchone()
        return _row_to_category(row) if row else None

    def list_active(self) -> list[Category]:
        """Return all active (non-deleted) categories ordered by name."""
        cur = self.conn.execute(
            """
            SELECT * FROM categories
            WHERE is_deleted = 0
            ORDER BY name COLLATE NOCASE ASC
            """
        )
        return [_row_to_category(row) for row in cur.fetchall()]

    def update(
        self, category_id: str, name: str, color: str
    ) -> Category | None:
        """Update category name and color; sets updated_at timestamp."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE categories
                SET name = ?, color = ?, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (name.strip(), color, now, category_id),
            )
            if cur.rowcount == 0:
                return None
        return self.get_by_id(category_id)

    def soft_delete(self, category_id: str) -> bool:
        """Soft-delete category and nullify linked tasks' category_id."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE categories
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, category_id),
            )
            if cur.rowcount == 0:
                return False

            # Cascade: set tasks.category_id to NULL in same transaction
            cur.execute(
                """
                UPDATE tasks
                SET category_id = NULL, updated_at = ?
                WHERE category_id = ? AND is_deleted = 0
                """,
                (now, category_id),
            )
        return True
