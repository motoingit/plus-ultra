"""Database package for PLUS-ULTRA.

Provides SQLite connection management, ACID transactions, migrations,
and initial demo seeding.
"""

from __future__ import annotations

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
from plus_ultra.database.seeds import seed_demo_workspace_data

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
]
