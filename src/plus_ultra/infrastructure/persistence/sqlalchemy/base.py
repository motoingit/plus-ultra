"""SQLAlchemy Declarative Base for PLUS-ULTRA."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative Base containing common metadata for all ORM models."""

    pass

