"""Main application entry point for PLUS-ULTRA.

Applies OS concepts:
- Mutual Exclusion & Single Instance: PlatformServices advisory file locking.
- Process Lifecycle: Signal handling (SIGINT, SIGTERM) and deterministic shutdown.
- Standardized logging to persistent storage in platform state directory.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from plus_ultra.config import (
    APP_NAME,
    get_log_path,
    get_metadata,
)
from plus_ultra.core.application import Application

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

    # File handler (persistent record in state directory)
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
    configure_logging()

    app = Application()
    is_pytest = "PYTEST_CURRENT_TEST" in os.environ and not args.smoke_test
    no_ui = args.no_ui or is_pytest

    success = app.initialize(
        seed_data=args.seed,
        no_ui=no_ui,
        smoke_test=args.smoke_test,
    )

    if not success:
        print("PLUS-ULTRA is already running.")
        return 0

    if no_ui:
        app.shutdown()
        return 0

    if args.smoke_test:
        logger.info("Running in smoke-test mode; verifying scheduler and UI.")
        if app.scheduler:
            app.scheduler.tick()
        if app.dashboard:
            app.dashboard.show()
        if app.widget and app.widget.root:
            app.widget.root.after(500, app.shutdown)

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
