"""Desktop notification dispatch interface and data contracts.

Applies OS concepts:
- Asynchronous IPC: Dispatching user notifications to the host notification
  daemon (FreeDesktop notify-send / D-Bus on Linux, Windows Notification Area).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


class NotificationUrgency(str, enum.Enum):
    """Urgency level for desktop notifications."""

    LOW = "low"
    NORMAL = "normal"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class NotificationRequest:
    """Immutable data contract for dispatching an OS desktop notification."""

    title: str
    message: str = ""
    urgency: NotificationUrgency = NotificationUrgency.NORMAL
    timeout_ms: int = 3000
    app_name: str = "plus-ultra"
    icon_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class DesktopNotifier(Protocol):
    """Protocol for platform desktop notification providers."""

    @property
    def is_available(self) -> bool:
        """Return True if notifications are supported and available."""
        ...

    def send(self, request: NotificationRequest) -> bool:
        """Dispatch a notification to the host operating system.

        Returns:
            True if dispatched successfully, False otherwise.
        """
        ...
