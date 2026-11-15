"""Platform and desktop environment detection for PLUS-ULTRA.

Applies OS concepts:
- Environmental introspection: Detects host operating system, display server
  (Wayland vs X11 vs Windows DWM), and desktop environment (GNOME, etc.).
- Centralized detection avoids scattering sys.platform checks throughout code.
"""

from __future__ import annotations

import enum
import os
import sys


class PlatformType(enum.StrEnum):
    """Supported and recognized host operating system platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class DesktopEnvironment(enum.StrEnum):
    """Detected desktop environment shell."""

    GNOME = "gnome"
    KDE = "kde"
    XFCE = "xfce"
    WINDOWS_SHELL = "windows_shell"
    MACOS_AQUA = "macos_aqua"
    UNKNOWN = "unknown"


class DisplayServer(enum.StrEnum):
    """Detected windowing system / display server."""

    WAYLAND = "wayland"
    X11 = "x11"
    WINDOWS_DWM = "windows_dwm"
    QUARTZ = "quartz"
    UNKNOWN = "unknown"


def detect_platform(platform_str: str | None = None) -> PlatformType:
    """Determine host operating system type from sys.platform string."""
    target = (platform_str or sys.platform).lower()
    if target.startswith("win"):
        return PlatformType.WINDOWS
    if target.startswith("linux"):
        return PlatformType.LINUX
    if target.startswith("darwin"):
        return PlatformType.MACOS
    return PlatformType.UNKNOWN


def detect_display_server() -> DisplayServer:
    """Detect active display server protocol (Wayland, X11, DWM, etc.)."""
    plat = detect_platform()
    if plat == PlatformType.WINDOWS:
        return DisplayServer.WINDOWS_DWM
    if plat == PlatformType.MACOS:
        return DisplayServer.QUARTZ
    if plat == PlatformType.LINUX:
        wayland_display = os.environ.get("WAYLAND_DISPLAY", "").strip()
        xdg_session_type = (
            os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
        )
        if wayland_display or xdg_session_type == "wayland":
            return DisplayServer.WAYLAND
        if os.environ.get("DISPLAY", "").strip() or xdg_session_type == "x11":
            return DisplayServer.X11
    return DisplayServer.UNKNOWN


def detect_desktop_environment() -> DesktopEnvironment:
    """Detect desktop shell environment (GNOME, KDE, Windows Shell, etc.)."""
    plat = detect_platform()
    if plat == PlatformType.WINDOWS:
        return DesktopEnvironment.WINDOWS_SHELL
    if plat == PlatformType.MACOS:
        return DesktopEnvironment.MACOS_AQUA

    xdg_current = os.environ.get("XDG_CURRENT_DESKTOP", "").strip().lower()
    if "gnome" in xdg_current:
        return DesktopEnvironment.GNOME
    if "kde" in xdg_current or "plasma" in xdg_current:
        return DesktopEnvironment.KDE
    if "xfce" in xdg_current:
        return DesktopEnvironment.XFCE

    desktop_session = os.environ.get("DESKTOP_SESSION", "").strip().lower()
    if "gnome" in desktop_session:
        return DesktopEnvironment.GNOME
    if "kde" in desktop_session or "plasma" in desktop_session:
        return DesktopEnvironment.KDE

    return DesktopEnvironment.UNKNOWN


def is_windows() -> bool:
    """Return True if running on Windows."""
    return detect_platform() == PlatformType.WINDOWS


def is_linux() -> bool:
    """Return True if running on Linux."""
    return detect_platform() == PlatformType.LINUX


def is_macos() -> bool:
    """Return True if running on macOS."""
    return detect_platform() == PlatformType.MACOS
