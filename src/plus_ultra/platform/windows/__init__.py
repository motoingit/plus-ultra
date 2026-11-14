"""Windows platform backend package."""

from __future__ import annotations

from plus_ultra.platform.windows.instance import WindowsSingleInstanceLock
from plus_ultra.platform.windows.notifications import WindowsDesktopNotifier
from plus_ultra.platform.windows.paths import WindowsPathProvider
from plus_ultra.platform.windows.process import WindowsProcessManager
from plus_ultra.platform.windows.startup import WindowsStartupManager
from plus_ultra.platform.windows.tray import WindowsSystemTray
from plus_ultra.platform.windows.window import WindowsWindowEffects

__all__ = [
    "WindowsDesktopNotifier",
    "WindowsPathProvider",
    "WindowsProcessManager",
    "WindowsSingleInstanceLock",
    "WindowsStartupManager",
    "WindowsSystemTray",
    "WindowsWindowEffects",
]
