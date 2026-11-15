"""AppState ORM model for SQLAlchemy 2.x."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from plus_ultra.infrastructure.persistence.sqlalchemy.base import Base


class AppStateModel(Base):
    """SQLAlchemy model for app_state key-value machine state table."""

    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

