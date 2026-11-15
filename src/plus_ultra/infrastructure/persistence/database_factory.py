"""Persistence provider and factory abstraction."""

from __future__ import annotations

import logging

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from plus_ultra.application.interfaces.unit_of_work import (
    UnitOfWork,
    UnitOfWorkFactory,
)
from plus_ultra.infrastructure.persistence.database_config import DatabaseConfig
from plus_ultra.infrastructure.persistence.sqlalchemy.session import (
    create_database_engine,
    create_session_factory,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Central persistence factory supporting pluggable database backends."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig.from_env()
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine:
        """Lazily initialize and return the SQLAlchemy Engine."""
        if self._engine is None:
            valid_relational = (
                "sqlalchemy",
                "sqlite",
                "sqlite3",
                "postgres",
                "postgresql",
            )
            if self.config.backend not in valid_relational:
                raise NotImplementedError(
                    f"Unsupported backend: '{self.config.backend}'. "
                    "Only relational backends ('sqlalchemy', 'sqlite') "
                    "are supported currently."
                )
            self._engine = create_database_engine(self.config)
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        """Lazily initialize and return the scoped sessionmaker."""
        if self._session_factory is None:
            self._session_factory = create_session_factory(self.engine)
        return self._session_factory

    def create_session(self) -> Session:
        """Create a new independent SQLAlchemy Session."""
        return self.session_factory()

    def create_unit_of_work(self) -> UnitOfWork:
        """Create a Unit of Work bound to the configured sessionmaker."""
        return SqlAlchemyUnitOfWork(self.session_factory)

    def get_unit_of_work_factory(self) -> UnitOfWorkFactory:
        """Return a callable factory producing new UnitOfWork instances."""
        return self.create_unit_of_work

    def close(self) -> None:
        """Dispose of the database engine and connection pools cleanly."""
        if self._engine is not None:
            try:
                self._engine.dispose()
                logger.debug("Database engine connection pool disposed.")
            except Exception as exc:
                logger.error("Error disposing database engine: %s", exc)
            finally:
                self._engine = None
                self._session_factory = None
