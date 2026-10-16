"""Data access operations for Course entities."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from plus_ultra.database.connection import transaction
from plus_ultra.models import Course
from plus_ultra.repositories.base import _now_utc


def _row_to_course(row: sqlite3.Row) -> Course:
    """Convert an SQLite row to a Course model."""
    return Course(
        id=row["id"],
        title=row["title"],
        platform=row["platform"],
        instructor=row["instructor"],
        total_modules=row["total_modules"],
        completed_modules=row["completed_modules"],
        url=row["url"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class CourseRepository:
    """Data access operations for Course entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_courses(
        self,
        platform: str | None = None,
        search_query: str | None = None,
    ) -> list[Course]:
        """List active courses with platform and search filters."""
        query = ["SELECT * FROM courses WHERE is_deleted = 0"]
        params: list[Any] = []

        if platform and platform != "All":
            query.append("AND platform = ?")
            params.append(platform)

        if search_query:
            query.append(
                "AND (title LIKE ? OR instructor LIKE ? OR notes LIKE ?)"
            )
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_course(row) for row in cur.fetchall()]

    def get(self, course_id: str) -> Course | None:
        """Fetch course by ID."""
        cur = self.conn.execute(
            "SELECT * FROM courses WHERE id = ? AND is_deleted = 0",
            (course_id,),
        )
        row = cur.fetchone()
        return _row_to_course(row) if row else None

    def create(
        self,
        title: str,
        platform: str = "Coursera",
        instructor: str = "",
        total_modules: int = 10,
        completed_modules: int = 0,
        url: str = "",
        notes: str = "",
    ) -> Course:
        """Insert a new course."""
        now = _now_utc()
        course_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO courses (
                    id, title, platform, instructor, total_modules,
                    completed_modules, url, notes, created_at, updated_at,
                    is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    course_id,
                    title,
                    platform,
                    instructor,
                    total_modules,
                    completed_modules,
                    url,
                    notes,
                    now,
                    now,
                ),
            )
        return Course(
            id=course_id,
            title=title,
            platform=platform,
            instructor=instructor,
            total_modules=total_modules,
            completed_modules=completed_modules,
            url=url,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def increment_module(self, course_id: str) -> bool:
        """Increment completed_modules count up to total_modules."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE courses
                SET completed_modules = MIN(
                    total_modules, completed_modules + 1
                ),
                updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, course_id),
            )
            return cur.rowcount > 0

    def update(
        self,
        course_id: str,
        title: str | None = None,
        platform: str | None = None,
        instructor: str | None = None,
        total_modules: int | None = None,
        completed_modules: int | None = None,
        url: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Update course fields."""
        fields: list[str] = []
        params: list[Any] = []
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if platform is not None:
            fields.append("platform = ?")
            params.append(platform)
        if instructor is not None:
            fields.append("instructor = ?")
            params.append(instructor)
        if total_modules is not None:
            fields.append("total_modules = ?")
            params.append(total_modules)
        if completed_modules is not None:
            fields.append("completed_modules = ?")
            params.append(completed_modules)
        if url is not None:
            fields.append("url = ?")
            params.append(url)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        if not fields:
            return False
        fields.append("updated_at = ?")
        params.extend([_now_utc(), course_id])
        with transaction(self.conn) as cur:
            cur.execute(
                f"UPDATE courses SET {', '.join(fields)} "
                "WHERE id = ? AND is_deleted = 0",
                params,
            )
            return cur.rowcount > 0

    def soft_delete(self, course_id: str) -> bool:
        """Soft delete a course."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE courses
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, course_id),
            )
            return cur.rowcount > 0
