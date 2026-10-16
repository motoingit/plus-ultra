"""Database facade module for backward compatibility.

Re-exports core database symbols from the `plus_ultra.database` package.
"""

from __future__ import annotations

from plus_ultra.database import (
    CURRENT_SCHEMA_VERSION,
    MIGRATION_V1_SQL,
    MIGRATION_V2_SQL,
    get_connection,
    get_schema_version,
    init_db,
    seed_demo_workspace_data,
    set_schema_version,
    transaction,
)

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
