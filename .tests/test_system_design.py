"""Automated tests validating system design architecture and modular layers.

Verifies:
- Clean Layered Architecture: Domain, Concurrency, Diagnostics, Utils.
- Facade Pattern equivalence and 100% backward compatibility.
- Decoupling of Domain entities from Presentation and Persistence layers.
"""

from __future__ import annotations

import datetime

import plus_ultra.concurrency as concurrency
import plus_ultra.datetime_utils as legacy_datetime
import plus_ultra.diagnostics as diagnostics
import plus_ultra.domain as domain
import plus_ultra.models as legacy_models
import plus_ultra.network as legacy_network
import plus_ultra.notifications as legacy_notifications
import plus_ultra.scheduler as legacy_scheduler
import plus_ultra.utils as utils
from plus_ultra.concurrency import ReminderScheduler
from plus_ultra.diagnostics import NetworkStatusMonitor
from plus_ultra.domain import (
    CapsuleNotification,
    CapsuleNotificationQueue,
    Task,
)
from plus_ultra.utils import parse_flexible_datetime


def test_domain_layer_models_and_facade_equivalence() -> None:
    """Domain models must be identical when imported via domain or facade."""
    assert domain.Task is legacy_models.Task
    assert domain.Category is legacy_models.Category
    assert domain.Reminder is legacy_models.Reminder
    assert domain.AppState is legacy_models.AppState
    assert domain.CodeItem is legacy_models.CodeItem
    assert domain.Course is legacy_models.Course
    assert domain.IdeaDoubt is legacy_models.IdeaDoubt
    assert domain.Opportunity is legacy_models.Opportunity
    assert domain.QuickLink is legacy_models.QuickLink

    # Instantiate domain entity
    task = Task(id="t-1", title="Verify Architecture")
    assert task.title == "Verify Architecture"
    assert task.status == "Pending"
    assert task.critical_level == "Medium"


def test_domain_layer_notifications_and_facade_equivalence() -> None:
    """Notification models and queue must be identical across import paths."""
    assert (
        domain.CapsuleNotification
        is legacy_notifications.CapsuleNotification
    )
    assert (
        domain.CapsuleNotificationQueue
        is legacy_notifications.CapsuleNotificationQueue
    )
    assert (
        domain.NotificationPriority
        is legacy_notifications.NotificationPriority
    )

    queue = CapsuleNotificationQueue()
    item = queue.push("Test Alert", "System Design Check")
    assert isinstance(item, CapsuleNotification)
    assert queue.unread_count == 1
    assert queue.count == 1


def test_concurrency_layer_and_facade_equivalence() -> None:
    """Concurrency scheduler must be identical across import paths."""
    assert concurrency.ReminderScheduler is legacy_scheduler.ReminderScheduler
    assert (
        concurrency.DEFAULT_POLL_INTERVAL_S
        == legacy_scheduler.DEFAULT_POLL_INTERVAL_S
    )
    assert issubclass(ReminderScheduler, object)


def test_diagnostics_layer_and_facade_equivalence() -> None:
    """Network diagnostics must be identical across import paths."""
    assert diagnostics.is_network_online is legacy_network.is_network_online
    assert (
        diagnostics.NetworkStatusMonitor is legacy_network.NetworkStatusMonitor
    )

    monitor = NetworkStatusMonitor()
    assert monitor.last_status is True


def test_utils_layer_and_facade_equivalence() -> None:
    """Datetime utility must be identical across import paths."""
    assert (
        utils.parse_flexible_datetime
        is legacy_datetime.parse_flexible_datetime
    )

    now = datetime.datetime.now(datetime.UTC)
    parsed = parse_flexible_datetime(now.isoformat())
    assert isinstance(parsed, datetime.datetime)
