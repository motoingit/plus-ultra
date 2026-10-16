"""Floating desktop capsule widget for PLUS-ULTRA.

Applies OS concepts:
- Event-driven programming: Tkinter mainloop handling window system events.
- Stacking order & Compositor: Window manager flags (overrideredirect, topmost).
- Pointer tracking: Drag gesture delta math and hover event state transitions.
"""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from typing import Any

from plus_ultra import settings
from plus_ultra.ui.theme import GEOMETRY, THEME, CapsuleGeometry, CapsuleTheme

logger = logging.getLogger(__name__)


class FloatingWidget:
    """Always-on-top hovering desktop capsule widget."""

    def __init__(
        self,
        root: tk.Tk | None = None,
        geometry: CapsuleGeometry = GEOMETRY,
        theme: CapsuleTheme = THEME,
        on_click_callback: Callable[[], None] | None = None,
    ) -> None:
        self.geometry = geometry
        self.theme = theme
        self.on_click_callback = on_click_callback
        self.root = root or tk.Tk()

        self._drag_start_x: int = 0
        self._drag_start_y: int = 0
        self._dragged: bool = False
        self._is_hovered: bool = False
        self._active_toggle: bool = False

        self._load_preferences()
        self._setup_window()
        self._build_canvas()
        self._bind_events()

    def _load_preferences(self) -> None:
        """Load user preferences for window stacking and animations."""
        eff: dict[str, Any] = settings.load_effective_settings()
        self.always_on_top: bool = eff.get("always_on_top", True)
        self.glow_enabled: bool = eff.get("glow_enabled", True)
        self.pulse_period_ms: int = eff.get("glow_pulse_period_ms", 3000)

    def _setup_window(self) -> None:
        """Configure borderless window placement at top-center of screen."""
        self.root.overrideredirect(True)
        if self.always_on_top:
            self.root.attributes("-topmost", True)

        screen_w = self.root.winfo_screenwidth()
        init_x = (screen_w - self.geometry.width) // 2
        init_y = self.geometry.top_offset
        self.root.geometry(
            f"{self.geometry.width}x{self.geometry.height}+{init_x}+{init_y}"
        )
        self.root.configure(bg=self.theme.window_bg)

    def _build_canvas(self) -> None:
        """Construct canvas and draw the initial capsule polygon and text."""
        self.canvas = tk.Canvas(
            self.root,
            width=self.geometry.width,
            height=self.geometry.height,
            bg=self.theme.window_bg,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        w = self.geometry.width
        h = self.geometry.height
        r = self.geometry.radius

        # Polygon points approximating a horizontal capsule/pill
        points = [
            r,
            2,
            w - r,
            2,
            w - 2,
            2,
            w - 2,
            r,
            w - 2,
            h - r,
            w - 2,
            h - 2,
            w - r,
            h - 2,
            r,
            h - 2,
            2,
            h - 2,
            2,
            h - r,
            2,
            r,
            2,
            2,
        ]

        self.capsule_id = self.canvas.create_polygon(
            points,
            smooth=True,
            fill=self.theme.idle_fill,
            outline=self.theme.idle_border,
            width=2,
        )

        mid_x = w // 2
        mid_y = h // 2
        self.text_id = self.canvas.create_text(
            mid_x,
            mid_y,
            text="PLUS-ULTRA",
            fill=self.theme.idle_text,
            font=(self.theme.font_family, self.theme.font_size, "bold"),
        )

    def _bind_events(self) -> None:
        """Bind mouse drag, hover, click, and keyboard events."""
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)
        self.root.bind("<Escape>", lambda _e: self.close())

    def _on_enter(self, _event: tk.Event[Any]) -> None:
        """Handle mouse hover entrance with glow styling."""
        self._is_hovered = True
        if self.glow_enabled:
            self.canvas.itemconfig(
                self.capsule_id,
                fill=self.theme.hover_fill,
                outline=self.theme.hover_border,
            )
            self.canvas.itemconfig(self.text_id, fill=self.theme.hover_text)

    def _on_leave(self, _event: tk.Event[Any]) -> None:
        """Handle mouse hover exit returning to idle styling."""
        self._is_hovered = False
        idle_border = (
            self.theme.hover_border
            if self._active_toggle
            else self.theme.idle_border
        )
        self.canvas.itemconfig(
            self.capsule_id,
            fill=self.theme.idle_fill,
            outline=idle_border,
        )
        self.canvas.itemconfig(self.text_id, fill=self.theme.idle_text)

    def _on_button_press(self, event: tk.Event[Any]) -> None:
        """Record initial mouse coordinates on click."""
        self._drag_start_x = event.x_root - self.root.winfo_x()
        self._drag_start_y = event.y_root - self.root.winfo_y()
        self._dragged = False

    def _on_motion(self, event: tk.Event[Any]) -> None:
        """Track mouse dragging and update window coordinates."""
        dx = abs(event.x_root - (self._drag_start_x + self.root.winfo_x()))
        dy = abs(event.y_root - (self._drag_start_y + self.root.winfo_y()))
        if dx > 2 or dy > 2:
            self._dragged = True

        new_x = event.x_root - self._drag_start_x
        new_y = event.y_root - self._drag_start_y
        self.root.geometry(
            f"{self.geometry.width}x{self.geometry.height}+{new_x}+{new_y}"
        )

    def _on_button_release(self, _event: tk.Event[Any]) -> None:
        """Handle click when mouse was released without dragging."""
        if not self._dragged:
            self._on_click()

    def _on_click(self) -> None:
        """Toggle active state and trigger click callback."""
        self._active_toggle = not self._active_toggle
        logger.info("Capsule clicked (active toggle: %s)", self._active_toggle)
        if self.on_click_callback:
            self.on_click_callback()

    def close(self) -> None:
        """Destroy window and terminate the Tkinter event loop."""
        logger.info("Closing floating widget window.")
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
