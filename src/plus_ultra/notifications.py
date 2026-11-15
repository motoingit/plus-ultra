"""Notification state management for PLUS-ULTRA capsule (Facade).

Re-exports capsule notification entities and queue from
plus_ultra.domain.notifications for backward compatibility.
"""

from __future__ import annotations

from plus_ultra.domain.notifications import (
    CapsuleNotification,
    CapsuleNotificationQueue,
    NotificationPriority,
    _now_utc,
)

__all__ = [
    "CapsuleNotification",
    "CapsuleNotificationQueue",
    "NotificationPriority",
    "_now_utc",
]
