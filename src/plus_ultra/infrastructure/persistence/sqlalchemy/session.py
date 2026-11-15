"""SQLAlchemy engine, pragmas, and session management."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from plus_ultra.infrastructure.persistence.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(
    dbapi_connection: object, _connection_record: object
) -> None:
    """Enforce SQLite integrity, concurrency, and durability pragmas."""
    mod = getattr(dbapi_connection.__class__, "__module__", "")
    if mod.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.close()


def create_database_engine(config: DatabaseConfig | None = None) -> Engine:
    """Create and configure a modern SQLAlchemy 2.x Engine."""
    cfg = config or DatabaseConfig.from_env()

    engine_kwargs: dict[str, object] = {
        "echo": cfg.echo,
    }

    # For SQLite in-memory, use StaticPool to share connection across threads
    if cfg.url == "sqlite:///:memory:":
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool
    elif cfg.is_sqlite:
        engine_kwargs["connect_args"] = {
            "check_same_thread": False,
            "timeout": 5.0,
        }
    else:
        # PostgreSQL / other relational backends
        engine_kwargs["pool_pre_ping"] = cfg.pool_pre_ping

    engine = create_engine(cfg.url, **engine_kwargs)
    logger.debug("Configured SQLAlchemy Engine for: %s", cfg.url.split("@")[-1])
    return engine


def create_session_factory(
    engine: Engine | None = None,
) -> sessionmaker[Session]:
    """Create a scoped sessionmaker factory bound to the Engine."""
    eng = engine or create_database_engine()
    return sessionmaker(
        bind=eng,
        autoflush=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(
    factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    """Provide a transactional session scope with commit and rollback."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
