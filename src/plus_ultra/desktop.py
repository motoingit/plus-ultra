"""Desktop platform adapter and process management for PLUS-ULTRA.

Applies OS concepts:
- Mutual Exclusion & Single Instance: POSIX advisory file locking (fcntl.flock)
  ensures only one application process runs concurrently per user session.
- Process lifecycle: Clean lock acquisition, PID recording, and release on
  normal shutdown or signal termination.
"""

from __future__ import annotations

import contextlib
import fcntl
import logging
import os
import shutil
import subprocess
from pathlib import Path

from plus_ultra import config

logger = logging.getLogger(__name__)

LOCK_FILENAME = "plus-ultra.lock"


class SingleInstanceLock:
    """Manages an exclusive advisory file lock for the application process."""

    def __init__(self, lock_path: Path | None = None) -> None:
        self.lock_path = lock_path or (config.get_state_dir() / LOCK_FILENAME)
        self._fd: int | None = None

    def acquire(self) -> bool:
        """Attempt to acquire exclusive advisory lock without blocking.

        Returns:
            True if lock was acquired, False if another instance holds it.
        """
        config.get_state_dir()  # Ensure state directory exists (0o700)
        try:
            fd = os.open(
                self.lock_path,
                os.O_RDWR | os.O_CREAT,
                0o600,
            )
            # Try exclusive non-blocking lock
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Record PID for diagnostic inspection
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, f"{os.getpid()}\n".encode())

            self._fd = fd
            logger.info(
                "Acquired single-instance lock on %s (pid: %d)",
                self.lock_path,
                os.getpid(),
            )
            return True
        except (BlockingIOError, OSError) as exc:
            logger.warning(
                "Single-instance lock contention on %s: %s",
                self.lock_path,
                exc,
            )
            with contextlib.suppress(OSError):
                if "fd" in locals():
                    os.close(fd)
            return False

    def release(self) -> None:
        """Release the advisory lock and close the file descriptor."""
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
                logger.info(
                    "Released single-instance lock on %s", self.lock_path
                )
            except OSError as err:
                logger.error("Error releasing lock: %s", err)
            finally:
                self._fd = None
                with contextlib.suppress(OSError):
                    self.lock_path.unlink()

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        self.release()


def apply_window_shape_mask(
    window_id: int, width: int, height: int, radius: int
) -> bool:
    """Clip XWayland window to capsule shape using XShape extension.

    Returns True if the mask was applied, False if Xlib/XShape is unavailable.
    """
    try:
        import ctypes
        import ctypes.util

        x11_name = ctypes.util.find_library("X11") or "libX11.so.6"
        xext_name = ctypes.util.find_library("Xext") or "libXext.so.6"
        x11 = ctypes.cdll.LoadLibrary(x11_name)
        xext = ctypes.cdll.LoadLibrary(xext_name)

        display = x11.XOpenDisplay(None)
        if not display:
            return False

        try:
            event_base = ctypes.c_int()
            error_base = ctypes.c_int()
            if not xext.XShapeQueryExtension(
                display, ctypes.byref(event_base), ctypes.byref(error_base)
            ):
                return False

            row_bytes = (width + 7) // 8
            data = bytearray(row_bytes * height)
            r = radius
            r_sq = r * r

            for y in range(height):
                for x in range(width):
                    inside = False
                    if r <= x <= width - r:
                        inside = True
                    elif x < r:
                        inside = (x - r) ** 2 + (y - r) ** 2 <= r_sq
                    else:
                        inside = (x - (width - r)) ** 2 + (y - r) ** 2 <= r_sq

                    if inside:
                        byte_idx = y * row_bytes + (x // 8)
                        bit_idx = x % 8
                        data[byte_idx] |= 1 << bit_idx

            bitmap_data = (ctypes.c_char * len(data)).from_buffer(data)
            pixmap = x11.XCreateBitmapFromData(
                display, window_id, bitmap_data, width, height
            )
            if not pixmap:
                return False

            # 0: ShapeBounding, 0: ShapeSet
            xext.XShapeCombineMask(display, window_id, 0, 0, 0, pixmap, 0)
            x11.XFreePixmap(display, pixmap)
            x11.XFlush(display)
            return True
        finally:
            x11.XCloseDisplay(display)
    except Exception as exc:
        logger.debug("Window shape mask skipped or unsupported: %s", exc)
        return False


def send_desktop_notification(
    title: str,
    message: str = "",
    urgency: str = "normal",
    timeout_ms: int = 5000,
    app_name: str = config.APP_NAME,
) -> bool:
    """Send a native Linux desktop notification via notify-send without shell.

    Args:
        title: Notification summary heading.
        message: Notification body text.
        urgency: Urgency level ('low', 'normal', 'critical').
        timeout_ms: Expiration timeout in milliseconds.
        app_name: Originating application identifier.

    Returns:
        True if notify-send completed successfully, False otherwise.
    """
    executable = shutil.which("notify-send")
    if not executable:
        logger.warning(
            "notify-send executable not found; desktop notification skipped."
        )
        return False

    cmd = [
        executable,
        "-a",
        app_name,
        "-u",
        urgency,
        "-t",
        str(timeout_ms),
        title,
        message,
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            timeout=3,
        )
        logger.info("Desktop notification dispatched: %s", title)
        return True
    except (subprocess.SubprocessError, OSError) as exc:
        logger.warning("Failed to dispatch desktop notification: %s", exc)
        return False


notify = send_desktop_notification
