"""Core foundation package for PLUS-ULTRA."""

from __future__ import annotations

from typing import Any

from plus_ultra.core.events import (
    AppEvent,
    EventBus,
    NotificationPostedEvent,
    ReminderDueEvent,
    SettingsChangedEvent,
    TrayActionEvent,
)
from plus_ultra.core.exceptions import (
    LifecycleError,
    NotificationError,
    PlatformError,
    PlusUltraError,
    SettingsError,
    SingleInstanceError,
    StorageError,
    TrayError,
    UnsupportedPlatformError,
)
from plus_ultra.core.lifecycle import (
    LifecycleManager,
    LifecycleState,
)


def __getattr__(name: str) -> Any:
    if name == "Application":
        from plus_ultra.core.application import Application

        return Application
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AppEvent",
    "Application",
    "EventBus",
    "LifecycleError",
    "LifecycleManager",
    "LifecycleState",
    "NotificationError",
    "NotificationPostedEvent",
    "PlatformError",
    "PlusUltraError",
    "ReminderDueEvent",
    "SettingsChangedEvent",
    "SettingsError",
    "SingleInstanceError",
    "StorageError",
    "TrayActionEvent",
    "TrayError",
    "UnsupportedPlatformError",
]
