"""Platform capability introspection for PLUS-ULTRA.

Applies OS concepts:
- Capability discovery over blind assumptions: Rather than assuming every Linux
  or Windows environment behaves identically, detect actual supported features
  (e.g., AppIndicator vs XEmbed, notify-send availability, win32 toast).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from plus_ultra.platform.detection import (
    DesktopEnvironment,
    DisplayServer,
    PlatformType,
    detect_desktop_environment,
    detect_display_server,
    detect_platform,
)


@dataclass(frozen=True, slots=True)
class PlatformCapabilities:
    """Matrix of capabilities supported by the active host environment."""

    platform_type: PlatformType
    display_server: DisplayServer
    desktop_environment: DesktopEnvironment
    supports_system_tray: bool
    supports_desktop_notifications: bool
    supports_autostart: bool
    supports_window_shaping: bool
    supports_posix_permissions: bool
    supports_process_introspection: bool
    notification_backend_name: str
    tray_backend_name: str


def discover_capabilities() -> PlatformCapabilities:
    """Inspect the running system and return its capability matrix."""
    plat = detect_platform()
    display = detect_display_server()
    desktop = detect_desktop_environment()

    # Notification discovery
    if plat == PlatformType.WINDOWS:
        notif_support = True
        notif_name = "windows_notification_area"
    elif plat == PlatformType.LINUX:
        has_notify_send = shutil.which("notify-send") is not None
        notif_support = has_notify_send
        notif_name = "notify_send" if has_notify_send else "none"
    elif plat == PlatformType.MACOS:
        notif_support = False
        notif_name = "macos_unsupported"
    else:
        notif_support = False
        notif_name = "none"

    # Tray discovery (pystray is installed and available)
    try:
        import pystray  # noqa: F401

        has_pystray = True
    except (ImportError, Exception):
        has_pystray = False

    if plat == PlatformType.WINDOWS:
        tray_support = has_pystray
        tray_name = "pystray_win32" if has_pystray else "none"
        window_shaping = True
        posix_perms = False
        autostart = True
    elif plat == PlatformType.LINUX:
        tray_support = has_pystray
        tray_name = "pystray_appindicator" if has_pystray else "none"
        # Window shaping via XShape is supported on X11 and XWayland
        window_shaping = display in (DisplayServer.X11, DisplayServer.WAYLAND)
        posix_perms = True
        autostart = True
    else:
        tray_support = False
        tray_name = "none"
        window_shaping = False
        posix_perms = False
        autostart = False

    return PlatformCapabilities(
        platform_type=plat,
        display_server=display,
        desktop_environment=desktop,
        supports_system_tray=tray_support,
        supports_desktop_notifications=notif_support,
        supports_autostart=autostart,
        supports_window_shaping=window_shaping,
        supports_posix_permissions=posix_perms,
        supports_process_introspection=True,
        notification_backend_name=notif_name,
        tray_backend_name=tray_name,
    )
