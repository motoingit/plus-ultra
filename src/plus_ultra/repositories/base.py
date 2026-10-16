"""Common utilities and base functions for data repositories."""

from __future__ import annotations

from datetime import UTC, datetime


def _now_utc() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()
