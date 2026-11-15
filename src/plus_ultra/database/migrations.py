"""Database initialization and schema version management."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from plus_ultra.database.connection import get_engine
from plus_ultra.database.schema import CURRENT_SCHEMA_VERSION
from plus_ultra.infrastructure.persistence.database_initializer import (
    init_database,
)

logger = logging.getLogger(__name__)


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return current PRAGMA user_version from SQLite database."""
    cur = conn.execute("PRAGMA user_version;")
    row = cur.fetchone()
    return int(row[0]) if row else CURRENT_SCHEMA_VERSION


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Set PRAGMA user_version on SQLite database."""
    conn.execute(f"PRAGMA user_version = {int(version)};")


def init_db(db_path: Path | None = None) -> None:
    """Initialize database schema non-destructively using SQLAlchemy."""
    engine = get_engine(db_path)
    init_database(engine)
    logger.info(
        "Database initialized via SQLAlchemy metadata (version %d).",
        CURRENT_SCHEMA_VERSION,
    )
