"""Database configuration and environment provider."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from plus_ultra.config import get_db_path

DEFAULT_BACKEND: str = "sqlalchemy"


@dataclass(slots=True, frozen=True)
class DatabaseConfig:
    """Centralized database configuration settings."""

    backend: str = DEFAULT_BACKEND
    url: str = ""
    echo: bool = False
    pool_pre_ping: bool = True

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Create configuration resolved from environment and defaults."""
        backend = os.environ.get("PERSISTENCE_BACKEND", DEFAULT_BACKEND).strip()
        url = os.environ.get("DATABASE_URL", "").strip()

        if not url:
            # Default to SQLite database located in user application data dir
            default_path = get_db_path().resolve()
            default_path.parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{default_path}"

        echo = os.environ.get("DATABASE_ECHO", "").lower() in (
            "1",
            "true",
            "yes",
        )
        return cls(backend=backend, url=url, echo=echo)

    @classmethod
    def for_sqlite_path(
        cls, path: Path | str, echo: bool = False
    ) -> DatabaseConfig:
        """Create configuration for a specific SQLite file path."""
        p = Path(path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return cls(backend="sqlalchemy", url=f"sqlite:///{p}", echo=echo)

    @classmethod
    def for_in_memory(cls, echo: bool = False) -> DatabaseConfig:
        """Create configuration for an isolated in-memory SQLite database."""
        return cls(backend="sqlalchemy", url="sqlite:///:memory:", echo=echo)

    @property
    def is_sqlite(self) -> bool:
        """Return True if configured database is SQLite."""
        return self.url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        """Return True if configured database is PostgreSQL."""
        return self.url.startswith("postgresql")
