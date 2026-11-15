"""Database package for PLUS-ULTRA.

Exposes high-level initialization, session management, and maintenance
facades backed by SQLAlchemy 2.x ORM.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from plus_ultra.database.connection import (
    get_connection,
    get_engine,
    get_session,
    transaction,
)
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
from plus_ultra.infrastructure.persistence.database_initializer import (
    wipe_database,
)


def seed_demo_workspace_data(
    target: Any = None, force: bool = False
) -> dict[str, int]:
    """Seed initial demo workspace data across all categories."""
    script_path = Path(__file__).resolve().parents[3] / ".scripts" / "seeds.py"
    if script_path.exists():
        spec = importlib.util.spec_from_file_location("seeds", script_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.seed_demo_workspace_data(target, force=force)
    return {}


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "MIGRATION_V1_SQL",
    "MIGRATION_V2_SQL",
    "get_connection",
    "get_engine",
    "get_schema_version",
    "get_session",
    "init_db",
    "seed_demo_workspace_data",
    "set_schema_version",
    "transaction",
    "wipe_database",
]
