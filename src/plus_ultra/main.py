"""Main application entry point for PLUS-ULTRA.

Applies OS concepts:
- Standardized logging to persistent storage in the XDG state directory.
- Clean process lifecycle and exit status codes.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from plus_ultra.config import (
    APP_NAME,
    get_data_dir,
    get_log_path,
    get_state_dir,
)

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
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="PLUS-ULTRA: Floating desktop assistant for Ubuntu",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> None:
    """Main application routine."""
    _args = parse_args(argv)
    log_path = configure_logging()

    logger.info("PLUS-ULTRA initializing...")
    logger.info("Data directory: %s", get_data_dir())
    logger.info("State directory: %s", get_state_dir())
    logger.info("Log file: %s", log_path)
    logger.info("PLUS-ULTRA foundation initialized successfully.")


if __name__ == "__main__":
    main()
