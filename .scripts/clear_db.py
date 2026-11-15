"""Database clearing utility for PLUS-ULTRA development and testing.

Provides CLI options to clear domain tables (hard DELETE or soft delete),
clear runtime machine state, and run VACUUM.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import Any

# Ensure 'src' is in sys.path when executed directly
_src_dir = Path(__file__).resolve().parents[1] / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from sqlalchemy import (  # noqa: E402
    create_engine,
    delete,
    func,
    select,
    text,
    update,
)
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from plus_ultra.infrastructure.persistence.database_factory import (  # noqa: E402
    DatabaseFactory,
)
from plus_ultra.infrastructure.persistence.sqlalchemy.models import (  # noqa: E402
    AppStateModel,
    CategoryModel,
    CodeItemModel,
    CourseModel,
    IdeaDoubtModel,
    OpportunityModel,
    QuickLinkModel,
    ReminderFireModel,
    ReminderModel,
    TaskModel,
)

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

_TABLE_MODEL_MAP: dict[str, Any] = {
    "reminder_fires": ReminderFireModel,
    "reminders": ReminderModel,
    "tasks": TaskModel,
    "categories": CategoryModel,
    "app_state": AppStateModel,
    "code_items": CodeItemModel,
    "courses": CourseModel,
    "ideas_doubts": IdeaDoubtModel,
    "opportunities": OpportunityModel,
    "quick_links": QuickLinkModel,
}


def clear_database(
    conn: Any | None = None,
    tables: list[str] | None = None,
    hard_delete: bool = True,
    clear_app_state: bool = False,
    vacuum: bool = False,
) -> dict[str, int]:
    """Clear specified or all domain tables in database using SQLAlchemy.

    Args:
        conn: Active Session or Connection.
        tables: List of table names to clear. Defaults to ALL_DOMAIN_TABLES.
        hard_delete: If True, execute DELETE FROM table; if False,
          soft-delete by setting is_deleted = 1.
        clear_app_state: If True, also clear app_state table.
        vacuum: If True, execute VACUUM after clearing.

    Returns:
        Mapping of table name to count of modified rows.
    """
    if isinstance(conn, Session):
        session = conn
        close_session = False
    elif hasattr(conn, "cursor") and not hasattr(conn, "scalars"):
        eng = create_engine(
            "sqlite://",
            creator=lambda: conn,
            poolclass=StaticPool,
            pool_reset_on_return=None,
        )
        session = Session(eng)
        close_session = True
    else:
        factory = DatabaseFactory()
        session = factory.create_session()
        close_session = True

    target_tables = (
        list(tables) if tables is not None else list(ALL_DOMAIN_TABLES)
    )
    if clear_app_state and "app_state" not in target_tables:
        target_tables.append("app_state")

    counts: dict[str, int] = {}

    try:
        # Order tables to respect foreign keys during deletion
        deletion_order = [
            "reminder_fires",
            "reminders",
            "tasks",
            "categories",
            "app_state",
            "code_items",
            "courses",
            "ideas_doubts",
            "opportunities",
            "quick_links",
        ]
        ordered_targets = [t for t in deletion_order if t in target_tables]
        for t in target_tables:
            if t not in ordered_targets:
                ordered_targets.append(t)

        for tbl in ordered_targets:
            model = _TABLE_MODEL_MAP.get(tbl)
            if model is None:
                continue

            if tbl == "app_state" or hard_delete:
                count_stmt = select(func.count()).select_from(model)
                cnt = session.scalar(count_stmt) or 0
                session.execute(delete(model))
                counts[tbl] = cnt
            else:
                count_stmt = (
                    select(func.count())
                    .select_from(model)
                    .where(model.is_deleted == 0)
                )
                cnt = session.scalar(count_stmt) or 0
                session.execute(
                    update(model)
                    .where(model.is_deleted == 0)
                    .values(is_deleted=1)
                )
                counts[tbl] = cnt

        session.commit()

        if vacuum:
            with contextlib.suppress(Exception):
                session.execute(text("VACUUM;"))

        return counts
    except Exception:
        session.rollback()
        raise
    finally:
        if close_session:
            session.close()


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

    factory = DatabaseFactory()
    session = factory.create_session()
    try:
        results = clear_database(
            conn=session,
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
        session.close()


if __name__ == "__main__":
    sys.exit(main())
