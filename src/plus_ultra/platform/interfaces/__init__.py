"""Platform abstraction interfaces for PLUS-ULTRA."""

from __future__ import annotations

from plus_ultra.platform.interfaces.instance import SingleInstanceLock
from plus_ultra.platform.interfaces.notifications import (
    DesktopNotifier,
    NotificationRequest,
    NotificationUrgency,
)
from plus_ultra.platform.interfaces.paths import PathProvider
from plus_ultra.platform.interfaces.process import ProcessManager
from plus_ultra.platform.interfaces.startup import StartupManager
from plus_ultra.platform.interfaces.tray import SystemTray, TrayMenuItem
from plus_ultra.platform.interfaces.window import WindowEffects

__all__ = [
    "DesktopNotifier",
    "NotificationRequest",
    "NotificationUrgency",
    "PathProvider",
    "ProcessManager",
    "SingleInstanceLock",
    "StartupManager",
    "SystemTray",
    "TrayMenuItem",
    "WindowEffects",
]
