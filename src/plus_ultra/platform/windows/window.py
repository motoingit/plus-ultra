"""Windows platform window effects, rounding, and styling.

Applies OS concepts:
- Borderless styling and transparency for floating capsule on Windows.
- Prevents invalid GDI handle collisions with Tkinter internal window wrappers.
"""

from __future__ import annotations

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class WindowsWindowEffects:
    """Manages Windows-specific window presentation and clipping."""

    def apply_capsule_shape(
        self, window: tk.Tk | tk.Toplevel, width: int, height: int, radius: int
    ) -> bool:
        """Apply capsule styling to Windows window.

        Note: Canvas-drawn rounded polygon with borderless window geometry
        provides pixel-perfect capsule rendering on Windows DWM without
        interfering with internal Tkinter HWND redraw queues.
        """
        try:
            # Configure transparent / matching borderless background
            window.configure(bg="#12151c")
            return True
        except Exception as exc:
            logger.debug("Windows window styling skipped: %s", exc)
            return False

    def set_always_on_top(
        self, window: tk.Tk | tk.Toplevel, enabled: bool
    ) -> bool:
        """Configure always-on-top attribute."""
        try:
            window.attributes("-topmost", enabled)
            return True
        except Exception as exc:
            logger.debug("Failed setting topmost on Windows: %s", exc)
            return False
