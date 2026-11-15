"""Date and time parsing utilities for PLUS-ULTRA (Facade).

Re-exports parse_flexible_datetime from plus_ultra.utils.datetime_utils
for backward compatibility.
"""

from __future__ import annotations

from plus_ultra.utils.datetime_utils import parse_flexible_datetime

__all__ = [
    "parse_flexible_datetime",
]
