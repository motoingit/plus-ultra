"""Notification state management and width calculation for PLUS-ULTRA capsule.

Applies architectural separation:
- Zero Tkinter imports: pure Python data structures for state and layout sizing.
- Center-outward expansion calculation with configurable min and max bounds.
- Multi-notification queueing, badge count calculation, and text truncation.
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
    action_label: str = "View"
    dismissable: bool = True
    created_at: str = ""


class CapsuleNotificationQueue:
    """Manages unread notifications and computes dynamic capsule dimensions."""

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
        action_label: str = "View",
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
            action_label=action_label,
            created_at=_now_utc(),
        )
        # If already exists with same ID, replace it; else append
        for idx, existing in enumerate(self._items):
            if existing.id == item_id:
                self._items[idx] = item
                return item

        self._items.append(item)
        return item

    def dismiss(self, notification_id: str) -> CapsuleNotification | None:
        """Dismiss a specific notification by ID."""
        for idx, item in enumerate(self._items):
            if item.id == notification_id:
                return self._items.pop(idx)
        return None

    def dismiss_current(self) -> CapsuleNotification | None:
        """Dismiss the currently visible top notification."""
        if self._items:
            return self._items.pop(0)
        return None

    def peek(self) -> CapsuleNotification | None:
        """Return the current top notification without removing it."""
        return self._items[0] if self._items else None

    def clear(self) -> None:
        """Clear all active notifications."""
        self._items.clear()

    @property
    def count(self) -> int:
        """Return the number of unread notifications in the queue."""
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        """Return True if there are no unread notifications."""
        return len(self._items) == 0

    def compute_target_width(self) -> int:
        """Compute required capsule width for the current notification state.

        Clamps result between min_width (idle) and max_width.
        """
        top = self.peek()
        if not top:
            return self.min_width

        # Base layout elements:
        # - Left end semicircle + padding: 32px
        # - Icon width: 20px
        # - Space between icon and text: 8px
        # - Text content (title + preview message)
        # - Badge width if multiple notifications: 28px
        # - Dismiss button width ('✕'): 24px
        # - Right end semicircle + padding: 32px
        fixed_chrome = 32 + 20 + 8 + 24 + 32
        if self.count > 1:
            fixed_chrome += 28

        text_len = len(top.title)
        if top.message:
            text_len += len(top.message) + 3  # " - " separator

        estimated_text_width = text_len * self.char_width_px
        total_width = fixed_chrome + estimated_text_width
        return max(self.min_width, min(self.max_width, total_width))

    def format_display_text(self, available_text_width_px: int) -> str:
        """Format and truncate title and message to fit the available space."""
        top = self.peek()
        if not top:
            return "PLUS-ULTRA"

        max_chars = max(10, available_text_width_px // self.char_width_px)
        full_text = top.title
        if top.message:
            full_text = f"{top.title} - {top.message}"

        if len(full_text) <= max_chars:
            return full_text
        return full_text[: max_chars - 1].rstrip() + "…"
