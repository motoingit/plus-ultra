"""Unit tests for notification queue and dynamic capsule width calculations.

Validates:
- Pure data structure isolation (zero Tkinter dependencies).
- Single and multi-notification queue management.
- Dynamic width estimation clamped between min_width and max_width.
- Text truncation and badge indicator formatting.
"""

from __future__ import annotations

from plus_ultra.notifications import CapsuleNotificationQueue


def test_notification_queue_idle_defaults() -> None:
    """Verify queue starts empty and computes min_width."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)
    assert queue.is_empty is True
    assert queue.count == 0
    assert queue.peek() is None
    assert queue.compute_target_width() == 160
    assert queue.format_display_text(100) == "PLUS-ULTRA"


def test_notification_queue_push_and_dismiss() -> None:
    """Verify pushing notification expands width and dismissal shrinks."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)

    n1 = queue.push("System Alert", "Kernel updated", icon="⚡")
    assert queue.count == 1
    assert queue.is_empty is False
    assert queue.peek() == n1
    assert queue.compute_target_width() > 160

    # Dismiss specific notification
    dismissed = queue.dismiss(n1.id)
    assert dismissed == n1
    assert queue.is_empty is True
    assert queue.compute_target_width() == 160


def test_notification_queue_multiple_unread_and_dismiss_current() -> None:
    """Verify multiple notifications stack, report count, and dismiss top."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)

    queue.push("Task Due", "OS assignment due in 15m", icon="📅")
    queue.push("DSA Practice", "LeetCode daily challenge ready", icon="💻")

    assert queue.count == 2
    # Extra badge chrome added when count > 1
    w_multi = queue.compute_target_width()
    assert w_multi > 160

    # Dismiss top item
    top = queue.dismiss_current()
    assert top is not None
    assert top.title == "Task Due"
    assert queue.count == 1
    assert queue.peek().title == "DSA Practice"


def test_notification_text_truncation() -> None:
    """Verify long preview text is truncated with ellipsis."""
    queue = CapsuleNotificationQueue(
        min_width=160, max_width=440, char_width_px=7
    )
    long_msg = "A" * 150
    queue.push("Super Long Title", long_msg)

    # Available width for ~10 characters
    formatted = queue.format_display_text(available_text_width_px=70)
    assert formatted.endswith("…")
    assert len(formatted) <= 12


def test_notification_queue_update_existing_id() -> None:
    """Verify pushing with existing ID replaces content in-place."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)
    queue.push("Old Title", notification_id="fixed_id")
    queue.push("Updated Title", notification_id="fixed_id")

    assert queue.count == 1
    assert queue.peek().title == "Updated Title"


def test_notification_queue_clear() -> None:
    """Verify clear resets all notifications."""
    queue = CapsuleNotificationQueue()
    queue.push("Msg 1")
    queue.push("Msg 2")
    assert queue.count == 2

    queue.clear()
    assert queue.is_empty is True
    assert queue.count == 0
