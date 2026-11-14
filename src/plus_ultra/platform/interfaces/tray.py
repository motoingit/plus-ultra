"""System tray interface and data contracts.

Applies OS concepts:
- Shell Integration: Registering a persistent icon with the host shell
  notification area (Windows Notification Area / Linux AppIndicator/StatusNotifier).
- Background Thread Isolation: Tray event loop runs on its own thread;
  menu callbacks are safely marshaled to the UI event loop.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class TrayMenuItem:
    """Specification for a system tray context menu entry."""

    label: str
    action: Callable[[], None] | None = None
    is_separator: bool = False
    enabled: bool = True
    visible: bool = True
    checked: bool | None = None
    children: tuple[TrayMenuItem, ...] = field(default_factory=tuple)


@runtime_checkable
class SystemTray(Protocol):
    """Protocol for system tray icon and context menu lifecycle."""

    @property
    def is_supported(self) -> bool:
        """Return True if system tray is supported in this environment."""
        ...

    @property
    def is_running(self) -> bool:
        """Return True if tray background icon is actively visible/running."""
        ...

    def start(
        self,
        icon_path: Path | None = None,
        tooltip: str = "PLUS-ULTRA",
        menu_items: list[TrayMenuItem] | None = None,
    ) -> bool:
        """Initialize and start the background system tray icon.

        Returns:
            True if started successfully, False otherwise.
        """
        ...

    def stop(self) -> None:
        """Stop and remove the system tray icon cleanly."""
        ...

    def update_tooltip(self, text: str) -> None:
        """Update hover tooltip text."""
        ...

    def update_icon(self, icon_path: Path) -> None:
        """Update system tray icon image."""
        ...

    def update_menu(self, menu_items: list[TrayMenuItem]) -> None:
        """Update system tray context menu items dynamically."""
        ...
