"""Data access operations for Reminder alerts."""

from __future__ import annotations

import sqlite3
import uuid

from plus_ultra.database.connection import transaction
from plus_ultra.datetime_utils import parse_flexible_datetime
from plus_ultra.models import Reminder
from plus_ultra.repositories.base import _now_utc


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
        - evaluates due status using aware datetime comparison.
        """
        cur = self.conn.execute(
            """
            SELECT r.* FROM reminders r
            JOIN tasks t ON r.task_id = t.id
            WHERE r.is_deleted = 0
              AND t.is_deleted = 0
              AND NOT EXISTS (
                  SELECT 1 FROM reminder_fires rf WHERE rf.reminder_id = r.id
              )
            ORDER BY r.remind_at ASC
            """
        )
        cutoff = parse_flexible_datetime(before_timestamp)
        due_list: list[Reminder] = []
        for row in cur.fetchall():
            rem = _row_to_reminder(row)
            try:
                rem_dt = parse_flexible_datetime(rem.remind_at)
                if rem_dt <= cutoff:
                    due_list.append(rem)
            except Exception:
                continue
        return due_list

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
