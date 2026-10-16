"""Transient notification popup capsule pill component for PLUS-ULTRA."""

from __future__ import annotations

import contextlib
import logging
import tkinter as tk

from plus_ultra.desktop import apply_window_shape_mask
from plus_ultra.notifications import (
    CapsuleNotification,
    CapsuleNotificationQueue,
)
from plus_ultra.ui.geometry import generate_capsule_points
from plus_ultra.ui.theme import THEME, CapsuleTheme

logger = logging.getLogger(__name__)


class CapsulePopupPill:
    """Transient rounded popup pill appearing below floating capsule."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        queue: CapsuleNotificationQueue,
        theme: CapsuleTheme = THEME,
        always_on_top: bool = True,
        default_duration_ms: int = 3000,
    ) -> None:
        self.parent = parent
        self.queue = queue
        self.theme = theme
        self.always_on_top = always_on_top
        self.default_duration_ms = default_duration_ms

        self.window: tk.Toplevel | None = None
        self._dismiss_timer_id: str | None = None
        self._current_width = 320
        self._height = 52
        self._radius = 26

    @property
    def is_visible(self) -> bool:
        """Return True if popup window currently exists and is displayed."""
        return bool(self.window is not None and self.window.winfo_exists())

    def show(
        self,
        item: CapsuleNotification,
        parent_x: int,
        parent_y: int,
        parent_w: int,
        parent_h: int,
        duration_ms: int | None = None,
    ) -> None:
        """Spawn or refresh the 3-second popup capsule directly below parent."""
        self.cancel_timer()

        duration = (
            duration_ms if duration_ms is not None else self.default_duration_ms
        )
        pop_w = max(320, self.queue.compute_popup_width(item))
        self._current_width = pop_w
        pop_h, pop_r = self._height, self._radius

        pop_x = parent_x + (parent_w - pop_w) // 2
        pop_y = parent_y + parent_h + 10

        if not self.is_visible:
            popup = tk.Toplevel(self.parent)
            popup.overrideredirect(True)
            if self.always_on_top:
                popup.attributes("-topmost", True)
            popup.configure(bg=self.theme.window_bg)
            self.window = popup
        else:
            popup = self.window  # type: ignore[assignment]

        popup.geometry(f"{pop_w}x{pop_h}+{pop_x}+{pop_y}")
        for child in popup.winfo_children():
            child.destroy()

        canvas = tk.Canvas(
            popup,
            width=pop_w,
            height=pop_h,
            bg=self.theme.window_bg,
            highlightthickness=0,
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        pts = generate_capsule_points(pop_w, pop_h, pop_r)
        canvas.create_polygon(
            pts,
            fill=self.theme.popup_bg,
            outline=self.theme.popup_border,
            width=2.0,
        )

        preview_text = self.queue.format_popup_text(item)
        content_str = (
            f"{item.icon}  {preview_text}" if item.icon else preview_text
        )
        canvas.create_text(
            pop_w // 2,
            pop_h // 2,
            text=content_str,
            fill=self.theme.popup_text,
            font=(self.theme.font_family, 11, "bold"),
        )

        popup.update_idletasks()
        apply_window_shape_mask(popup.winfo_id(), pop_w, pop_h, pop_r)

        self._dismiss_timer_id = self.parent.after(duration, self.dismiss)

    def reposition(
        self, parent_x: int, parent_y: int, parent_w: int, parent_h: int
    ) -> None:
        """Keep popup pill positioned relative to moving parent window."""
        if self.is_visible and self.window:
            pop_x = parent_x + (parent_w - self._current_width) // 2
            pop_y = parent_y + parent_h + 8
            self.window.geometry(f"+{pop_x}+{pop_y}")

    def cancel_timer(self) -> None:
        """Cancel any pending auto-dismiss timer."""
        if self._dismiss_timer_id is not None:
            with contextlib.suppress(Exception):
                self.parent.after_cancel(self._dismiss_timer_id)
            self._dismiss_timer_id = None

    def dismiss(self) -> None:
        """Dismiss and destroy the popup pill window."""
        self.cancel_timer()
        if self.is_visible and self.window:
            with contextlib.suppress(Exception):
                self.window.destroy()
        self.window = None
