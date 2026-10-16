"""Data access operations for local machine-written runtime state."""

from __future__ import annotations

import sqlite3

from plus_ultra.database.connection import transaction


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
