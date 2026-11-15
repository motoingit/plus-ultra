"""Date and time parsing utilities for PLUS-ULTRA."""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_flexible_datetime(val: str | datetime) -> datetime:
    """Parse a datetime string in common formats into timezone-aware datetime.

    Supports:
    - ISO 8601 with Z ("2026-10-17T09:30:00Z")
    - ISO 8601 with offset ("2026-10-17T09:30:00+05:30")
    - ISO 8601 naive ("2026-10-17T09:30:00") -> localized
    - Space-separated local ("2026-10-17 09:30", "2026-10-17 09:30:00")
    - Date only ("2026-10-17") -> localized to 00:00:00
    """
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.astimezone()
        return val

    clean = val.strip()
    if not clean:
        raise ValueError("Empty datetime string")

    # Replace Z with UTC offset for standard fromisoformat
    iso_clean = clean.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            return dt.astimezone()
        return dt
    except Exception:
        pass

    # Try common local formats
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(clean, fmt)
            return dt.astimezone()
        except ValueError:
            continue

    logger.warning("Unrecognized datetime format '%s'; fallback to now", val)
    return datetime.now().astimezone()
