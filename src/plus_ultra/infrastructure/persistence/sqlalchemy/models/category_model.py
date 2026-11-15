"""Category ORM model for SQLAlchemy 2.x."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plus_ultra.infrastructure.persistence.sqlalchemy.base import Base

if TYPE_CHECKING:
    from .task_model import TaskModel


class CategoryModel(Base):
    """SQLAlchemy model for categories table."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(
        String(32),
        default="#4a5568",
        server_default=text("'#4a5568'"),
        nullable=False,
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    tasks: Mapped[list[TaskModel]] = relationship(
        "TaskModel", back_populates="category"
    )

    __table_args__ = (
        Index(
            "idx_categories_name_active",
            "name",
            unique=True,
            sqlite_where=text("is_deleted = 0"),
        ),
    )
