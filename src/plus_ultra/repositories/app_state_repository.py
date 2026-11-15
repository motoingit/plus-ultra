"""AppState repository facade pointing to SQLAlchemy implementation."""

from __future__ import annotations

from plus_ultra.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyAppStateRepository as AppStateRepository,
)

__all__ = ["AppStateRepository"]
