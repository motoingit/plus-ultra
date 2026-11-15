"""Linux platform backend package."""

from __future__ import annotations

from plus_ultra.platform.linux.instance import LinuxSingleInstanceLock
from plus_ultra.platform.linux.notifications import LinuxDesktopNotifier
from plus_ultra.platform.linux.paths import LinuxPathProvider
from plus_ultra.platform.linux.process import LinuxProcessManager
from plus_ultra.platform.linux.startup import LinuxStartupManager
from plus_ultra.platform.linux.tray import LinuxSystemTray
from plus_ultra.platform.linux.window import LinuxWindowEffects

__all__ = [
    "LinuxDesktopNotifier",
    "LinuxPathProvider",
    "LinuxProcessManager",
    "LinuxSingleInstanceLock",
    "LinuxStartupManager",
    "LinuxSystemTray",
    "LinuxWindowEffects",
]
