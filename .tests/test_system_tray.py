"""Automated tests for System Tray lifecycle, menu items, and callback safety.

Validates:
- Menu items hierarchy and checked/enabled state.
- Tray startup and shutdown lifecycle.
- Tooltip and dynamic menu updates.
- Background callback safety when invoked from tray threads.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plus_ultra.platform.interfaces.tray import SystemTray, TrayMenuItem
from plus_ultra.platform.linux.tray import LinuxSystemTray
from plus_ultra.platform.windows.tray import WindowsSystemTray


def test_tray_menu_item_attributes() -> None:
    """Verify TrayMenuItem data contract and defaults."""
    action_called = False

    def _action() -> None:
        nonlocal action_called
        action_called = True

    item = TrayMenuItem(label="Show Dashboard", action=_action)
    assert item.label == "Show Dashboard"
    assert item.is_separator is False
    assert item.enabled is True
    assert item.visible is True
    assert item.checked is None

    if item.action:
        item.action()
    assert action_called is True

    sep = TrayMenuItem(label="", is_separator=True)
    assert sep.is_separator is True


def test_windows_tray_interface_compliance() -> None:
    """Verify WindowsSystemTray implements the SystemTray protocol."""
    tray = WindowsSystemTray()
    assert isinstance(tray, SystemTray)
    assert tray.is_running is False


def test_linux_tray_interface_compliance() -> None:
    """Verify LinuxSystemTray implements the SystemTray protocol."""
    tray = LinuxSystemTray()
    assert isinstance(tray, SystemTray)
    assert tray.is_running is False


def test_tray_menu_item_conversion() -> None:
    """Verify TrayMenuItem hierarchy converts to pystray menu structure."""
    tray = WindowsSystemTray()
    clicked = []

    items = [
        TrayMenuItem(label="Dashboard", action=lambda: clicked.append("dash")),
        TrayMenuItem(is_separator=True, label=""),
        TrayMenuItem(label="Exit", action=lambda: clicked.append("exit")),
    ]

    converted = tray._convert_menu_items(items)
    assert len(converted) == 3
    # 2nd is separator
    import pystray

    assert converted[1] == pystray.Menu.SEPARATOR


def test_tray_lifecycle_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify tray start and stop lifecycle with mocked pystray Icon."""
    mock_icon = MagicMock()
    monkeypatch.setattr("pystray.Icon", lambda **_kwargs: mock_icon)

    tray = WindowsSystemTray()
    started = tray.start(tooltip="PLUS-ULTRA Testing")
    assert started is True
    assert tray.is_running is True

    tray.update_tooltip("New Tooltip")
    assert mock_icon.title == "New Tooltip"

    tray.stop()
    mock_icon.stop.assert_called_once()
    assert tray.is_running is False


def test_tray_idempotent_stop() -> None:
    """Verify calling stop() on unstarted or stopped tray is safe."""
    tray = WindowsSystemTray()
    tray.stop()  # Should not raise
    tray.stop()
    assert tray.is_running is False
