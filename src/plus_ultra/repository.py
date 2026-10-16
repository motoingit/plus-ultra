"""Data access repositories for PLUS-ULTRA.

Applies DBMS concepts:
- Parameterized SQL: Defense against SQL injection across all operations.
- Cascading Soft Deletes: Atomic multi-table updates within single transactions.
- Query Optimization: Indexed filtering for active tasks and due reminders.
- Machine State Separation: Isolated AppState repository for runtime state.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from plus_ultra.db import transaction
from plus_ultra.models import Category, Reminder, Task


def _now_utc() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


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


def _row_to_task(row: sqlite3.Row) -> Task:
    """Convert an SQLite row to a Task model."""
    return Task(
        id=row["id"],
        category_id=row["category_id"],
        title=row["title"],
        description=row["description"],
        due_date=row["due_date"],
        status=row["status"],
        task_label=row["task_label"],
        critical_level=row["critical_level"],
        pace_level=row["pace_level"],
        is_google_task=bool(row["is_google_task"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


def _row_to_reminder(row: sqlite3.Row) -> Reminder:
    """Convert an SQLite row to a Reminder model."""
    return Reminder(
        id=row["id"],
        task_id=row["task_id"],
        remind_at=row["remind_at"],
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


class TaskRepository:
    """Data access operations for Task entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(
        self,
        title: str,
        category_id: str | None = None,
        description: str = "",
        due_date: str | None = None,
        status: str = "Pending",
        task_label: str = "College",
        critical_level: str = "Medium",
        pace_level: str = "Short-term",
        is_google_task: bool = False,
    ) -> Task:
        """Create and persist a new task record."""
        clean_title = title.strip()
        task_id = str(uuid.uuid4())
        now = _now_utc()
        google_flag = 1 if is_google_task else 0

        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, category_id, title, description, due_date, status,
                    task_label, critical_level, pace_level, is_google_task,
                    created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    task_id,
                    category_id,
                    clean_title,
                    description,
                    due_date,
                    status,
                    task_label,
                    critical_level,
                    pace_level,
                    google_flag,
                    now,
                    now,
                ),
            )

        return Task(
            id=task_id,
            category_id=category_id,
            title=clean_title,
            description=description,
            due_date=due_date,
            status=status,
            task_label=task_label,
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=is_google_task,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, task_id: str) -> Task | None:
        """Fetch task by ID."""
        cur = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return _row_to_task(row) if row else None

    def list_active(
        self,
        category_id: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        """List active non-deleted tasks with optional filters."""
        query = "SELECT * FROM tasks WHERE is_deleted = 0"
        params: list[Any] = []

        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"
        cur = self.conn.execute(query, params)
        return [_row_to_task(row) for row in cur.fetchall()]

    def update(
        self,
        task_id: str,
        title: str | None = None,
        category_id: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        status: str | None = None,
        task_label: str | None = None,
        critical_level: str | None = None,
        pace_level: str | None = None,
        is_google_task: bool | None = None,
    ) -> Task | None:
        """Update task fields; automatically bumps updated_at timestamp."""
        existing = self.get_by_id(task_id)
        if not existing or existing.is_deleted:
            return None

        now = _now_utc()
        new_title = title.strip() if title is not None else existing.title
        new_category_id = (
            category_id if category_id is not None else existing.category_id
        )
        new_description = (
            description if description is not None else existing.description
        )
        new_due_date = due_date if due_date is not None else existing.due_date
        new_status = status if status is not None else existing.status
        new_label = (
            task_label if task_label is not None else existing.task_label
        )
        new_critical = (
            critical_level
            if critical_level is not None
            else existing.critical_level
        )
        new_pace = pace_level if pace_level is not None else existing.pace_level
        new_google = (
            is_google_task
            if is_google_task is not None
            else existing.is_google_task
        )

        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE tasks SET
                    title = ?, category_id = ?, description = ?,
                    due_date = ?, status = ?, task_label = ?,
                    critical_level = ?, pace_level = ?, is_google_task = ?,
                    updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (
                    new_title,
                    new_category_id,
                    new_description,
                    new_due_date,
                    new_status,
                    new_label,
                    new_critical,
                    new_pace,
                    1 if new_google else 0,
                    now,
                    task_id,
                ),
            )
        return self.get_by_id(task_id)

    def soft_delete(self, task_id: str) -> bool:
        """Soft-delete task and cascade soft-delete to its reminders."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE tasks
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, task_id),
            )
            if cur.rowcount == 0:
                return False

            # Cascade: soft-delete task's reminders in the same transaction
            cur.execute(
                """
                UPDATE reminders
                SET is_deleted = 1, updated_at = ?
                WHERE task_id = ? AND is_deleted = 0
                """,
                (now, task_id),
            )
        return True


class ReminderRepository:
    """Data access operations for Reminder alerts."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, task_id: str, remind_at: str) -> Reminder:
        """Create and schedule a reminder for an existing task."""
        rem_id = str(uuid.uuid4())
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO reminders (
                    id, task_id, remind_at, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, 0)
                """,
                (rem_id, task_id, remind_at, now, now),
            )
        return Reminder(
            id=rem_id,
            task_id=task_id,
            remind_at=remind_at,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, reminder_id: str) -> Reminder | None:
        """Fetch reminder by ID."""
        cur = self.conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        )
        row = cur.fetchone()
        return _row_to_reminder(row) if row else None

    def list_due(self, before_timestamp: str) -> list[Reminder]:
        """Query active reminders due at or before a given timestamp.

        Enforces:
        - reminder is_deleted = 0.
        - linked task is_deleted = 0 (excludes reminders of deleted tasks).
        - reminder has not already fired (not in reminder_fires table).
        """
        cur = self.conn.execute(
            """
            SELECT r.* FROM reminders r
            JOIN tasks t ON r.task_id = t.id
            WHERE r.is_deleted = 0
              AND t.is_deleted = 0
              AND r.remind_at <= ?
              AND NOT EXISTS (
                  SELECT 1 FROM reminder_fires rf WHERE rf.reminder_id = r.id
              )
            ORDER BY r.remind_at ASC
            """,
            (before_timestamp,),
        )
        return [_row_to_reminder(row) for row in cur.fetchall()]

    def mark_fired(self, reminder_id: str) -> None:
        """Record that a reminder alert has been dispatched on this device."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT OR IGNORE INTO reminder_fires (reminder_id, fired_at)
                VALUES (?, ?)
                """,
                (reminder_id, now),
            )

    def is_fired(self, reminder_id: str) -> bool:
        """Check if reminder was already dispatched on this device."""
        cur = self.conn.execute(
            "SELECT 1 FROM reminder_fires WHERE reminder_id = ?",
            (reminder_id,),
        )
        return cur.fetchone() is not None

    def soft_delete(self, reminder_id: str) -> bool:
        """Soft-delete an individual reminder."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE reminders
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, reminder_id),
            )
            return cur.rowcount > 0


class AppStateRepository:
    """Data access operations for local machine-written runtime state."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a machine-written state value."""
        cur = self.conn.execute(
            "SELECT value FROM app_state WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return str(row["value"]) if row else default

    def set(self, key: str, value: str) -> None:
        """Set or update a machine-written state value atomically."""
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO app_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_widget_position(self) -> tuple[int, int] | None:
        """Retrieve saved widget screen coordinates (widget_x, widget_y)."""
        x_str = self.get("widget_x")
        y_str = self.get("widget_y")
        if x_str is not None and y_str is not None:
            try:
                return int(x_str), int(y_str)
            except ValueError:
                return None
        return None

    def set_widget_position(self, x: int, y: int) -> None:
        """Save widget screen coordinates to machine state."""
        with transaction(self.conn):
            self.set("widget_x", str(x))
            self.set("widget_y", str(y))
