"""Database migration runner and schema version management."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from plus_ultra.database.connection import get_connection, transaction
from plus_ultra.database.schema import (
    MIGRATION_V1_SQL,
    MIGRATION_V2_SQL,
)

logger = logging.getLogger(__name__)


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

        if current_version < 2:
            logger.info("Applying Migration 2 (workspace tabs)...")
            with transaction(conn) as cur:
                cur.executescript(MIGRATION_V2_SQL)
            set_schema_version(conn, 2)
            logger.info("Database migrated successfully to version 2.")

    finally:
        conn.close()
