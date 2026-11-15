"""Background reminder evaluation scheduler for PLUS-ULTRA (Facade).

Re-exports ReminderScheduler and constants from plus_ultra.concurrency.scheduler
for backward compatibility with legacy import paths.
"""

from __future__ import annotations

from plus_ultra.concurrency.scheduler import (
    DEFAULT_POLL_INTERVAL_S,
    ReminderScheduler,
)

__all__ = [
    "DEFAULT_POLL_INTERVAL_S",
    "ReminderScheduler",
]
