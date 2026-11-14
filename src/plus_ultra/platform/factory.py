"""Platform factory and dependency composition for PLUS-ULTRA.

Applies OS concepts:
- Dependency Inversion Principle: High-level business logic and UI depend upon
  abstract platform interfaces, not concrete OS APIs.
- Platform Factory: Centralizes operating-system specific instantiation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plus_ultra.core.exceptions import UnsupportedPlatformError
from plus_ultra.platform.capabilities import (
    PlatformCapabilities,
    discover_capabilities,
)
from plus_ultra.platform.detection import PlatformType, detect_platform
from plus_ultra.platform.interfaces import (
    DesktopNotifier,
    PathProvider,
    ProcessManager,
    SingleInstanceLock,
    StartupManager,
    SystemTray,
    WindowEffects,
)


@dataclass(frozen=True, slots=True)
class PlatformServices:
    """Unified container of all platform-specific adapters."""

    paths: PathProvider
    instance_lock: SingleInstanceLock
    notifications: DesktopNotifier
    tray: SystemTray
    startup: StartupManager
    process: ProcessManager
    window: WindowEffects
    capabilities: PlatformCapabilities


def create_platform_services(
    platform_override: PlatformType | None = None,
    **kwargs: Any,
) -> PlatformServices:
    """Create and return the platform adapter bundle for the current host.

    Args:
        platform_override: Optional platform enum to force a specific backend
            (primarily used for cross-platform unit testing).
        kwargs: Optional overrides for individual platform components.

    Returns:
        A strongly typed PlatformServices container.

    Raises:
        UnsupportedPlatformError: If the platform is not yet supported.
    """
    plat = platform_override or detect_platform()
    caps = discover_capabilities()

    if plat == PlatformType.WINDOWS:
        from plus_ultra.platform.windows import (
            WindowsDesktopNotifier,
            WindowsPathProvider,
            WindowsProcessManager,
            WindowsSingleInstanceLock,
            WindowsStartupManager,
            WindowsSystemTray,
            WindowsWindowEffects,
        )

        paths = kwargs.get("paths") or WindowsPathProvider()
        lock = kwargs.get("instance_lock") or WindowsSingleInstanceLock(paths=paths)
        tray = kwargs.get("tray") or WindowsSystemTray()
        notifier = kwargs.get("notifications") or WindowsDesktopNotifier(
            tray_instance=tray
        )
        startup = kwargs.get("startup") or WindowsStartupManager()
        proc = kwargs.get("process") or WindowsProcessManager()
        win = kwargs.get("window") or WindowsWindowEffects()

    elif plat == PlatformType.LINUX:
        from plus_ultra.platform.linux import (
            LinuxDesktopNotifier,
            LinuxPathProvider,
            LinuxProcessManager,
            LinuxSingleInstanceLock,
            LinuxStartupManager,
            LinuxSystemTray,
            LinuxWindowEffects,
        )

        paths = kwargs.get("paths") or LinuxPathProvider()
        lock = kwargs.get("instance_lock") or LinuxSingleInstanceLock(paths=paths)
        tray = kwargs.get("tray") or LinuxSystemTray()
        notifier = kwargs.get("notifications") or LinuxDesktopNotifier()
        startup = kwargs.get("startup") or LinuxStartupManager()
        proc = kwargs.get("process") or LinuxProcessManager()
        win = kwargs.get("window") or LinuxWindowEffects()

    elif plat == PlatformType.MACOS:
        raise UnsupportedPlatformError(
            "macOS is not yet natively supported in this build. "
            "See .docs/architecture.MD for the platform extension guide."
        )
    else:
        raise UnsupportedPlatformError(
            f"Unsupported operating system platform: {plat.value}"
        )

    return PlatformServices(
        paths=paths,
        instance_lock=lock,
        notifications=notifier,
        tray=tray,
        startup=startup,
        process=proc,
        window=win,
        capabilities=caps,
    )
