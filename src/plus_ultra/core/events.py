"""Typed event bus and domain events for PLUS-ULTRA.

Applies OS and Software Architecture concepts:
- Event-Driven Architecture: Decouples background services from GUI components.
- Thread Safety: Events emitted from worker threads are safely dispatched.
"""

from __future__ import annotations

import collections
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class AppEvent:
    """Base immutable application event."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class ReminderDueEvent(AppEvent):
    """Fired when a task reminder reaches its scheduled trigger time."""

    task_id: str = ""
    task_title: str = ""
    task_description: str = ""
    critical_level: str = "normal"
    reminder_id: str = ""


@dataclass(frozen=True, slots=True)
class NotificationPostedEvent(AppEvent):
    """Fired when a new user notification is created."""

    notification_id: str = ""
    title: str = ""
    message: str = ""
    urgency: str = "normal"


@dataclass(frozen=True, slots=True)
class SettingsChangedEvent(AppEvent):
    """Fired when user settings are updated."""

    changed_keys: tuple[str, ...] = ()
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrayActionEvent(AppEvent):
    """Fired when the user selects a system-tray menu item."""

    action: str = ""


class EventBus:
    """Thread-safe event dispatcher with sync and queued delivery."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Any], None]]] = (
            collections.defaultdict(list)
        )
        self._lock = threading.RLock()

    def subscribe(
        self, event_type: type[T], handler: Callable[[T], None]
    ) -> Callable[[], None]:
        """Register a handler for a specific event type.

        Returns:
            A parameterless unsubscribe function.
        """
        with self._lock:
            self._subscribers[event_type].append(handler)

        def _unsubscribe() -> None:
            with self._lock:
                if handler in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(handler)

        return _unsubscribe

    def publish(self, event: AppEvent) -> None:
        """Publish an event to all registered subscribers."""
        event_cls = type(event)
        with self._lock:
            handlers = list(self._subscribers.get(event_cls, []))
            generic_handlers = list(self._subscribers.get(AppEvent, []))

        for handler in handlers + generic_handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.error(
                    "Error executing event handler %s for %s: %s",
                    handler,
                    event_cls.__name__,
                    exc,
                    exc_info=True,
                )
