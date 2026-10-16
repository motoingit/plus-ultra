"""Database clearing utility for PLUS-ULTRA development and testing.

Provides CLI options to clear domain tables (hard DELETE or soft delete),
clear runtime machine state, and run VACUUM.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Ensure 'src' is in sys.path when executed directly
_src_dir = Path(__file__).resolve().parents[1] / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from plus_ultra.database.connection import get_connection, transaction  # noqa: E402

ALL_DOMAIN_TABLES: list[str] = [
    "reminders",
    "tasks",
    "categories",
    "code_items",
    "courses",
    "ideas_doubts",
    "opportunities",
    "quick_links",
]


def clear_database(
    conn: sqlite3.Connection,
    tables: list[str] | None = None,
    hard_delete: bool = True,
    clear_app_state: bool = False,
    vacuum: bool = False,
) -> dict[str, int]:
    """Clear specified or all domain tables in SQLite database.

    Args:
        conn: Active SQLite connection.
        tables: List of table names to clear. Defaults to ALL_DOMAIN_TABLES.
        hard_delete: If True, execute DELETE FROM table; if False,
          soft-delete by setting is_deleted = 1.
        clear_app_state: If True, also clear app_state table.
        vacuum: If True, execute VACUUM after clearing.

    Returns:
        Mapping of table name to count of modified rows.
    """
    target_tables = list(tables or ALL_DOMAIN_TABLES)
    if clear_app_state and "app_state" not in target_tables:
        target_tables.append("app_state")

    counts: dict[str, int] = {}

    with transaction(conn) as cur:
        for tbl in target_tables:
            if tbl == "app_state":
                cur.execute("SELECT COUNT(*) FROM app_state;")
                row_cnt = cur.fetchone()[0]
                cur.execute("DELETE FROM app_state;")
                counts[tbl] = row_cnt
            elif hard_delete:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")  # noqa: S608
                row_cnt = cur.fetchone()[0]
                cur.execute(f"DELETE FROM {tbl};")  # noqa: S608
                counts[tbl] = row_cnt
            else:
                cur.execute(
                    f"SELECT COUNT(*) FROM {tbl} WHERE is_deleted = 0;"  # noqa: S608
                )
                row_cnt = cur.fetchone()[0]
                cur.execute(
                    f"UPDATE {tbl} SET is_deleted = 1 WHERE is_deleted = 0;"  # noqa: S608
                )
                counts[tbl] = row_cnt

    if vacuum:
        conn.execute("VACUUM;")

    return counts


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for clear_db script."""
    parser = argparse.ArgumentParser(
        description="Clear PLUS-ULTRA database tables for testing and resets."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clear all domain tables and categories.",
    )
    parser.add_argument(
        "--table",
        "-t",
        action="append",
        choices=ALL_DOMAIN_TABLES + ["app_state"],
        help="Specify individual table(s) to clear (repeatable).",
    )
    parser.add_argument(
        "--soft",
        action="store_true",
        help="Perform soft delete (is_deleted = 1) instead of hard delete.",
    )
    parser.add_argument(
        "--include-app-state",
        action="store_true",
        help="Also clear machine runtime state (app_state table).",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Run SQLite VACUUM after clearing records.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip interactive confirmation prompt.",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    """CLI script entrypoint."""
    args = parse_args(argv)

    tables_to_clear: list[str] = args.table or ALL_DOMAIN_TABLES
    mode_str = "SOFT DELETE" if args.soft else "HARD DELETE"

    if not args.force:
        print(f"Warning: About to {mode_str} data from: {tables_to_clear}")
        if args.include_app_state:
            print("Notice: 'app_state' table will also be cleared.")
        confirm = input("Are you sure you want to proceed? [y/N]: ").strip()
        if confirm.lower() not in ("y", "yes"):
            print("Aborted.")
            return 1

    conn = get_connection()
    try:
        results = clear_database(
            conn=conn,
            tables=tables_to_clear,
            hard_delete=not args.soft,
            clear_app_state=args.include_app_state,
            vacuum=args.vacuum,
        )
        print(f"Database cleared successfully ({mode_str}):")
        for tbl, count in results.items():
            print(f"  - {tbl}: {count} rows affected")
        if args.vacuum:
            print("  - VACUUM completed.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
