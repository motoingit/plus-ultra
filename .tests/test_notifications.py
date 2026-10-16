"""Unit tests for notification queue, read/unread states, and popup formatting.

Validates:
- Pure data structure isolation (zero Tkinter dependencies).
- Read/unread status tracking (unread_count, has_unread, mark_all_read).
- Popup width computation and text truncation.
"""

from __future__ import annotations

from plus_ultra.notifications import CapsuleNotificationQueue


def test_notification_queue_idle_defaults() -> None:
    """Verify queue starts empty and reports zero unread."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)
    assert queue.is_empty is True
    assert queue.count == 0
    assert queue.unread_count == 0
    assert queue.has_unread is False
    assert queue.peek() is None


def test_notification_push_and_unread_tracking() -> None:
    """Verify pushing notifications sets unread status and marks read."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)

    n1 = queue.push("System Alert", "Kernel updated", icon="⚡")
    assert queue.count == 1
    assert queue.unread_count == 1
    assert queue.has_unread is True
    assert n1.is_read is False

    # Mark single read
    queue.mark_read(n1.id)
    assert queue.unread_count == 0
    assert queue.has_unread is False
    assert n1.is_read is True


def test_notification_multiple_and_mark_all_read() -> None:
    """Verify multiple unread notifications and mark_all_read."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)

    queue.push("Task Due", "OS assignment due in 15m", icon="📅")
    queue.push("DSA Practice", "LeetCode daily challenge ready", icon="💻")

    assert queue.count == 2
    assert queue.unread_count == 2
    assert queue.has_unread is True

    queue.mark_all_read()
    assert queue.unread_count == 0
    assert queue.has_unread is False


def test_popup_width_and_text_formatting() -> None:
    """Verify popup width calculation and preview text truncation."""
    queue = CapsuleNotificationQueue()
    n = queue.push("Task 1", "Very detailed reminder text")

    w = queue.compute_popup_width(n)
    assert 200 <= w <= 360

    formatted = queue.format_popup_text(n, max_chars=20)
    assert formatted.endswith("…")
    assert len(formatted) <= 20


def test_notification_queue_update_existing_id() -> None:
    """Verify pushing with existing ID replaces content in-place."""
    queue = CapsuleNotificationQueue(min_width=160, max_width=440)
    queue.push("Old Title", notification_id="fixed_id")
    queue.push("Updated Title", notification_id="fixed_id")

    assert queue.count == 1
    assert queue.peek().title == "Updated Title"


def test_notification_queue_dismiss_and_clear() -> None:
    """Verify dismiss by ID and clear resets all notifications."""
    queue = CapsuleNotificationQueue()
    n1 = queue.push("Msg 1")
    queue.push("Msg 2")
    assert queue.count == 2

    dismissed = queue.dismiss(n1.id)
    assert dismissed == n1
    assert queue.count == 1

    queue.clear()
    assert queue.is_empty is True
    assert queue.count == 0
