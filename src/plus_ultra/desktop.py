"""Desktop platform adapter and process management for PLUS-ULTRA.

Applies OS concepts:
- Mutual Exclusion & Single Instance: Delegates to PlatformServices instance lock.
- Desktop notifications: Provides native notify-send compatibility on Linux
  and delegates across platforms.
- Window Shaping: Delegates to WindowEffects.
"""

from __future__ import annotations

import logging
from pathlib import Path

from plus_ultra.config import APP_NAME, get_platform_services
from plus_ultra.platform.interfaces.notifications import (
    NotificationRequest,
    NotificationUrgency,
)

logger = logging.getLogger(__name__)

LOCK_FILENAME = "plus-ultra.lock"


class SingleInstanceLock:
    """Advisory single-instance lock delegating to current platform backend."""

    def __init__(self, lock_path: Path | None = None) -> None:
        if lock_path is not None:
            from plus_ultra.platform.detection import is_windows
            if is_windows():
                from plus_ultra.platform.windows.instance import (
                    WindowsSingleInstanceLock,
                )
                self._backend = WindowsSingleInstanceLock(lock_path=lock_path)
            else:
                from plus_ultra.platform.linux.instance import (
                    LinuxSingleInstanceLock,
                )
                self._backend = LinuxSingleInstanceLock(lock_path=lock_path)
        else:
            self._backend = get_platform_services().instance_lock

    @property
    def lock_path(self) -> Path:
        return self._backend.lock_path

    def acquire(self) -> bool:
        return self._backend.acquire()

    def release(self) -> None:
        self._backend.release()

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        self.release()


def apply_window_shape_mask(
    window_id_or_widget: object, width: int, height: int, radius: int
) -> bool:
    """Clip window to capsule shape using platform-specific mechanism."""
    import tkinter as tk

    win_effects = get_platform_services().window
    if isinstance(window_id_or_widget, (tk.Tk, tk.Toplevel)):
        return win_effects.apply_capsule_shape(
            window_id_or_widget, width, height, radius
        )

    try:
        from plus_ultra.platform.linux.window import LinuxWindowEffects
        class _StubWidget:
            def winfo_id(self) -> int:
                return int(window_id_or_widget)  # type: ignore[arg-type]

        return LinuxWindowEffects().apply_capsule_shape(
            _StubWidget(), width, height, radius  # type: ignore[arg-type]
        )
    except Exception:
        return False


def send_desktop_notification(
    title: str,
    message: str = "",
    urgency: str = "normal",
    timeout_ms: int = 3000,
    app_name: str = APP_NAME,
) -> bool:
    """Send native desktop notification via notify-send adapter."""
    from plus_ultra.platform.linux.notifications import LinuxDesktopNotifier

    try:
        urg = NotificationUrgency(urgency.lower())
    except ValueError:
        urg = NotificationUrgency.NORMAL

    req = NotificationRequest(
        title=title,
        message=message,
        urgency=urg,
        timeout_ms=timeout_ms,
        app_name=app_name,
    )
    return LinuxDesktopNotifier().send(req)


notify = send_desktop_notification
