"""Platform Abstraction Layer (PAL) for PLUS-ULTRA."""

from __future__ import annotations

from plus_ultra.platform.capabilities import (
    PlatformCapabilities,
    discover_capabilities,
)
from plus_ultra.platform.detection import (
    DesktopEnvironment,
    DisplayServer,
    PlatformType,
    detect_desktop_environment,
    detect_display_server,
    detect_platform,
    is_linux,
    is_macos,
    is_windows,
)
from plus_ultra.platform.factory import (
    PlatformServices,
    create_platform_services,
)
from plus_ultra.platform.interfaces import (
    DesktopNotifier,
    NotificationRequest,
    NotificationUrgency,
    PathProvider,
    ProcessManager,
    SingleInstanceLock,
    StartupManager,
    SystemTray,
    TrayMenuItem,
    WindowEffects,
)

__all__ = [
    "DesktopEnvironment",
    "DesktopNotifier",
    "DisplayServer",
    "NotificationRequest",
    "NotificationUrgency",
    "PathProvider",
    "PlatformCapabilities",
    "PlatformServices",
    "PlatformType",
    "ProcessManager",
    "SingleInstanceLock",
    "StartupManager",
    "SystemTray",
    "TrayMenuItem",
    "WindowEffects",
    "create_platform_services",
    "detect_desktop_environment",
    "detect_display_server",
    "detect_platform",
    "discover_capabilities",
    "is_linux",
    "is_macos",
    "is_windows",
]
