"""Data access operations for Task entities."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from plus_ultra.database.connection import transaction
from plus_ultra.models import Task
from plus_ultra.repositories.base import _now_utc


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
