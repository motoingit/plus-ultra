"""Database schema initialization and maintenance routines."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from plus_ultra.infrastructure.persistence.database_config import DatabaseConfig
from plus_ultra.infrastructure.persistence.database_factory import (
    DatabaseFactory,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (
    AppStateModel,
    Base,
    CategoryModel,
    CodeItemModel,
    CourseModel,
    IdeaDoubtModel,
    OpportunityModel,
    QuickLinkModel,
    ReminderFireModel,
    ReminderModel,
    TaskModel,
)

logger = logging.getLogger(__name__)


def init_database(
    engine: Engine | None = None,
    config: DatabaseConfig | None = None,
) -> Engine:
    """Non-destructively initialize missing tables using SQLAlchemy metadata.

    Preserves existing tables, constraints, indexes, and user records.
    Does not use or require migration versioning (Alembic).

    Returns:
        The configured Engine instance.
    """
    if engine is None:
        factory = DatabaseFactory(config)
        engine = factory.engine

    logger.info("Initializing database schema via Base.metadata.create_all...")
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            conn.exec_driver_sql("PRAGMA user_version = 2;")
    logger.info("Database schema verified and initialized non-destructively.")
    return engine


def wipe_database(
    target: Session | Engine | Any | None = None,
) -> None:
    """Transactionally clear all application records while preserving schema.

    Deletes records in proper foreign-key dependency order across all 10
    application tables.
    """
    if target is None:
        factory = DatabaseFactory()
        session = factory.create_session()
        _wipe_via_session(session)
        session.close()
    elif isinstance(target, Session):
        _wipe_via_session(target)
    elif isinstance(target, Engine):
        with Session(target) as session:
            _wipe_via_session(session)
    else:
        # Backward compatibility for legacy sqlite3.Connection
        try:
            with target:
                cur = target.cursor()
                cur.execute("PRAGMA foreign_keys = OFF;")
                for tbl in [
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
                ]:
                    cur.execute(f"DELETE FROM {tbl};")
                cur.execute("PRAGMA foreign_keys = ON;")
        except Exception as exc:
            logger.error("Legacy wipe failed: %s", exc)
            raise


def _wipe_via_session(session: Session) -> None:
    """Delete all rows using typed SQLAlchemy ORM delete statements."""
    try:
        # Delete in foreign key dependency order
        session.execute(delete(ReminderFireModel))
        session.execute(delete(ReminderModel))
        session.execute(delete(TaskModel))
        session.execute(delete(CategoryModel))
        session.execute(delete(AppStateModel))
        session.execute(delete(CodeItemModel))
        session.execute(delete(CourseModel))
        session.execute(delete(IdeaDoubtModel))
        session.execute(delete(OpportunityModel))
        session.execute(delete(QuickLinkModel))
        session.commit()
        logger.info("All domain tables cleared successfully in transaction.")
    except Exception as exc:
        session.rollback()
        logger.error("Failed to wipe database: %s", exc)
        raise
