"""Database connection management, migrations, and transactions for PLUS-ULTRA.

Applies DBMS concepts:
- ACID Transactions: Atomic commit and rollback guarantees via transaction().
- Concurrency Control: Write-Ahead Logging (WAL mode) for non-blocking reads.
- Referential Integrity: Foreign keys with ON DELETE CASCADE and SET NULL.
- Schema Evolution: Migration runner using SQLite PRAGMA user_version.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from plus_ultra import config

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1

MIGRATION_V1_SQL = """
-- Categories table (reusable across tasks and features)
CREATE TABLE IF NOT EXISTS categories (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    color      TEXT DEFAULT '#4a5568',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Partial index: allow reusing category names if previous one was soft-deleted
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_name_active
    ON categories(name) WHERE is_deleted = 0;

-- Tasks table with priority, labels, pace, and cloud readiness
CREATE TABLE IF NOT EXISTS tasks (
    id             TEXT PRIMARY KEY,
    category_id    TEXT REFERENCES categories(id) ON DELETE SET NULL,
    title          TEXT NOT NULL CHECK(length(trim(title)) > 0),
    description    TEXT DEFAULT '',
    due_date       TEXT,
    status         TEXT NOT NULL DEFAULT 'Pending'
                   CHECK(status IN (
                       'Pending', 'In Progress', 'Completed', 'Overdue'
                   )),
    task_label     TEXT DEFAULT 'College',
    critical_level TEXT NOT NULL DEFAULT 'Medium'
                   CHECK(critical_level IN ('High', 'Medium', 'Low')),
    pace_level     TEXT NOT NULL DEFAULT 'Short-term'
                   CHECK(pace_level IN ('Long-term', 'Short-term')),
    is_google_task INTEGER NOT NULL DEFAULT 0 CHECK(is_google_task IN (0, 1)),
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    synced_at      TEXT,
    is_deleted     INTEGER NOT NULL DEFAULT 0
);

-- Reminders table linked to tasks
CREATE TABLE IF NOT EXISTS reminders (
    id         TEXT PRIMARY KEY,
    task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at  TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Partial index: scheduler queries active reminders
CREATE INDEX IF NOT EXISTS idx_reminders_due
    ON reminders(remind_at) WHERE is_deleted = 0;

-- Local-only table: reminder fired state is device-specific
CREATE TABLE IF NOT EXISTS reminder_fires (
    reminder_id TEXT PRIMARY KEY REFERENCES reminders(id) ON DELETE CASCADE,
    fired_at    TEXT NOT NULL
);

-- machine-written state only (widget_x, widget_y, last_synced_at);
-- user preferences live only in user-settings.json
CREATE TABLE IF NOT EXISTS app_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Create and configure a connection to the SQLite database.

    Enforces:
    - Foreign keys enabled.
    - Write-Ahead Logging (WAL) journal mode.
    - Busy timeout for concurrency resilience.
    - Row factory returning dict-accessible rows.
    """
    path = db_path or config.get_db_path()
    config.get_data_dir()  # Ensure data directory exists with mode 0o700

    conn = sqlite3.connect(path, timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


@contextlib.contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    """Context manager for ACID transactions.

    Executes a block of operations atomically:
    - Commits automatically if the block finishes without error.
    - Rolls back immediately on any unhandled exception.
    """
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction rolled back due to error: %s", exc)
        raise


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return current PRAGMA user_version from SQLite database."""
    cur = conn.execute("PRAGMA user_version;")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Set PRAGMA user_version on SQLite database."""
    conn.execute(f"PRAGMA user_version = {int(version)};")


def init_db(db_path: Path | None = None) -> None:
    """Run pending database schema migrations incrementally."""
    conn = get_connection(db_path)
    try:
        current_version = get_schema_version(conn)
        logger.info("Current SQLite database version: %d", current_version)

        if current_version < 1:
            logger.info("Applying Migration 1 (core schema)...")
            with transaction(conn) as cur:
                cur.executescript(MIGRATION_V1_SQL)
            set_schema_version(conn, 1)
            logger.info("Database migrated successfully to version 1.")
    finally:
        conn.close()
