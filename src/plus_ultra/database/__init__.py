"""Database package for PLUS-ULTRA.

Provides SQLite connection management, ACID transactions, and migrations.
Demo seeding delegates to .scripts/ outside the primary package src tree.
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

from plus_ultra.database.connection import get_connection, transaction
from plus_ultra.database.migrations import (
    get_schema_version,
    init_db,
    set_schema_version,
)
from plus_ultra.database.schema import (
    CURRENT_SCHEMA_VERSION,
    MIGRATION_V1_SQL,
    MIGRATION_V2_SQL,
)


def seed_demo_workspace_data(conn: sqlite3.Connection) -> None:
    """Delegate to .scripts/seeds.py if present."""
    script_path = Path(__file__).resolve().parents[3] / ".scripts" / "seeds.py"
    if script_path.exists():
        spec = importlib.util.spec_from_file_location("seeds", script_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.seed_demo_workspace_data(conn)


def wipe_database(conn: sqlite3.Connection) -> None:
    """Wipe all user data from all application tables transactionally."""
    tables = [
        "reminder_fires",
        "reminders",
        "tasks",
        "categories",
        "app_state",
        "code_items",
        "courses",
        "ideas_doubts",
        "opportunities",
        "quick_links",
    ]
    with conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        for t in tables:
            cursor.execute(f"DELETE FROM {t};")
        cursor.execute("PRAGMA foreign_keys = ON;")


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIGRATION_V1_SQL",
    "MIGRATION_V2_SQL",
    "get_connection",
    "get_schema_version",
    "init_db",
    "seed_demo_workspace_data",
    "set_schema_version",
    "transaction",
    "wipe_database",
]
