"""Notification state management for PLUS-ULTRA capsule.

Applies architectural separation:
- Zero Tkinter imports: pure Python data structures for state and sizing.
- Multi-notification queueing, read/unread state tracking.
- Popup notification text formatting and width calculation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


def _now_utc() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class CapsuleNotification:
    """Notification entity displayed in the dynamic capsule."""

    id: str
    title: str
    message: str = ""
    icon: str = "🔔"
    is_read: bool = False
    created_at: str = ""


class CapsuleNotificationQueue:
    """Manages unread notifications and computes dynamic dimensions."""

    def __init__(
        self,
        min_width: int = 160,
        max_width: int = 440,
        char_width_px: int = 7,
    ) -> None:
        self.min_width = min_width
        self.max_width = max_width
        self.char_width_px = char_width_px
        self._items: list[CapsuleNotification] = []

    def push(
        self,
        title: str,
        message: str = "",
        icon: str = "🔔",
        notification_id: str | None = None,
    ) -> CapsuleNotification:
        """Add or update an active notification in the queue."""
        clean_title = title.strip()
        item_id = notification_id or str(uuid.uuid4())
        item = CapsuleNotification(
            id=item_id,
            title=clean_title,
            message=message.strip(),
            icon=icon,
            is_read=False,
            created_at=_now_utc(),
        )
        # If already exists with same ID, replace it; else append to front
        for idx, existing in enumerate(self._items):
            if existing.id == item_id:
                self._items[idx] = item
                return item

        self._items.insert(0, item)
        return item

    def mark_read(self, notification_id: str) -> None:
        """Mark a specific notification as read."""
        for item in self._items:
            if item.id == notification_id:
                item.is_read = True

    def mark_all_read(self) -> None:
        """Mark all notifications as read."""
        for item in self._items:
            item.is_read = True

    def dismiss(self, notification_id: str) -> CapsuleNotification | None:
        """Dismiss and remove a notification by ID."""
        for idx, item in enumerate(self._items):
            if item.id == notification_id:
                return self._items.pop(idx)
        return None

    def peek(self) -> CapsuleNotification | None:
        """Return the most recent notification without removing it."""
        return self._items[0] if self._items else None

    def list_all(self) -> list[CapsuleNotification]:
        """Return a copy of all notifications."""
        return list(self._items)

    def clear(self) -> None:
        """Clear all notifications."""
        self._items.clear()

    @property
    def unread_count(self) -> int:
        """Return count of unread notifications."""
        return sum(1 for item in self._items if not item.is_read)

    @property
    def has_unread(self) -> bool:
        """Return True if at least one notification is unread."""
        return self.unread_count > 0

    @property
    def count(self) -> int:
        """Return total count of notifications."""
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        """Return True if there are no notifications."""
        return len(self._items) == 0

    def compute_popup_width(self, item: CapsuleNotification) -> int:
        """Compute required width for the 3-second popup capsule."""
        text = self.format_popup_text(item)
        content_len = len(text) + 6  # icon + padding
        estimated_w = 40 + (content_len * self.char_width_px)
        return max(200, min(360, estimated_w))

    def format_popup_text(
        self, item: CapsuleNotification, max_chars: int = 42
    ) -> str:
        """Format and truncate notification for the popup banner."""
        full_text = item.title
        if item.message:
            full_text = f"{item.title}: {item.message}"

        if len(full_text) <= max_chars:
            return full_text
        return full_text[: max_chars - 1].rstrip() + "…"
