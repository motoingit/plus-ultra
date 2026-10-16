"""Data access repositories for PLUS-ULTRA.

Applies DBMS concepts:
- Parameterized SQL: Defense against SQL injection across all operations.
- Cascading Soft Deletes: Atomic multi-table updates within single transactions.
- Query Optimization: Indexed filtering for active tasks and due reminders.
- Machine State Separation: Isolated AppState repository for runtime state.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from plus_ultra.db import transaction
from plus_ultra.models import (
    Category,
    CodeItem,
    Course,
    IdeaDoubt,
    Opportunity,
    QuickLink,
    Reminder,
    Task,
)


def _now_utc() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def _row_to_category(row: sqlite3.Row) -> Category:
    """Convert an SQLite row to a Category model."""
    return Category(
        id=row["id"],
        name=row["name"],
        color=row["color"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


def _row_to_task(row: sqlite3.Row) -> Task:
    """Convert an SQLite row to a Task model."""
    return Task(
        id=row["id"],
        category_id=row["category_id"],
        title=row["title"],
        description=row["description"],
        due_date=row["due_date"],
        status=row["status"],
        task_label=row["task_label"],
        critical_level=row["critical_level"],
        pace_level=row["pace_level"],
        is_google_task=bool(row["is_google_task"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


def _row_to_reminder(row: sqlite3.Row) -> Reminder:
    """Convert an SQLite row to a Reminder model."""
    return Reminder(
        id=row["id"],
        task_id=row["task_id"],
        remind_at=row["remind_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


def _row_to_code_item(row: sqlite3.Row) -> CodeItem:
    """Convert an SQLite row to a CodeItem model."""
    return CodeItem(
        id=row["id"],
        category=row["category"],
        title=row["title"],
        content=row["content"],
        language=row["language"],
        difficulty=row["difficulty"],
        is_done=row["is_done"],
        url=row["url"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


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


def _row_to_idea_doubt(row: sqlite3.Row) -> IdeaDoubt:
    """Convert an SQLite row to an IdeaDoubt model."""
    return IdeaDoubt(
        id=row["id"],
        kind=row["kind"],
        title=row["title"],
        description=row["description"],
        tech_stack_or_ref=row["tech_stack_or_ref"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


def _row_to_opportunity(row: sqlite3.Row) -> Opportunity:
    """Convert an SQLite row to an Opportunity model."""
    return Opportunity(
        id=row["id"],
        title=row["title"],
        organization=row["organization"],
        kind=row["kind"],
        url=row["url"],
        deadline=row["deadline"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


def _row_to_quick_link(row: sqlite3.Row) -> QuickLink:
    """Convert an SQLite row to a QuickLink model."""
    return QuickLink(
        id=row["id"],
        name=row["name"],
        target_uri=row["target_uri"],
        category=row["category"],
        click_count=row["click_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        synced_at=row["synced_at"],
        is_deleted=row["is_deleted"],
    )


class CategoryRepository:
    """Data access operations for Category entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, name: str, color: str = "#4a5568") -> Category:
        """Create a new category.

        Raises:
            sqlite3.IntegrityError: If active category name already exists.
        """
        cat_id = str(uuid.uuid4())
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO categories (
                    id, name, color, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, 0)
                """,
                (cat_id, name.strip(), color, now, now),
            )
        return Category(
            id=cat_id,
            name=name.strip(),
            color=color,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, category_id: str) -> Category | None:
        """Fetch category by ID, including soft-deleted ones."""
        cur = self.conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        )
        row = cur.fetchone()
        return _row_to_category(row) if row else None

    def list_active(self) -> list[Category]:
        """Return all active (non-deleted) categories ordered by name."""
        cur = self.conn.execute(
            """
            SELECT * FROM categories
            WHERE is_deleted = 0
            ORDER BY name COLLATE NOCASE ASC
            """
        )
        return [_row_to_category(row) for row in cur.fetchall()]

    def update(
        self, category_id: str, name: str, color: str
    ) -> Category | None:
        """Update category name and color; sets updated_at timestamp."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE categories
                SET name = ?, color = ?, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (name.strip(), color, now, category_id),
            )
            if cur.rowcount == 0:
                return None
        return self.get_by_id(category_id)

    def soft_delete(self, category_id: str) -> bool:
        """Soft-delete category and nullify linked tasks' category_id."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE categories
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, category_id),
            )
            if cur.rowcount == 0:
                return False

            # Cascade: set tasks.category_id to NULL in same transaction
            cur.execute(
                """
                UPDATE tasks
                SET category_id = NULL, updated_at = ?
                WHERE category_id = ? AND is_deleted = 0
                """,
                (now, category_id),
            )
        return True


class TaskRepository:
    """Data access operations for Task entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(
        self,
        title: str,
        category_id: str | None = None,
        description: str = "",
        due_date: str | None = None,
        status: str = "Pending",
        task_label: str = "College",
        critical_level: str = "Medium",
        pace_level: str = "Short-term",
        is_google_task: bool = False,
    ) -> Task:
        """Create and persist a new task record."""
        clean_title = title.strip()
        task_id = str(uuid.uuid4())
        now = _now_utc()
        google_flag = 1 if is_google_task else 0

        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, category_id, title, description, due_date, status,
                    task_label, critical_level, pace_level, is_google_task,
                    created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    task_id,
                    category_id,
                    clean_title,
                    description,
                    due_date,
                    status,
                    task_label,
                    critical_level,
                    pace_level,
                    google_flag,
                    now,
                    now,
                ),
            )

        return Task(
            id=task_id,
            category_id=category_id,
            title=clean_title,
            description=description,
            due_date=due_date,
            status=status,
            task_label=task_label,
            critical_level=critical_level,
            pace_level=pace_level,
            is_google_task=is_google_task,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, task_id: str) -> Task | None:
        """Fetch task by ID."""
        cur = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return _row_to_task(row) if row else None

    def list_active(
        self,
        category_id: str | None = None,
        status: str | None = None,
    ) -> list[Task]:
        """List active non-deleted tasks with optional filters."""
        query = "SELECT * FROM tasks WHERE is_deleted = 0"
        params: list[Any] = []

        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"
        cur = self.conn.execute(query, params)
        return [_row_to_task(row) for row in cur.fetchall()]

    def update(
        self,
        task_id: str,
        title: str | None = None,
        category_id: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        status: str | None = None,
        task_label: str | None = None,
        critical_level: str | None = None,
        pace_level: str | None = None,
        is_google_task: bool | None = None,
    ) -> Task | None:
        """Update task fields; automatically bumps updated_at timestamp."""
        existing = self.get_by_id(task_id)
        if not existing or existing.is_deleted:
            return None

        now = _now_utc()
        new_title = title.strip() if title is not None else existing.title
        new_category_id = (
            category_id if category_id is not None else existing.category_id
        )
        new_description = (
            description if description is not None else existing.description
        )
        new_due_date = due_date if due_date is not None else existing.due_date
        new_status = status if status is not None else existing.status
        new_label = (
            task_label if task_label is not None else existing.task_label
        )
        new_critical = (
            critical_level
            if critical_level is not None
            else existing.critical_level
        )
        new_pace = pace_level if pace_level is not None else existing.pace_level
        new_google = (
            is_google_task
            if is_google_task is not None
            else existing.is_google_task
        )

        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE tasks SET
                    title = ?, category_id = ?, description = ?,
                    due_date = ?, status = ?, task_label = ?,
                    critical_level = ?, pace_level = ?, is_google_task = ?,
                    updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (
                    new_title,
                    new_category_id,
                    new_description,
                    new_due_date,
                    new_status,
                    new_label,
                    new_critical,
                    new_pace,
                    1 if new_google else 0,
                    now,
                    task_id,
                ),
            )
        return self.get_by_id(task_id)

    def soft_delete(self, task_id: str) -> bool:
        """Soft-delete task and cascade soft-delete to its reminders."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE tasks
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, task_id),
            )
            if cur.rowcount == 0:
                return False

            # Cascade: soft-delete task's reminders in the same transaction
            cur.execute(
                """
                UPDATE reminders
                SET is_deleted = 1, updated_at = ?
                WHERE task_id = ? AND is_deleted = 0
                """,
                (now, task_id),
            )
        return True


class ReminderRepository:
    """Data access operations for Reminder alerts."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, task_id: str, remind_at: str) -> Reminder:
        """Create and schedule a reminder for an existing task."""
        rem_id = str(uuid.uuid4())
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO reminders (
                    id, task_id, remind_at, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, 0)
                """,
                (rem_id, task_id, remind_at, now, now),
            )
        return Reminder(
            id=rem_id,
            task_id=task_id,
            remind_at=remind_at,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, reminder_id: str) -> Reminder | None:
        """Fetch reminder by ID."""
        cur = self.conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        )
        row = cur.fetchone()
        return _row_to_reminder(row) if row else None

    def list_due(self, before_timestamp: str) -> list[Reminder]:
        """Query active reminders due at or before a given timestamp.

        Enforces:
        - reminder is_deleted = 0.
        - linked task is_deleted = 0 (excludes reminders of deleted tasks).
        - reminder has not already fired (not in reminder_fires table).
        """
        cur = self.conn.execute(
            """
            SELECT r.* FROM reminders r
            JOIN tasks t ON r.task_id = t.id
            WHERE r.is_deleted = 0
              AND t.is_deleted = 0
              AND r.remind_at <= ?
              AND NOT EXISTS (
                  SELECT 1 FROM reminder_fires rf WHERE rf.reminder_id = r.id
              )
            ORDER BY r.remind_at ASC
            """,
            (before_timestamp,),
        )
        return [_row_to_reminder(row) for row in cur.fetchall()]

    def mark_fired(self, reminder_id: str) -> None:
        """Record that a reminder alert has been dispatched on this device."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT OR IGNORE INTO reminder_fires (reminder_id, fired_at)
                VALUES (?, ?)
                """,
                (reminder_id, now),
            )

    def is_fired(self, reminder_id: str) -> bool:
        """Check if reminder was already dispatched on this device."""
        cur = self.conn.execute(
            "SELECT 1 FROM reminder_fires WHERE reminder_id = ?",
            (reminder_id,),
        )
        return cur.fetchone() is not None

    def soft_delete(self, reminder_id: str) -> bool:
        """Soft-delete an individual reminder."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE reminders
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, reminder_id),
            )
            return cur.rowcount > 0


class AppStateRepository:
    """Data access operations for local machine-written runtime state."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a machine-written state value."""
        cur = self.conn.execute(
            "SELECT value FROM app_state WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return str(row["value"]) if row else default

    def set(self, key: str, value: str) -> None:
        """Set or update a machine-written state value atomically."""
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO app_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_widget_position(self) -> tuple[int, int] | None:
        """Retrieve saved widget screen coordinates (widget_x, widget_y)."""
        x_str = self.get("widget_x")
        y_str = self.get("widget_y")
        if x_str is not None and y_str is not None:
            try:
                return int(x_str), int(y_str)
            except ValueError:
                return None
        return None

    def set_widget_position(self, x: int, y: int) -> None:
        """Save widget screen coordinates to machine state."""
        with transaction(self.conn):
            self.set("widget_x", str(x))
            self.set("widget_y", str(y))


class CodeRepository:
    """Data access operations for CodeItem entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_items(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[CodeItem]:
        """Query active code items with optional category and search filters."""
        query = ["SELECT * FROM code_items WHERE is_deleted = 0"]
        params: list[Any] = []

        if category and category != "All":
            query.append("AND category = ?")
            params.append(category)

        if search_query:
            query.append("AND (title LIKE ? OR content LIKE ? OR notes LIKE ?)")
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_code_item(row) for row in cur.fetchall()]

    def get(self, item_id: str) -> CodeItem | None:
        """Fetch a single code item by ID."""
        cur = self.conn.execute(
            "SELECT * FROM code_items WHERE id = ? AND is_deleted = 0",
            (item_id,),
        )
        row = cur.fetchone()
        return _row_to_code_item(row) if row else None

    def create(
        self,
        category: str,
        title: str,
        content: str = "",
        language: str = "python",
        difficulty: str = "Easy",
        is_done: int = 0,
        url: str = "",
        notes: str = "",
    ) -> CodeItem:
        """Create a new code item."""
        now = _now_utc()
        item_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO code_items (
                    id, category, title, content, language, difficulty,
                    is_done, url, notes, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    item_id,
                    category,
                    title,
                    content,
                    language,
                    difficulty,
                    is_done,
                    url,
                    notes,
                    now,
                    now,
                ),
            )
        return CodeItem(
            id=item_id,
            category=category,
            title=title,
            content=content,
            language=language,
            difficulty=difficulty,
            is_done=is_done,
            url=url,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def toggle_done(self, item_id: str) -> bool:
        """Toggle is_done status for a DSA item."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE code_items
                SET is_done = CASE WHEN is_done = 1 THEN 0 ELSE 1 END,
                    updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, item_id),
            )
            return cur.rowcount > 0

    def soft_delete(self, item_id: str) -> bool:
        """Soft delete a code item."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE code_items
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, item_id),
            )
            return cur.rowcount > 0


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


class IdeaDoubtRepository:
    """Data access operations for IdeaDoubt entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_items(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[IdeaDoubt]:
        """List active ideas and doubts."""
        query = ["SELECT * FROM ideas_doubts WHERE is_deleted = 0"]
        params: list[Any] = []

        if kind and kind != "All":
            query.append("AND kind = ?")
            params.append(kind)

        if status and status != "All":
            query.append("AND status = ?")
            params.append(status)

        if search_query:
            query.append(
                "AND (title LIKE ? OR description LIKE ? OR "
                "tech_stack_or_ref LIKE ?)"
            )
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_idea_doubt(row) for row in cur.fetchall()]

    def get(self, item_id: str) -> IdeaDoubt | None:
        """Fetch item by ID."""
        cur = self.conn.execute(
            "SELECT * FROM ideas_doubts WHERE id = ? AND is_deleted = 0",
            (item_id,),
        )
        row = cur.fetchone()
        return _row_to_idea_doubt(row) if row else None

    def create(
        self,
        kind: str,
        title: str,
        description: str = "",
        tech_stack_or_ref: str = "",
        status: str = "Idea",
    ) -> IdeaDoubt:
        """Create a new idea or doubt."""
        now = _now_utc()
        item_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO ideas_doubts (
                    id, kind, title, description, tech_stack_or_ref,
                    status, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    item_id,
                    kind,
                    title,
                    description,
                    tech_stack_or_ref,
                    status,
                    now,
                    now,
                ),
            )
        return IdeaDoubt(
            id=item_id,
            kind=kind,
            title=title,
            description=description,
            tech_stack_or_ref=tech_stack_or_ref,
            status=status,
            created_at=now,
            updated_at=now,
        )

    def update_status(self, item_id: str, new_status: str) -> bool:
        """Update status of an idea or doubt."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE ideas_doubts
                SET status = ?, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (new_status, now, item_id),
            )
            return cur.rowcount > 0

    def soft_delete(self, item_id: str) -> bool:
        """Soft delete an idea or doubt."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE ideas_doubts
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, item_id),
            )
            return cur.rowcount > 0


class OpportunityRepository:
    """Data access operations for Opportunity entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_opportunities(
        self,
        kind: str | None = None,
        status: str | None = None,
        search_query: str | None = None,
    ) -> list[Opportunity]:
        """List active opportunities with filters."""
        query = ["SELECT * FROM opportunities WHERE is_deleted = 0"]
        params: list[Any] = []

        if kind and kind != "All":
            query.append("AND kind = ?")
            params.append(kind)

        if status and status != "All":
            query.append("AND status = ?")
            params.append(status)

        if search_query:
            query.append(
                "AND (title LIKE ? OR organization LIKE ? OR notes LIKE ?)"
            )
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        query.append("ORDER BY created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_opportunity(row) for row in cur.fetchall()]

    def get(self, opp_id: str) -> Opportunity | None:
        """Fetch opportunity by ID."""
        cur = self.conn.execute(
            "SELECT * FROM opportunities WHERE id = ? AND is_deleted = 0",
            (opp_id,),
        )
        row = cur.fetchone()
        return _row_to_opportunity(row) if row else None

    def create(
        self,
        title: str,
        organization: str,
        kind: str = "Internship",
        url: str = "",
        deadline: str = "",
        status: str = "Saved",
        notes: str = "",
    ) -> Opportunity:
        """Create a new opportunity."""
        now = _now_utc()
        opp_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO opportunities (
                    id, title, organization, kind, url, deadline,
                    status, notes, created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    opp_id,
                    title,
                    organization,
                    kind,
                    url,
                    deadline,
                    status,
                    notes,
                    now,
                    now,
                ),
            )
        return Opportunity(
            id=opp_id,
            title=title,
            organization=organization,
            kind=kind,
            url=url,
            deadline=deadline,
            status=status,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def update_status(self, opp_id: str, new_status: str) -> bool:
        """Update opportunity status."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE opportunities
                SET status = ?, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (new_status, now, opp_id),
            )
            return cur.rowcount > 0

    def soft_delete(self, opp_id: str) -> bool:
        """Soft delete an opportunity."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE opportunities
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, opp_id),
            )
            return cur.rowcount > 0


class QuickLinkRepository:
    """Data access operations for QuickLink entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_links(
        self,
        category: str | None = None,
        search_query: str | None = None,
    ) -> list[QuickLink]:
        """List active quick links."""
        query = ["SELECT * FROM quick_links WHERE is_deleted = 0"]
        params: list[Any] = []

        if category and category != "All":
            query.append("AND category = ?")
            params.append(category)

        if search_query:
            query.append("AND (name LIKE ? OR target_uri LIKE ?)")
            wildcard = f"%{search_query.strip()}%"
            params.extend([wildcard, wildcard])

        query.append("ORDER BY click_count DESC, created_at DESC")
        cur = self.conn.execute(" ".join(query), params)
        return [_row_to_quick_link(row) for row in cur.fetchall()]

    def get(self, link_id: str) -> QuickLink | None:
        """Fetch quick link by ID."""
        cur = self.conn.execute(
            "SELECT * FROM quick_links WHERE id = ? AND is_deleted = 0",
            (link_id,),
        )
        row = cur.fetchone()
        return _row_to_quick_link(row) if row else None

    def create(
        self,
        name: str,
        target_uri: str,
        category: str = "Web",
    ) -> QuickLink:
        """Create a new quick link."""
        now = _now_utc()
        link_id = uuid.uuid4().hex
        with transaction(self.conn) as cur:
            cur.execute(
                """
                INSERT INTO quick_links (
                    id, name, target_uri, category, click_count,
                    created_at, updated_at, is_deleted
                ) VALUES (?, ?, ?, ?, 0, ?, ?, 0)
                """,
                (link_id, name, target_uri, category, now, now),
            )
        return QuickLink(
            id=link_id,
            name=name,
            target_uri=target_uri,
            category=category,
            click_count=0,
            created_at=now,
            updated_at=now,
        )

    def increment_click(self, link_id: str) -> bool:
        """Increment click count."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE quick_links
                SET click_count = click_count + 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, link_id),
            )
            return cur.rowcount > 0

    def soft_delete(self, link_id: str) -> bool:
        """Soft delete a quick link."""
        now = _now_utc()
        with transaction(self.conn) as cur:
            cur.execute(
                """
                UPDATE quick_links
                SET is_deleted = 1, updated_at = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (now, link_id),
            )
            return cur.rowcount > 0
