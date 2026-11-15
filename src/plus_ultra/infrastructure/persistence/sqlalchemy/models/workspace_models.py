"""Workspace tabs ORM models for SQLAlchemy 2.x."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from plus_ultra.infrastructure.persistence.sqlalchemy.base import Base


class CodeItemModel(Base):
    """SQLAlchemy model for code_items table."""

    __tablename__ = "code_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    language: Mapped[str] = mapped_column(
        String(64),
        default="python",
        server_default=text("'python'"),
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        String(32),
        default="Easy",
        server_default=text("'Easy'"),
        nullable=False,
    )
    is_done: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    url: Mapped[str] = mapped_column(
        String(1024), default="", server_default=text("''"), nullable=False
    )
    notes: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    __table_args__ = (
        Index(
            "idx_code_items_cat",
            "category",
            sqlite_where=text("is_deleted = 0"),
        ),
    )


class CourseModel(Base):
    """SQLAlchemy model for courses table."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(
        String(64),
        default="Coursera",
        server_default=text("'Coursera'"),
        nullable=False,
    )
    instructor: Mapped[str] = mapped_column(
        String(128), default="", server_default=text("''"), nullable=False
    )
    total_modules: Mapped[int] = mapped_column(
        Integer, default=10, server_default=text("10"), nullable=False
    )
    completed_modules: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    url: Mapped[str] = mapped_column(
        String(1024), default="", server_default=text("''"), nullable=False
    )
    notes: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )


class IdeaDoubtModel(Base):
    """SQLAlchemy model for ideas_doubts table."""

    __tablename__ = "ideas_doubts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    tech_stack_or_ref: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="Idea",
        server_default=text("'Idea'"),
        nullable=False,
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    __table_args__ = (
        Index(
            "idx_ideas_doubts_kind",
            "kind",
            "status",
            sqlite_where=text("is_deleted = 0"),
        ),
    )


class OpportunityModel(Base):
    """SQLAlchemy model for opportunities table."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(64),
        default="Internship",
        server_default=text("'Internship'"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        String(1024), default="", server_default=text("''"), nullable=False
    )
    deadline: Mapped[str] = mapped_column(
        String(64), default="", server_default=text("''"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="Saved",
        server_default=text("'Saved'"),
        nullable=False,
    )
    notes: Mapped[str] = mapped_column(
        Text, default="", server_default=text("''"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    __table_args__ = (
        Index(
            "idx_opportunities_kind",
            "kind",
            "status",
            sqlite_where=text("is_deleted = 0"),
        ),
    )


class QuickLinkModel(Base):
    """SQLAlchemy model for quick_links table."""

    __tablename__ = "quick_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64),
        default="Web",
        server_default=text("'Web'"),
        nullable=False,
    )
    click_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )

    __table_args__ = (
        Index(
            "idx_quick_links_cat",
            "category",
            sqlite_where=text("is_deleted = 0"),
        ),
    )
