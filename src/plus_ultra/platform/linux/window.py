"""Linux window effects and XShape capsule masking.

Applies OS concepts:
- X11/XWayland Non-rectangular Window Shaping: Uses XShape extension via ctypes
  to clip XWayland window bounding box to a rounded pill, eliminating square
  window borders.
"""

from __future__ import annotations

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class LinuxWindowEffects:
    """Manages Linux X11/XWayland window presentation and shaping."""

    def apply_capsule_shape(
        self, window: tk.Tk | tk.Toplevel, width: int, height: int, radius: int
    ) -> bool:
        """Clip XWayland window to capsule shape using XShape extension."""
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

            window_id = window.winfo_id()
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
            logger.debug("Linux XShape window mask skipped: %s", exc)
            return False

    def set_always_on_top(
        self, window: tk.Tk | tk.Toplevel, enabled: bool
    ) -> bool:
        """Configure always-on-top attribute on Linux."""
        try:
            window.attributes("-topmost", enabled)
            return True
        except Exception as exc:
            logger.debug("Failed setting topmost on Linux: %s", exc)
            return False
