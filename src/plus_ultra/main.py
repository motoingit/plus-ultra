"""Main application entry point for PLUS-ULTRA.

Applies OS concepts:
- Mutual Exclusion & Single Instance: Advisory locking (fcntl.flock).
- Process Lifecycle: Signal handling (SIGINT, SIGTERM) and clean shutdown.
- Standardized logging to persistent storage in the XDG state directory.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
from pathlib import Path

from plus_ultra.config import (
    APP_NAME,
    get_app_version,
    get_config_dir,
    get_data_dir,
    get_log_path,
    get_metadata,
    get_state_dir,
)
from plus_ultra.database import (
    get_connection,
    init_db,
    seed_demo_workspace_data,
)
from plus_ultra.desktop import SingleInstanceLock
from plus_ultra.models import Reminder, Task
from plus_ultra.repositories import (
    AppStateRepository,
    CategoryRepository,
    CodeRepository,
    CourseRepository,
    IdeaDoubtRepository,
    OpportunityRepository,
    QuickLinkRepository,
    ReminderRepository,
    TaskRepository,
)
from plus_ultra.scheduler import ReminderScheduler
from plus_ultra.services import (
    CategoryService,
    CodeService,
    CourseService,
    IdeaDoubtService,
    OpportunityService,
    QuickLinkService,
    ReminderService,
    TaskService,
)
from plus_ultra.ui.floating import FloatingWidget
from plus_ultra.ui.panel import DashboardPanel

logger = logging.getLogger(APP_NAME)


def configure_logging() -> Path:
    """Set up dual logging to console and launcher.log in state directory.

    Returns the path to the active log file.
    """
    log_file = get_log_path()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # File handler (persistent record in XDG state directory)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console stream handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    for name in ("plus_ultra", APP_NAME):
        lgr = logging.getLogger(name)
        lgr.setLevel(logging.INFO)

    return log_file


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    meta = get_metadata()
    parser = argparse.ArgumentParser(
        prog=meta.get("app_name", APP_NAME),
        description=(
            f"{meta.get('display_name', APP_NAME)}: "
            f"{meta.get('description', '')}"
        ),
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Initialize foundation and logging without starting GUI.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Launch floating widget, wait briefly, and exit cleanly.",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed or reseed demo workspace data from .scripts/seeds.py.",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    """Main application routine."""
    args = parse_args(argv)
    log_path = configure_logging()

    meta = get_metadata()
    version = get_app_version()
    logger.info("PLUS-ULTRA initializing...")
    logger.info(
        "Application: %s v%s (%s)",
        meta.get("display_name", APP_NAME),
        version,
        meta.get("company", ""),
    )
    logger.info("Data directory: %s", get_data_dir())
    logger.info("State directory: %s", get_state_dir())
    logger.info("Config directory: %s", get_config_dir())
    logger.info("Log file: %s", log_path)
    logger.info("PLUS-ULTRA foundation initialized successfully.")

    lock = SingleInstanceLock()
    if not lock.acquire():
        logger.warning("Another instance of PLUS-ULTRA is already running.")
        print("PLUS-ULTRA is already running.")
        return 0

    try:
        init_db()
        conn = get_connection()
        seed_demo_workspace_data(conn)

        app_state_repo = AppStateRepository(conn)
        task_repo = TaskRepository(conn)
        cat_repo = CategoryRepository(conn)
        rem_repo = ReminderRepository(conn)
        code_repo = CodeRepository(conn)
        course_repo = CourseRepository(conn)
        idea_repo = IdeaDoubtRepository(conn)
        opp_repo = OpportunityRepository(conn)
        link_repo = QuickLinkRepository(conn)

        task_service = TaskService(task_repo, cat_repo)
        cat_service = CategoryService(cat_repo)
        rem_service = ReminderService(rem_repo, task_repo)
        code_service = CodeService(code_repo)
        course_service = CourseService(course_repo)
        idea_service = IdeaDoubtService(idea_repo)
        opp_service = OpportunityService(opp_repo)
        link_service = QuickLinkService(link_repo)

        if args.no_ui or (
            "PYTEST_CURRENT_TEST" in os.environ and not args.smoke_test
        ):
            conn.close()
            return 0

        saved_pos = app_state_repo.get_widget_position()
        init_x = saved_pos[0] if saved_pos else None
        init_y = saved_pos[1] if saved_pos else None

        widget = FloatingWidget(
            initial_x=init_x,
            initial_y=init_y,
            on_position_change=app_state_repo.set_widget_position,
        )

        dashboard = DashboardPanel(
            parent=widget.root,
            task_service=task_service,
            category_service=cat_service,
            notification_queue=widget.notifications,
            reminder_service=rem_service,
            code_service=code_service,
            course_service=course_service,
            idea_doubt_service=idea_service,
            opportunity_service=opp_service,
            quick_link_service=link_service,
            on_notifications_cleared=widget._update_bell_state,
            on_open=widget.root.withdraw,
            on_close=widget.root.deiconify,
        )
        widget.on_click_callback = dashboard.toggle

        def _handle_reminder_due(task: Task, _rem: Reminder) -> None:
            """Safely enqueue reminder alert to Tkinter main thread."""
            logger.info(
                "Reminder triggered for task '%s' [id=%s]. Alerting UI.",
                task.title,
                task.id,
            )

            def _ui_action() -> None:
                if not widget._closed:
                    widget.post_notification(
                        title=f"Due: {task.title}",
                        message=task.description
                        or f"Priority: {task.critical_level}",
                    )
                    if dashboard.winfo_exists():
                        dashboard._refresh_tasks()
                        dashboard._refresh_notifications()

            widget.root.after_idle(_ui_action)

        scheduler = ReminderScheduler(
            reminder_service=rem_service,
            on_reminder_due=_handle_reminder_due,
            desktop_notify=True,
        )
        scheduler.start()

        def _signal_handler(_sig: int, _frame: object) -> None:
            logger.info("Received termination signal, shutting down.")
            scheduler.stop()
            if dashboard.winfo_exists():
                dashboard.destroy()
            widget.close()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        if args.smoke_test:
            logger.info(
                "Running in smoke-test mode; verifying scheduler and UI."
            )
            scheduler.tick()
            dashboard.show()
            widget.root.after(500, widget.close)

        try:
            widget.run()
        finally:
            scheduler.stop()
            conn.close()
        return 0
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
