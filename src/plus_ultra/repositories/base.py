"""Base repository utilities facade."""

from __future__ import annotations

from plus_ultra.infrastructure.persistence.sqlalchemy.repositories.base import (
    SqlAlchemyRepositoryBase,
    _now_utc,
)

__all__ = ["SqlAlchemyRepositoryBase", "_now_utc"]
