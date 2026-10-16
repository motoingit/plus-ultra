"""Database connection management, migrations, and transactions for PLUS-ULTRA.

Applies DBMS concepts:
- ACID Transactions: Atomic commit and rollback guarantees via transaction().
- Concurrency Control: Write-Ahead Logging (WAL mode) for non-blocking reads.
- Referential Integrity: Foreign keys with ON DELETE CASCADE and SET NULL.
- Schema Evolution: Migration runner using SQLite PRAGMA user_version.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from plus_ultra import config

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 2


MIGRATION_V1_SQL = """
-- Categories table (reusable across tasks and features)
CREATE TABLE IF NOT EXISTS categories (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    color      TEXT DEFAULT '#4a5568',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Partial index: allow reusing category names if previous one was soft-deleted
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_name_active
    ON categories(name) WHERE is_deleted = 0;

-- Tasks table with priority, labels, pace, and cloud readiness
CREATE TABLE IF NOT EXISTS tasks (
    id             TEXT PRIMARY KEY,
    category_id    TEXT REFERENCES categories(id) ON DELETE SET NULL,
    title          TEXT NOT NULL CHECK(length(trim(title)) > 0),
    description    TEXT DEFAULT '',
    due_date       TEXT,
    status         TEXT NOT NULL DEFAULT 'Pending'
                   CHECK(status IN (
                       'Pending', 'In Progress', 'Completed', 'Overdue'
                   )),
    task_label     TEXT DEFAULT 'College',
    critical_level TEXT NOT NULL DEFAULT 'Medium'
                   CHECK(critical_level IN ('High', 'Medium', 'Low')),
    pace_level     TEXT NOT NULL DEFAULT 'Short-term'
                   CHECK(pace_level IN ('Long-term', 'Short-term')),
    is_google_task INTEGER NOT NULL DEFAULT 0 CHECK(is_google_task IN (0, 1)),
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    synced_at      TEXT,
    is_deleted     INTEGER NOT NULL DEFAULT 0
);

-- Reminders table linked to tasks
CREATE TABLE IF NOT EXISTS reminders (
    id         TEXT PRIMARY KEY,
    task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at  TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Partial index: scheduler queries active reminders
CREATE INDEX IF NOT EXISTS idx_reminders_due
    ON reminders(remind_at) WHERE is_deleted = 0;

-- Local-only table: reminder fired state is device-specific
CREATE TABLE IF NOT EXISTS reminder_fires (
    reminder_id TEXT PRIMARY KEY REFERENCES reminders(id) ON DELETE CASCADE,
    fired_at    TEXT NOT NULL
);

-- machine-written state only (widget_x, widget_y, last_synced_at);
-- user preferences live only in user-settings.json
CREATE TABLE IF NOT EXISTS app_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

MIGRATION_V2_SQL = """
-- Code tab items (snippets, commands, syntax, DSA problems)
CREATE TABLE IF NOT EXISTS code_items (
    id         TEXT PRIMARY KEY,
    category   TEXT NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL DEFAULT '',
    language   TEXT DEFAULT 'python',
    difficulty TEXT DEFAULT 'Easy',
    is_done    INTEGER NOT NULL DEFAULT 0,
    url        TEXT DEFAULT '',
    notes      TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_code_items_cat
    ON code_items(category) WHERE is_deleted = 0;

-- Courses tab tracker
CREATE TABLE IF NOT EXISTS courses (
    id                TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    platform          TEXT DEFAULT 'Coursera',
    instructor        TEXT DEFAULT '',
    total_modules     INTEGER NOT NULL DEFAULT 10,
    completed_modules INTEGER NOT NULL DEFAULT 0,
    url               TEXT DEFAULT '',
    notes             TEXT DEFAULT '',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    synced_at         TEXT,
    is_deleted        INTEGER NOT NULL DEFAULT 0
);

-- Ideas and Doubts tab items
CREATE TABLE IF NOT EXISTS ideas_doubts (
    id                TEXT PRIMARY KEY,
    kind              TEXT NOT NULL,
    title             TEXT NOT NULL,
    description       TEXT DEFAULT '',
    tech_stack_or_ref TEXT DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'Idea',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    synced_at         TEXT,
    is_deleted        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ideas_doubts_kind
    ON ideas_doubts(kind, status) WHERE is_deleted = 0;

-- Opportunities tab items (internships, jobs, hackathons)
CREATE TABLE IF NOT EXISTS opportunities (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    organization TEXT NOT NULL,
    kind         TEXT NOT NULL DEFAULT 'Internship',
    url          TEXT DEFAULT '',
    deadline     TEXT DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'Saved',
    notes        TEXT DEFAULT '',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    synced_at    TEXT,
    is_deleted   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_opportunities_kind
    ON opportunities(kind, status) WHERE is_deleted = 0;

-- Quick Links launcher
CREATE TABLE IF NOT EXISTS quick_links (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    target_uri  TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'Web',
    click_count INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    synced_at   TEXT,
    is_deleted  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_quick_links_cat
    ON quick_links(category) WHERE is_deleted = 0;
"""


def seed_demo_workspace_data(conn: sqlite3.Connection) -> None:
    """Seed initial sample data for all workspace tabs if empty."""
    now = datetime.now(UTC).isoformat()

    # Code items
    cur = conn.execute("SELECT COUNT(*) FROM code_items WHERE is_deleted = 0;")
    if cur.fetchone()[0] == 0:
        demo_code = [
            (
                uuid.uuid4().hex,
                "Snippets",
                "Python Atomic File Write",
                (
                    "import os, tempfile\n"
                    "with tempfile.NamedTemporaryFile("
                    "'w', dir='.', delete=False) as f:\n"
                    "    f.write(data)\n"
                    "    tmp_name = f.name\n"
                    "os.replace(tmp_name, target_file)"
                ),
                "python",
                "Easy",
                0,
                "",
                "Atomic file write prevents corruption on power loss.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CLI Commands",
                "Kill Process on TCP Port",
                "lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9",
                "bash",
                "Easy",
                0,
                "",
                "One-liner to terminate zombie dev servers.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Syntax Reference",
                "SQLite WAL & Pragmas",
                (
                    "PRAGMA journal_mode = WAL;\n"
                    "PRAGMA foreign_keys = ON;\n"
                    "PRAGMA busy_timeout = 5000;"
                ),
                "sql",
                "Easy",
                0,
                "",
                "Concurrency and integrity defaults for SQLite.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Two Sum (LeetCode #1)",
                (
                    "class Solution:\n"
                    "    def twoSum(self, nums: list[int], "
                    "target: int) -> list[int]:\n"
                    "        seen = {}\n"
                    "        for i, n in enumerate(nums):\n"
                    "            if target - n in seen:\n"
                    "                return [seen[target - n], i]\n"
                    "            seen[n] = i"
                ),
                "python",
                "Easy",
                1,
                "https://leetcode.com/problems/two-sum/",
                "Single-pass hash table with O(n) time and O(n) space.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Course Schedule (LeetCode #207)",
                "# Topological sort with Kahn's algorithm or DFS cycle check",
                "python",
                "Medium",
                0,
                "https://leetcode.com/problems/course-schedule/",
                "Directed graph cycle check for prerequisites.",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO code_items ("
                "id, category, title, content, language, difficulty, is_done, "
                "url, notes, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_code,
            )

    # Courses
    cur = conn.execute("SELECT COUNT(*) FROM courses WHERE is_deleted = 0;")
    if cur.fetchone()[0] == 0:
        demo_courses = [
            (
                uuid.uuid4().hex,
                "Operating Systems: Three Easy Pieces (OSTEP)",
                "University",
                "Remzi Arpaci-Dusseau",
                12,
                8,
                "https://pages.cs.wisc.edu/~remzi/OSTEP/",
                "Virtualization, Concurrency, and Persistence.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Database Management Systems & Transactions",
                "NPTEL",
                "Prof. Partha Pratim Das",
                10,
                6,
                "https://nptel.ac.in",
                "Relational algebra, B+ Trees, ACID, WAL logging.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Modern Python Software Architecture",
                "Self-Paced",
                "ArjanCodes",
                8,
                5,
                "https://docs.python.org/3/",
                "Clean architecture, SOLID principles, testing with pytest.",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO courses ("
                "id, title, platform, instructor, total_modules, "
                "completed_modules, url, notes, created_at, updated_at, "
                "is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_courses,
            )

    # Ideas & Doubts
    cur = conn.execute(
        "SELECT COUNT(*) FROM ideas_doubts WHERE is_deleted = 0;"
    )
    if cur.fetchone()[0] == 0:
        demo_ideas = [
            (
                uuid.uuid4().hex,
                "Idea",
                "Real-time Top-bar System Monitor Plasmoid",
                "Minimal floating Linux desktop widget reading /proc/stat.",
                "Python, /proc, Wayland",
                "In Progress",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Idea",
                "SQLite Vector Search Extension",
                "Embeddings index inside standard sqlite3 with SIMD.",
                "C, SQLite, SIMD",
                "Idea",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Doubt",
                "Why Tkinter on XWayland falls back to fixed bitmap font?",
                "Tkinter font lookup fails silently on missing font names.",
                "XWayland, fontconfig, Tk",
                "Resolved",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Doubt",
                "How does WAL mode handle checkpointing under read loads?",
                (
                    "Active readers lock earlier WAL frames until transactions"
                    " commit."
                ),
                "SQLite WAL",
                "Open",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO ideas_doubts ("
                "id, kind, title, description, tech_stack_or_ref, status, "
                "created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_ideas,
            )

    # Opportunities
    cur = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE is_deleted = 0;"
    )
    if cur.fetchone()[0] == 0:
        demo_opps = [
            (
                uuid.uuid4().hex,
                "Google Summer of Code 2026",
                "Google Open Source",
                "Internship",
                "https://summerofcode.withgoogle.com",
                "2026-11-15",
                "Applied",
                "Submitted project proposal on open source system tooling.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Smart India Hackathon (SIH) 2026",
                "Ministry of Education",
                "Hackathon",
                "https://sih.gov.in",
                "2026-12-01",
                "Saved",
                "Hardware & Software edition student innovation challenge.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Systems Software Engineering Intern",
                "Red Hat Linux",
                "Internship",
                "https://redhat.com/jobs",
                "2026-11-30",
                "In Progress",
                "Interview round 1 scheduled for next week.",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO opportunities ("
                "id, title, organization, kind, url, deadline, status, "
                "notes, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_opps,
            )

    # Quick Links
    cur = conn.execute("SELECT COUNT(*) FROM quick_links WHERE is_deleted = 0;")
    if cur.fetchone()[0] == 0:
        demo_links = [
            (
                uuid.uuid4().hex,
                "GitHub Dashboard",
                "https://github.com",
                "Web",
                14,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Project Workspace Directory",
                str(config.get_data_dir()),
                "Local Folder",
                22,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "LeetCode Problem Set",
                "https://leetcode.com/problemset/all/",
                "Web",
                9,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Python Official Docs",
                "https://docs.python.org/3/",
                "Web",
                18,
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO quick_links ("
                "id, name, target_uri, category, click_count, created_at, "
                "updated_at, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                demo_links,
            )

    # Categories & Tasks
    cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted = 0;")
    if cur.fetchone()[0] == 0:
        cat_cur = conn.execute(
            "SELECT id FROM categories WHERE name = 'College' "
            "AND is_deleted = 0;"
        )
        cat_row = cat_cur.fetchone()
        if not cat_row:
            cat_id = uuid.uuid4().hex
            with transaction(conn) as c:
                c.execute(
                    "INSERT INTO categories ("
                    "id, name, color, created_at, updated_at, is_deleted) "
                    "VALUES (?, 'College', '#00e5ff', ?, ?, 0);",
                    (cat_id, now, now),
                )
        else:
            cat_id = cat_row[0]

        demo_tasks = [
            (
                uuid.uuid4().hex,
                cat_id,
                "OS Lab Concurrency Semaphore Assignment",
                "Implement reader-writer lock using POSIX semaphores.",
                "2026-10-25",
                "Pending",
                "College",
                "High",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                cat_id,
                "DBMS B+ Tree Index Optimization",
                "Analyze query plans and write benchmark script.",
                "2026-10-30",
                "In Progress",
                "College",
                "Medium",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO tasks (id, category_id, title, description, "
                "due_date, status, task_label, critical_level, pace_level, "
                "is_google_task, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_tasks,
            )


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Create and configure a connection to the SQLite database.

    Enforces:
    - Foreign keys enabled.
    - Write-Ahead Logging (WAL) journal mode.
    - Busy timeout for concurrency resilience.
    - Row factory returning dict-accessible rows.
    """
    path = db_path or config.get_db_path()
    config.get_data_dir()  # Ensure data directory exists with mode 0o700

    conn = sqlite3.connect(path, timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


@contextlib.contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    """Context manager for ACID transactions.

    Executes a block of operations atomically:
    - Commits automatically if the block finishes without error.
    - Rolls back immediately on any unhandled exception.
    """
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction rolled back due to error: %s", exc)
        raise


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return current PRAGMA user_version from SQLite database."""
    cur = conn.execute("PRAGMA user_version;")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Set PRAGMA user_version on SQLite database."""
    conn.execute(f"PRAGMA user_version = {int(version)};")


def init_db(db_path: Path | None = None) -> None:
    """Run pending database schema migrations incrementally."""
    conn = get_connection(db_path)
    try:
        current_version = get_schema_version(conn)
        logger.info("Current SQLite database version: %d", current_version)

        if current_version < 1:
            logger.info("Applying Migration 1 (core schema)...")
            with transaction(conn) as cur:
                cur.executescript(MIGRATION_V1_SQL)
            set_schema_version(conn, 1)
            logger.info("Database migrated successfully to version 1.")

        if current_version < 2:
            logger.info("Applying Migration 2 (workspace tabs)...")
            with transaction(conn) as cur:
                cur.executescript(MIGRATION_V2_SQL)
            set_schema_version(conn, 2)
            logger.info("Database migrated successfully to version 2.")

    finally:
        conn.close()
