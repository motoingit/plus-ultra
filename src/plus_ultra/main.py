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
from plus_ultra.desktop import SingleInstanceLock
from plus_ultra.ui.floating import FloatingWidget

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

    app_logger = logging.getLogger(APP_NAME)
    app_logger.setLevel(logging.INFO)
    app_logger.handlers.clear()

    # File handler (persistent record in XDG state directory)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    # Console stream handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

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
        if args.no_ui or (
            "PYTEST_CURRENT_TEST" in os.environ and not args.smoke_test
        ):
            return 0

        widget = FloatingWidget()

        def _signal_handler(_sig: int, _frame: object) -> None:
            logger.info("Received termination signal, shutting down.")
            widget.close()

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        if args.smoke_test:
            logger.info("Running in smoke-test mode; exiting in 500ms.")
            widget.root.after(500, widget.close)

        widget.run()
        return 0
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
