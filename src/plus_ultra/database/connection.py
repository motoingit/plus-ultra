"""SQLite database connection management and transaction context manager."""

from __future__ import annotations

import contextlib
import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from plus_ultra import config

logger = logging.getLogger(__name__)


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
