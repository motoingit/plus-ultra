"""Linux system tray implementation using pystray with AppIndicator backend.

Applies OS concepts:
- FreeDesktop StatusNotifier / AppIndicator shell tray integration.
- Graceful diagnosis: Detects missing PyGObject/AppIndicator system bindings,
  logs accurate diagnostic information, and ensures the application stays
  usable even if the system tray backend is unavailable.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from plus_ultra.platform.interfaces.tray import TrayMenuItem

logger = logging.getLogger(__name__)


def _create_default_pillow_icon(size: int = 64) -> Any:
    """Generate a clean fallback PIL Image in memory."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill="#1a1f2c",
        outline="#00e5ff",
        width=3,
    )
    center = size // 2
    dot_r = size // 5
    draw.ellipse(
        [center - dot_r, center - dot_r, center + dot_r, center + dot_r],
        fill="#00e5ff",
        outline=None,
    )
    return img


class LinuxSystemTray:
    """Manages system tray integration on Linux desktop environments."""

    def __init__(self) -> None:
        self._icon: Any | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._is_running = False
        self._current_tooltip = "PLUS-ULTRA"
        self._menu_items: list[TrayMenuItem] = []
        self._on_menu_popup: Callable[[int, int], None] | None = None

    @property
    def is_supported(self) -> bool:
        try:
            import pystray  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    def _convert_menu_items(
        self, items: list[TrayMenuItem]
    ) -> list[Any]:
        import pystray

        result: list[Any] = []
        for it in items:
            if not it.visible:
                continue
            if it.is_separator:
                result.append(pystray.Menu.SEPARATOR)
                continue

            action_cb = it.action
            if it.children:
                sub_items = self._convert_menu_items(list(it.children))
                sub_menu = pystray.Menu(*sub_items)
                result.append(
                    pystray.MenuItem(
                        text=it.label,
                        action=sub_menu,
                        enabled=it.enabled,
                    )
                )
            else:
                def _make_action(
                    fn: Callable[[], None] | None,
                ) -> Callable[[Any, Any], None] | None:
                    if fn is None:
                        return None
                    return lambda _icon, _item: fn()

                checked_fn = (
                    (lambda _item, state=it.checked: state)
                    if it.checked is not None
                    else None
                )
                is_default = (it.label == "Show Dashboard") or (
                    not any(getattr(r, "default", False) for r in result)
                    and not it.is_separator
                )
                result.append(
                    pystray.MenuItem(
                        text=it.label,
                        action=_make_action(action_cb),
                        checked=checked_fn,
                        enabled=it.enabled,
                        default=is_default,
                    )
                )
        return result

    def start(
        self,
        icon_path: Path | None = None,
        tooltip: str = "PLUS-ULTRA",
        menu_items: list[TrayMenuItem] | None = None,
        on_menu_popup: Callable[[int, int], None] | None = None,
    ) -> bool:
        """Start Linux system tray icon in a dedicated daemon thread."""
        with self._lock:
            if self._is_running:
                return True

            try:
                import pystray
                from PIL import Image

                self._menu_items = list(menu_items) if menu_items else []
                self._on_menu_popup = on_menu_popup

                if icon_path and icon_path.is_file():
                    img = Image.open(icon_path)
                else:
                    img = _create_default_pillow_icon()

                self._current_tooltip = tooltip
                menu = None
                if menu_items:
                    menu = pystray.Menu(*self._convert_menu_items(menu_items))

                self._icon = pystray.Icon(
                    name="plus-ultra",
                    icon=img,
                    title=tooltip,
                    menu=menu,
                )

                if hasattr(self._icon, "_message_handlers"):
                    self._wire_xorg_events()

                def _run_worker() -> None:
                    try:
                        logger.info("Linux system tray loop starting.")
                        self._icon.run()
                    except Exception as exc:
                        logger.warning(
                            "Linux system tray failed to start or run: %s. "
                            "Ensure AppIndicator typelib is installed.",
                            exc,
                        )
                    finally:
                        with self._lock:
                            self._is_running = False

                self._thread = threading.Thread(
                    target=_run_worker,
                    name="LinuxSystemTrayThread",
                    daemon=True,
                )
                self._is_running = True
                self._thread.start()
                logger.info("Linux system tray thread dispatched.")
                return True
            except Exception as exc:
                logger.warning(
                    "Could not initialize Linux system tray: %s. "
                    "Running without system tray icon.",
                    exc,
                )
                self._is_running = False
                self._icon = None
                return False

    def stop(self) -> None:
        """Stop and unregister Linux system tray icon."""
        with self._lock:
            if not self._is_running or self._icon is None:
                return
            logger.info("Stopping Linux system tray icon...")
            try:
                self._icon.stop()
            except Exception as exc:
                logger.debug("Exception stopping Linux tray icon: %s", exc)
            finally:
                self._icon = None
                self._is_running = False

    def update_tooltip(self, text: str) -> None:
        with self._lock:
            self._current_tooltip = text
            if self._icon is not None:
                with contextlib.suppress(Exception):
                    self._icon.title = text

    def update_icon(self, icon_path: Path) -> None:
        with self._lock:
            if self._icon is not None and icon_path.is_file():
                try:
                    from PIL import Image

                    img = Image.open(icon_path)
                    self._icon.icon = img
                except Exception as exc:
                    logger.warning("Could not update Linux tray icon: %s", exc)

    def update_menu(self, menu_items: list[TrayMenuItem]) -> None:
        with self._lock:
            self._menu_items = list(menu_items)
            if self._icon is not None:
                try:
                    import pystray

                    new_menu = pystray.Menu(
                        *self._convert_menu_items(menu_items)
                    )
                    self._icon.menu = new_menu
                except Exception as exc:
                    logger.warning("Could not update Linux tray menu: %s", exc)

    def _wire_xorg_events(self) -> None:
        """Attach right-click popup menu handler for Xorg tray icons."""
        try:
            import Xlib.X

            def _on_xorg_button_press(event: Any) -> None:
                detail = getattr(event, "detail", 1)
                root_x = getattr(event, "root_x", 0)
                root_y = getattr(event, "root_y", 0)

                logger.debug(
                    "Linux tray button press: detail=%s, x=%s, y=%s",
                    detail,
                    root_x,
                    root_y,
                )
                if detail == 3:
                    self._dispatch_menu_popup(root_x, root_y)
                elif detail == 1:
                    if self._icon and callable(self._icon):
                        try:
                            self._icon()
                        except Exception:
                            self._dispatch_menu_popup(root_x, root_y)
                    else:
                        self._dispatch_menu_popup(root_x, root_y)

            self._icon._message_handlers[Xlib.X.ButtonPress] = (
                _on_xorg_button_press
            )
        except Exception as exc:
            logger.debug("Could not attach Xorg button handlers: %s", exc)

    def _dispatch_menu_popup(self, x: int, y: int) -> None:
        """Dispatch tray menu display to registered callback or Tkinter."""
        if self._on_menu_popup is not None:
            try:
                self._on_menu_popup(x, y)
                return
            except Exception as exc:
                logger.warning("Error in on_menu_popup callback: %s", exc)

        try:
            import tkinter as tk

            root = getattr(tk, "_default_root", None)
            if root and root.winfo_exists():
                root.after_idle(lambda: self._show_tk_menu(root, x, y))
        except Exception as exc:
            logger.debug("Could not show fallback Tkinter menu: %s", exc)

    def _show_tk_menu(self, root: Any, x: int, y: int) -> None:
        """Render a Tkinter context popup menu at screen position (x, y)."""
        import tkinter as tk

        menu = tk.Menu(
            root,
            tearoff=0,
            bg="#1a1f2c",
            fg="#f8fafc",
            activebackground="#00e5ff",
            activeforeground="#0a0e17",
            activeborderwidth=0,
            font=("Helvetica", 10),
        )
        for it in self._menu_items:
            if not it.visible:
                continue
            if it.is_separator:
                menu.add_separator()
            else:
                act = it.action
                menu.add_command(
                    label=it.label,
                    command=act,
                    state="normal" if it.enabled else "disabled",
                )

        if x <= 0 or y <= 0:
            sw = root.winfo_screenwidth()
            x, y = sw - 220, 32

        menu.tk_popup(x, y)
