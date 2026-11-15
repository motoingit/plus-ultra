"""Base class and common utilities for SQLAlchemy repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def _now_utc() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


class SqlAlchemyRepositoryBase:
    """Base repository class providing session and transaction management."""

    def __init__(
        self,
        session: Session | Any,
        autocommit: bool = True,
    ) -> None:
        """Initialize repository with an active Session or Connection.

        Args:
            session: Scoped SQLAlchemy Session, Engine, or DBAPI Connection.
            autocommit: If True, commits changes immediately on mutation.
                When operated within a UnitOfWork, set to False so the UoW
                coordinates the transaction commit.
        """
        if isinstance(session, Session):
            self.session = session
        elif isinstance(session, Engine):
            self.session = Session(session)
        elif hasattr(session, "cursor") and not hasattr(session, "scalars"):
            # Wrap legacy DBAPI connection seamlessly
            eng = create_engine(
                "sqlite://",
                creator=lambda: session,
                poolclass=StaticPool,
                pool_reset_on_return=None,
            )
            self.session = Session(eng)
        else:
            self.session = session  # type: ignore[assignment]
        self.autocommit = autocommit

    def _commit_or_flush(self) -> None:
        """Commit when in standalone mode; flush when in Unit of Work."""
        if self.autocommit:
            self.session.commit()
        else:
            self.session.flush()
