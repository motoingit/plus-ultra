"""Automated tests for the Platform Abstraction Layer (PAL).

Validates:
- Platform detection across Windows, Linux, and macOS.
- Capability detection matrix.
- Platform factory backend selection and dependency composition.
- Unsupported platform error handling.
- Interface contract compliance across Windows and Linux providers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from plus_ultra.core.exceptions import UnsupportedPlatformError
from plus_ultra.platform.capabilities import discover_capabilities
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
    create_platform_services,
)
from plus_ultra.platform.interfaces import (
    DesktopNotifier,
    PathProvider,
    ProcessManager,
    SingleInstanceLock,
    StartupManager,
    SystemTray,
    WindowEffects,
)
from plus_ultra.platform.linux import (
    LinuxDesktopNotifier,
    LinuxPathProvider,
    LinuxProcessManager,
    LinuxSingleInstanceLock,
    LinuxStartupManager,
    LinuxSystemTray,
    LinuxWindowEffects,
)
from plus_ultra.platform.windows import (
    WindowsDesktopNotifier,
    WindowsPathProvider,
    WindowsProcessManager,
    WindowsSingleInstanceLock,
    WindowsStartupManager,
    WindowsSystemTray,
    WindowsWindowEffects,
)


def test_platform_detection_variants() -> None:
    """Verify platform detection correctly identifies OS strings."""
    assert detect_platform("win32") == PlatformType.WINDOWS
    assert detect_platform("windows") == PlatformType.WINDOWS
    assert detect_platform("linux") == PlatformType.LINUX
    assert detect_platform("linux2") == PlatformType.LINUX
    assert detect_platform("darwin") == PlatformType.MACOS
    assert detect_platform("freebsd") == PlatformType.UNKNOWN


def test_platform_helper_booleans(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify is_windows, is_linux, is_macos booleans reflect platform."""
    monkeypatch.setattr("sys.platform", "win32")
    assert is_windows() is True
    assert is_linux() is False
    assert is_macos() is False

    monkeypatch.setattr("sys.platform", "linux")
    assert is_windows() is False
    assert is_linux() is True
    assert is_macos() is False

    monkeypatch.setattr("sys.platform", "darwin")
    assert is_windows() is False
    assert is_linux() is False
    assert is_macos() is True


def test_display_server_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify detection of Wayland vs X11 on Linux and DWM on Windows."""
    monkeypatch.setattr("sys.platform", "win32")
    assert detect_display_server() == DisplayServer.WINDOWS_DWM

    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert detect_display_server() == DisplayServer.WAYLAND

    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":0")
    assert detect_display_server() == DisplayServer.X11


def test_desktop_environment_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify desktop shell detection on Linux and Windows."""
    monkeypatch.setattr("sys.platform", "win32")
    assert detect_desktop_environment() == DesktopEnvironment.WINDOWS_SHELL

    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    assert detect_desktop_environment() == DesktopEnvironment.GNOME

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    assert detect_desktop_environment() == DesktopEnvironment.KDE


def test_capabilities_matrix() -> None:
    """Verify discover_capabilities returns a populated capability matrix."""
    caps = discover_capabilities()
    assert isinstance(caps.platform_type, PlatformType)
    assert isinstance(caps.display_server, DisplayServer)
    assert isinstance(caps.desktop_environment, DesktopEnvironment)
    assert isinstance(caps.supports_system_tray, bool)
    assert isinstance(caps.supports_desktop_notifications, bool)
    assert len(caps.notification_backend_name) > 0
    assert len(caps.tray_backend_name) > 0


def test_factory_creates_windows_services() -> None:
    """Verify factory returns Windows implementations when targeted."""
    services = create_platform_services(platform_override=PlatformType.WINDOWS)
    assert isinstance(services.paths, WindowsPathProvider)
    assert isinstance(services.instance_lock, WindowsSingleInstanceLock)
    assert isinstance(services.tray, WindowsSystemTray)
    assert isinstance(services.notifications, WindowsDesktopNotifier)
    assert isinstance(services.startup, WindowsStartupManager)
    assert isinstance(services.process, WindowsProcessManager)
    assert isinstance(services.window, WindowsWindowEffects)


def test_factory_creates_linux_services() -> None:
    """Verify factory returns Linux implementations when targeted."""
    services = create_platform_services(platform_override=PlatformType.LINUX)
    assert isinstance(services.paths, LinuxPathProvider)
    assert isinstance(services.instance_lock, LinuxSingleInstanceLock)
    assert isinstance(services.tray, LinuxSystemTray)
    assert isinstance(services.notifications, LinuxDesktopNotifier)
    assert isinstance(services.startup, LinuxStartupManager)
    assert isinstance(services.process, LinuxProcessManager)
    assert isinstance(services.window, LinuxWindowEffects)


def test_factory_raises_for_unsupported_platform() -> None:
    """Verify factory raises UnsupportedPlatformError for macOS and unknown."""
    with pytest.raises(UnsupportedPlatformError):
        create_platform_services(platform_override=PlatformType.MACOS)

    with pytest.raises(UnsupportedPlatformError):
        create_platform_services(platform_override=PlatformType.UNKNOWN)


def test_path_providers_contract_compliance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify both Windows and Linux path providers satisfy PathProvider."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    win_paths = WindowsPathProvider(app_name="test-app")
    linux_paths = LinuxPathProvider(app_name="test-app")

    for provider in (win_paths, linux_paths):
        assert isinstance(provider, PathProvider)
        assert provider.app_name == "test-app"
        assert isinstance(provider.get_data_dir(), Path)
        assert isinstance(provider.get_state_dir(), Path)
        assert isinstance(provider.get_config_dir(), Path)
        assert isinstance(provider.get_db_path(), Path)
        assert isinstance(provider.get_log_path(), Path)
        assert isinstance(provider.get_user_settings_path(), Path)


def test_process_managers_contract_compliance() -> None:
    """Verify both process managers return active PID and probe accurately."""
    win_pm = WindowsProcessManager()
    linux_pm = LinuxProcessManager()

    for pm in (win_pm, linux_pm):
        assert isinstance(pm, ProcessManager)
        pid = pm.get_current_pid()
        assert pid > 0
        assert pm.is_pid_running(pid) is True
        assert pm.is_pid_running(-999) is False
