"""Database connection management and backward-compatibility adapters."""

from __future__ import annotations

import contextlib
import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from plus_ultra import config
from plus_ultra.infrastructure.persistence.database_config import DatabaseConfig
from plus_ultra.infrastructure.persistence.database_factory import (
    DatabaseFactory,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.session import (
    create_database_engine,
    create_session_factory,
)

logger = logging.getLogger(__name__)


def get_engine(db_path: Path | None = None) -> Engine:
    """Return an Engine configured for db_path or default config."""
    if db_path is not None:
        cfg = DatabaseConfig.for_sqlite_path(db_path)
        return create_database_engine(cfg)
    return DatabaseFactory().engine


def get_session(db_path: Path | None = None) -> Session:
    """Create a scoped SQLAlchemy session."""
    engine = get_engine(db_path)
    factory = create_session_factory(engine)
    return factory()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return configured SQLite connection with pragmas."""
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
    """Context manager for ACID transactions (backward compatibility)."""
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction rolled back due to error: %s", exc)
        raise
