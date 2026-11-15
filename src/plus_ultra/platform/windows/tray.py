"""Windows system tray implementation using pystray and Pillow.

Applies OS concepts:
- Shell Integration: Communicates with Windows Shell_NotifyIcon API via pystray.
- Thread Safety: Runs tray event loop on a dedicated background worker thread;
  menu callbacks invoke user actions through safe dispatch.
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
    # Draw rounded dark circle with electric cyan border and center dot
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


class WindowsSystemTray:
    """Manages the Windows notification area system tray icon."""

    def __init__(self) -> None:
        self._icon: Any | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._is_running = False
        self._current_tooltip = "PLUS-ULTRA"

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
                result.append(
                    pystray.MenuItem(
                        text=it.label,
                        action=_make_action(action_cb),
                        checked=checked_fn,
                        enabled=it.enabled,
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
        """Start the system tray icon in a dedicated daemon thread."""
        with self._lock:
            if self._is_running:
                logger.debug("Tray already running.")
                return True

            try:
                import pystray
                from PIL import Image

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

                # Run icon loop in a background daemon thread
                def _run_worker() -> None:
                    try:
                        logger.info("Windows system tray loop starting.")
                        self._icon.run()
                    except Exception as exc:
                        logger.warning(
                            "Windows system tray loop ended: %s", exc
                        )
                    finally:
                        with self._lock:
                            self._is_running = False

                self._thread = threading.Thread(
                    target=_run_worker,
                    name="WindowsSystemTrayThread",
                    daemon=True,
                )
                self._is_running = True
                self._thread.start()
                logger.info("Windows system tray started successfully.")
                return True
            except Exception as exc:
                logger.error("Failed to start Windows system tray: %s", exc)
                self._is_running = False
                self._icon = None
                return False

    def stop(self) -> None:
        """Remove tray icon and terminate tray thread."""
        with self._lock:
            if not self._is_running or self._icon is None:
                return
            logger.info("Stopping Windows system tray icon...")
            try:
                self._icon.stop()
            except Exception as exc:
                logger.debug("Exception stopping tray icon: %s", exc)
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
                    logger.warning("Could not update tray icon: %s", exc)

    def update_menu(self, menu_items: list[TrayMenuItem]) -> None:
        with self._lock:
            if self._icon is not None:
                try:
                    import pystray

                    new_items = self._convert_menu_items(menu_items)
                    new_menu = pystray.Menu(*new_items)
                    self._icon.menu = new_menu
                except Exception as exc:
                    logger.warning("Could not update tray menu: %s", exc)
