"""Initial demo dataset for workspace modules and tasks."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime

from plus_ultra import config
from plus_ultra.database.connection import transaction


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
