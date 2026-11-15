"""Task ORM model for SQLAlchemy 2.x."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plus_ultra.infrastructure.persistence.sqlalchemy.base import Base

if TYPE_CHECKING:
    from .category_model import CategoryModel
    from .reminder_model import ReminderModel


class TaskModel(Base):
    """SQLAlchemy model for tasks table."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    due_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default="Pending",
        server_default=text("'Pending'"),
        nullable=False,
    )
    task_label: Mapped[str] = mapped_column(
        String(64),
        default="College",
        server_default=text("'College'"),
        nullable=False,
    )
    critical_level: Mapped[str] = mapped_column(
        String(32),
        default="Medium",
        server_default=text("'Medium'"),
        nullable=False,
    )
    pace_level: Mapped[str] = mapped_column(
        String(32),
        default="Short-term",
        server_default=text("'Short-term'"),
        nullable=False,
    )
    is_google_task: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    category: Mapped[CategoryModel | None] = relationship(
        "CategoryModel", back_populates="tasks"
    )
    reminders: Mapped[list[ReminderModel]] = relationship(
        "ReminderModel",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) > 0", name="chk_tasks_title_nonempty"
        ),
        CheckConstraint(
            "status IN ('Pending', 'In Progress', 'Completed', 'Overdue')",
            name="chk_tasks_status_valid",
        ),
        CheckConstraint(
            "critical_level IN ('High', 'Medium', 'Low')",
            name="chk_tasks_critical_level_valid",
        ),
        CheckConstraint(
            "pace_level IN ('Long-term', 'Short-term')",
            name="chk_tasks_pace_level_valid",
        ),
        CheckConstraint(
            "is_google_task IN (0, 1)",
            name="chk_tasks_google_task_flag",
        ),
    )
