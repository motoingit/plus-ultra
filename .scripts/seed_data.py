"""Demo dataset seeding and unseeding utility for PLUS-ULTRA workspace.

Lives in .scripts/ outside the primary package src tree.
Provides standalone CLI to populate or remove demo records across all tabs.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Ensure 'src' is in sys.path when executed directly
_src_dir = Path(__file__).resolve().parents[1] / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from plus_ultra import config  # noqa: E402
from plus_ultra.database.connection import (  # noqa: E402
    get_connection,
    transaction,
)

# Known signatures of seeded demo data for selective unseeding
DEMO_CODE_TITLES = [
    "Python Atomic File Write",
    "Kill Process on TCP Port",
    "SQLite WAL & Pragmas",
    "Two Sum (LeetCode #1)",
    "Course Schedule (LeetCode #207)",
]

DEMO_COURSE_TITLES = [
    "Operating Systems: Three Easy Pieces (OSTEP)",
    "Database Management Systems & Transactions",
    "Modern Python Software Architecture",
]

DEMO_IDEA_TITLES = [
    "Real-time Top-bar System Monitor Plasmoid",
    "SQLite Vector Search Extension",
    "Why Tkinter on XWayland falls back to fixed bitmap font?",
    "How does WAL mode handle checkpointing under read loads?",
]

DEMO_OPP_TITLES = [
    "Google Summer of Code 2026",
    "Smart India Hackathon (SIH) 2026",
    "Systems Software Engineering Intern",
]

DEMO_LINK_NAMES = [
    "GitHub Dashboard",
    "Project Workspace Directory",
    "LeetCode Problem Set",
    "Python Official Docs",
]

DEMO_TASK_TITLES = [
    "OS Lab Concurrency Semaphore Assignment",
    "DBMS B+ Tree Index Optimization",
]


def seed_demo_workspace_data(
    conn: sqlite3.Connection, force: bool = False
) -> dict[str, int]:
    """Seed initial sample data for all workspace tabs if empty or forced."""
    now = datetime.now(UTC).isoformat()
    seeded_counts: dict[str, int] = {}

    # 1. Code items
    cur = conn.execute("SELECT COUNT(*) FROM code_items WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
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
        seeded_counts["code_items"] = len(demo_code)

    # 2. Courses
    cur = conn.execute("SELECT COUNT(*) FROM courses WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
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
                "University Lab",
                "Prof. Partha Pratim Das",
                10,
                6,
                "https://example.edu/dbms",
                "Relational algebra, B+ Trees, ACID, WAL logging.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Modern Python Software Architecture",
                "Open Courseware",
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
        seeded_counts["courses"] = len(demo_courses)

    # 3. Ideas & Doubts
    cur = conn.execute(
        "SELECT COUNT(*) FROM ideas_doubts WHERE is_deleted = 0;"
    )
    if force or cur.fetchone()[0] == 0:
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
        seeded_counts["ideas_doubts"] = len(demo_ideas)

    # 4. Opportunities
    cur = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE is_deleted = 0;"
    )
    if force or cur.fetchone()[0] == 0:
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
        seeded_counts["opportunities"] = len(demo_opps)

    # 5. Quick Links
    cur = conn.execute("SELECT COUNT(*) FROM quick_links WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
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
        seeded_counts["quick_links"] = len(demo_links)

    # 6. Categories & Tasks
    cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
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
        seeded_counts["tasks"] = len(demo_tasks)

    return seeded_counts


def unseed_demo_workspace_data(
    conn: sqlite3.Connection, hard_delete: bool = True
) -> dict[str, int]:
    """Remove demo seeded records while preserving user-created entries."""
    unseeded_counts: dict[str, int] = {}

    def _execute_unseed(table: str, col: str, values: list[str]) -> int:
        placeholders = ",".join("?" for _ in values)
        query_sel = (
            f"SELECT COUNT(*) FROM {table} "  # noqa: S608
            f"WHERE {col} IN ({placeholders});"
        )
        with transaction(conn) as cur:
            cur.execute(query_sel, values)
            cnt = cur.fetchone()[0]
            if cnt > 0:
                if hard_delete:
                    query_del = (
                        f"DELETE FROM {table} "  # noqa: S608
                        f"WHERE {col} IN ({placeholders});"
                    )
                    cur.execute(query_del, values)
                else:
                    query_upd = (
                        f"UPDATE {table} SET is_deleted = 1 "  # noqa: S608
                        f"WHERE {col} IN ({placeholders});"
                    )
                    cur.execute(query_upd, values)
            return cnt

    # 1. Unseed demo tasks & cascade to their reminders
    with transaction(conn) as cur:
        q_marks = ",".join("?" for _ in DEMO_TASK_TITLES)
        cur.execute(
            f"SELECT id FROM tasks WHERE title IN ({q_marks});",  # noqa: S608
            DEMO_TASK_TITLES,
        )
        task_ids = [r[0] for r in cur.fetchall()]
        if task_ids:
            rem_marks = ",".join("?" for _ in task_ids)
            if hard_delete:
                cur.execute(
                    f"DELETE FROM reminders "  # noqa: S608
                    f"WHERE task_id IN ({rem_marks});",
                    task_ids,
                )
            else:
                cur.execute(
                    "UPDATE reminders SET is_deleted = 1 "
                    f"WHERE task_id IN ({rem_marks});",  # noqa: S608
                    task_ids,
                )

    unseeded_counts["tasks"] = _execute_unseed(
        "tasks", "title", DEMO_TASK_TITLES
    )
    unseeded_counts["code_items"] = _execute_unseed(
        "code_items", "title", DEMO_CODE_TITLES
    )
    unseeded_counts["courses"] = _execute_unseed(
        "courses", "title", DEMO_COURSE_TITLES
    )
    unseeded_counts["ideas_doubts"] = _execute_unseed(
        "ideas_doubts", "title", DEMO_IDEA_TITLES
    )
    unseeded_counts["opportunities"] = _execute_unseed(
        "opportunities", "title", DEMO_OPP_TITLES
    )
    unseeded_counts["quick_links"] = _execute_unseed(
        "quick_links", "name", DEMO_LINK_NAMES
    )

    return unseeded_counts


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for seed_data script."""
    parser = argparse.ArgumentParser(
        description=(
            "Seed or unseed demo dataset in PLUS-ULTRA SQLite database."
        )
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--seed",
        action="store_true",
        default=True,
        help="Seed demo records if tables are empty (default).",
    )
    group.add_argument(
        "--unseed",
        action="store_true",
        help="Remove all demo seeded records from the database.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-seeding even if tables are not empty.",
    )
    parser.add_argument(
        "--soft",
        action="store_true",
        help="During unseeding, soft-delete records instead of hard delete.",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    """CLI script entrypoint."""
    args = parse_args(argv)
    conn = get_connection()
    try:
        if args.unseed:
            print("Unseeding demo workspace data...")
            counts = unseed_demo_workspace_data(conn, hard_delete=not args.soft)
            print("Unseeding complete:")
            for tbl, cnt in counts.items():
                print(f"  - {tbl}: {cnt} demo records removed")
        else:
            print("Seeding demo workspace data...")
            counts = seed_demo_workspace_data(conn, force=args.force)
            if not counts:
                print("Tables already contained data (use --force to reseed).")
            else:
                print("Seeding complete:")
                for tbl, cnt in counts.items():
                    print(f"  - {tbl}: {cnt} demo records added")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
