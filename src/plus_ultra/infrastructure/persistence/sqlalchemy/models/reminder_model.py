"""Reminder and ReminderFire ORM models for SQLAlchemy 2.x."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plus_ultra.infrastructure.persistence.sqlalchemy.base import Base

if TYPE_CHECKING:
    from .task_model import TaskModel


class ReminderModel(Base):
    """SQLAlchemy model for reminders table."""

    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    remind_at: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    task: Mapped[TaskModel] = relationship(
        "TaskModel", back_populates="reminders"
    )
    fires: Mapped[list[ReminderFireModel]] = relationship(
        "ReminderFireModel",
        back_populates="reminder",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "idx_reminders_due",
            "remind_at",
            sqlite_where=text("is_deleted = 0"),
        ),
    )


class ReminderFireModel(Base):
    """SQLAlchemy model for reminder_fires device-local tracking table."""

    __tablename__ = "reminder_fires"

    reminder_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reminders.id", ondelete="CASCADE"),
        primary_key=True,
    )
    fired_at: Mapped[str] = mapped_column(String(64), nullable=False)

    reminder: Mapped[ReminderModel] = relationship(
        "ReminderModel", back_populates="fires"
    )
