"""Floating desktop capsule widget for PLUS-ULTRA."""

from __future__ import annotations

import contextlib
import logging
import tkinter as tk
from collections.abc import Callable
from typing import Any

from plus_ultra import settings
from plus_ultra.desktop import apply_window_shape_mask
from plus_ultra.network import NetworkStatusMonitor
from plus_ultra.notifications import (
    CapsuleNotification,
    CapsuleNotificationQueue,
)
from plus_ultra.ui.components.popup_pill import CapsulePopupPill
from plus_ultra.ui.geometry import (
    generate_capsule_points,
    generate_perimeter_path,
)
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import GEOMETRY, THEME, CapsuleGeometry, CapsuleTheme

logger = logging.getLogger(__name__)


class FloatingWidget:
    """Always-on-top hovering capsule widget with hover beam and popups."""

    def __init__(
        self,
        root: tk.Tk | None = None,
        geometry: CapsuleGeometry = GEOMETRY,
        theme: CapsuleTheme = THEME,
        on_click_callback: Callable[[], None] | None = None,
        initial_x: int | None = None,
        initial_y: int | None = None,
        on_position_change: Callable[[int, int], None] | None = None,
    ) -> None:
        self.geometry = geometry
        self.theme = theme
        self.on_click_callback = on_click_callback
        self.initial_x = initial_x
        self.initial_y = initial_y
        self.on_position_change = on_position_change
        self.root = root or tk.Tk()

        # Notification State Queue
        self.notifications = CapsuleNotificationQueue(
            min_width=self.geometry.min_width,
            max_width=self.geometry.max_width,
        )

        self.width = self.geometry.width
        self.height = self.geometry.height
        self.radius = self.geometry.radius

        self._drag_start_x = self._drag_start_y = self._beam_idx = 0
        self._dragged = self._is_hovered = self._active_toggle = False
        self._closed = False
        self._beam_length = 56
        self._beam_timer_id: str | None = None
        self._net_monitor = NetworkStatusMonitor()
        self._net_poll_timer_id: str | None = None

        self._load_preferences()
        self.popup_pill = CapsulePopupPill(
            parent=self.root,
            queue=self.notifications,
            theme=self.theme,
            always_on_top=self.always_on_top,
            default_duration_ms=self.popup_duration_ms,
        )
        self._setup_window()
        self._build_canvas()
        self._bind_events()
        self.root.after(400, self._poll_network_status)

    def _load_preferences(self) -> None:
        """Load user preferences for window stacking and animations."""
        eff: dict[str, Any] = settings.load_effective_settings()
        self.always_on_top: bool = eff.get("always_on_top", True)
        self.glow_enabled: bool = eff.get("glow_enabled", True)
        self.popup_duration_ms: int = eff.get(
            "notification_popup_duration_ms", 3000
        )

    def _setup_window(self) -> None:
        """Configure borderless window placement at top-center of screen."""
        self.root.overrideredirect(True)
        if self.always_on_top:
            self.root.attributes("-topmost", True)

        screen_w = self.root.winfo_screenwidth()
        default_x = (screen_w - self.width) // 2
        default_y = self.geometry.top_offset
        init_x = self.initial_x if self.initial_x is not None else default_x
        init_y = self.initial_y if self.initial_y is not None else default_y

        self.root.geometry(f"{self.width}x{self.height}+{init_x}+{init_y}")
        self.root.configure(bg=self.theme.window_bg)

    def _build_canvas(self) -> None:
        """Construct canvas and draw capsule polygon, beam, and text."""
        w = self.width
        h = self.height
        r = self.radius

        self.canvas = tk.Canvas(
            self.root,
            width=w,
            height=h,
            bg=self.theme.window_bg,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 1. Base capsule polygon (clean dark fill)
        points = generate_capsule_points(w, h, r)
        self.capsule_id = self.canvas.create_polygon(
            points,
            fill=self.theme.idle_fill,
            outline=self.theme.idle_border,
            width=2,
        )

        # 2. Animated Border Beam (runs only on hover)
        self._perimeter_path = generate_perimeter_path(w, h, r)
        self.beam_body_id = self.canvas.create_line(
            0,
            0,
            0,
            0,
            fill=self.theme.beam_body,
            width=3.5,
            capstyle="round",
            joinstyle="round",
        )
        self.beam_head_id = self.canvas.create_line(
            0,
            0,
            0,
            0,
            fill=self.theme.beam_head,
            width=4.5,
            capstyle="round",
        )

        # 3. Content items: Alert indicator icon + PLUS-ULTRA text
        self._bell_icon = get_icon("fallback", 18)
        self.bell_id = self.canvas.create_image(
            52,
            h // 2,
            image=self._bell_icon,
            state="hidden",
        )

        self.idle_text_id = self.canvas.create_text(
            w // 2,
            h // 2,
            text="PLUS-ULTRA",
            fill=self.theme.idle_text,
            font=(self.theme.font_family, self.theme.font_size, "bold"),
        )

        # 4. Small network status indicator dot on right side of capsule
        self.net_dot_id = self.canvas.create_oval(
            w - 28,
            (h // 2) - 4,
            w - 20,
            (h // 2) + 4,
            fill="#10b981",
            outline="",
            state="hidden",
        )

        # Apply initial XWayland shape mask to eliminate square corners
        self.root.update_idletasks()
        apply_window_shape_mask(self.root.winfo_id(), w, h, r)

    def _bind_events(self) -> None:
        """Bind mouse drag, hover, click, and keyboard events."""
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)
        self.root.bind("<Escape>", lambda _e: self.close())

    def _on_enter(self, _event: tk.Event[Any]) -> None:
        """Handle mouse hover entrance: start trailing beam."""
        self._is_hovered = True
        self.canvas.itemconfig(self.idle_text_id, fill=self.theme.hover_text)
        if self.glow_enabled:
            self._start_beam()

    def _on_leave(self, _event: tk.Event[Any]) -> None:
        """Handle mouse hover exit: stop trailing beam and restore border."""
        self._is_hovered = False
        self.canvas.itemconfig(self.idle_text_id, fill=self.theme.idle_text)
        self._stop_beam()
        border = (
            self.theme.hover_border
            if self._active_toggle
            else self.theme.idle_border
        )
        self.canvas.itemconfig(
            self.capsule_id, fill=self.theme.idle_fill, outline=border
        )

    def _start_beam(self) -> None:
        """Start the orbiting beam animation loop on hover."""
        if self._beam_timer_id is None and not self._closed:
            self._tick_beam()

    def _stop_beam(self) -> None:
        """Stop orbiting beam and clear line coordinates when not hovered."""
        if self._beam_timer_id is not None:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._beam_timer_id)
            self._beam_timer_id = None
        self.canvas.coords(self.beam_body_id, 0, 0, 0, 0)
        self.canvas.coords(self.beam_head_id, 0, 0, 0, 0)

    def _tick_beam(self) -> None:
        """Advance Animated Border Beam along perimeter path (~40 FPS)."""
        if self._closed or not self._is_hovered:
            return

        total_pts = len(self._perimeter_path)
        if total_pts > 0 and self.glow_enabled:
            self._beam_idx = (self._beam_idx + 2) % total_pts
            body_coords = [
                c
                for k in range(self._beam_length)
                for c in self._perimeter_path[(self._beam_idx - k) % total_pts]
            ]
            self.canvas.coords(self.beam_body_id, *body_coords)
            head_coords = [
                c
                for k in range(6)
                for c in self._perimeter_path[(self._beam_idx - k) % total_pts]
            ]
            self.canvas.coords(self.beam_head_id, *head_coords)

        self._beam_timer_id = self.root.after(25, self._tick_beam)

    def _on_button_press(self, event: tk.Event[Any]) -> None:
        self._drag_start_x = event.x_root - self.root.winfo_x()
        self._drag_start_y = event.y_root - self.root.winfo_y()
        self._dragged = False

    def _on_motion(self, event: tk.Event[Any]) -> None:
        dx = abs(event.x_root - (self._drag_start_x + self.root.winfo_x()))
        dy = abs(event.y_root - (self._drag_start_y + self.root.winfo_y()))
        if dx > 2 or dy > 2:
            self._dragged = True

        new_x = event.x_root - self._drag_start_x
        new_y = event.y_root - self._drag_start_y
        self.root.geometry(f"{self.width}x{self.height}+{new_x}+{new_y}")
        self.popup_pill.reposition(new_x, new_y, self.width, self.height)

    def _on_button_release(self, _event: tk.Event[Any]) -> None:
        if not self._dragged:
            self._on_click()
        elif self.on_position_change:
            self.on_position_change(self.root.winfo_x(), self.root.winfo_y())

    def _on_click(self) -> None:
        """Toggle active state and trigger click callback."""
        self._active_toggle = not self._active_toggle
        logger.info("Capsule clicked (active toggle: %s)", self._active_toggle)
        if self.on_click_callback:
            self.on_click_callback()

    # --- Notification & Popup Banner Methods ---

    def post_notification(
        self,
        title: str,
        message: str = "",
        icon: str = "",
        notification_id: str | None = None,
    ) -> str:
        """Add notification: shows 3s popup below and displays orange bell."""
        item = self.notifications.push(
            title=title,
            message=message,
            icon=icon,
            notification_id=notification_id,
        )
        self.root.after_idle(lambda: self._handle_new_notification(item))
        return item.id

    def mark_all_read(self) -> None:
        self.notifications.mark_all_read()
        self.root.after_idle(self._update_bell_state)

    def mark_read(self, notification_id: str) -> None:
        self.notifications.mark_read(notification_id)
        self.root.after_idle(self._update_bell_state)

    def clear_notifications(self) -> None:
        self.notifications.clear()
        self.root.after_idle(self._update_bell_state)

    def _handle_new_notification(self, item: CapsuleNotification) -> None:
        """Display orange bell in main capsule and spawn 3-second popup pill."""
        if self._closed:
            return

        self._update_bell_state()
        self._spawn_popup_pill(item)

    def _update_capsule_geometry(self) -> None:
        """Dynamically adjust capsule width based on unread notifications."""
        if self._closed:
            return

        target_w = self.geometry.width
        if self.notifications.has_unread:
            target_w = self.geometry.width + 48

        if target_w != self.width:
            old_w = self.width
            self.width = target_w
            cur_x = self.root.winfo_x()
            cur_y = self.root.winfo_y()
            new_x = cur_x - (target_w - old_w) // 2
            self.root.geometry(f"{self.width}x{self.height}+{new_x}+{cur_y}")
            self.canvas.config(width=self.width)

            points = generate_capsule_points(
                self.width, self.height, self.radius
            )
            self.canvas.coords(self.capsule_id, *points)
            self._perimeter_path = generate_perimeter_path(
                self.width, self.height, self.radius
            )

            self.root.update_idletasks()
            apply_window_shape_mask(
                self.root.winfo_id(), self.width, self.height, self.radius
            )
            if hasattr(self, "net_dot_id"):
                self.canvas.coords(
                    self.net_dot_id,
                    self.width - 28,
                    (self.height // 2) - 4,
                    self.width - 20,
                    (self.height // 2) + 4,
                )

    def _update_bell_state(self) -> None:
        """Show orange bell if unread notifications exist, else center text."""
        if self._closed:
            return

        self._update_capsule_geometry()

        w = self.width
        h = self.height

        if self.notifications.has_unread:
            # Orange bell visible on left; text offset right
            self.canvas.itemconfig(self.bell_id, state="normal")
            self.canvas.coords(self.bell_id, 48, h // 2)
            self.canvas.coords(self.idle_text_id, (w // 2) + 12, h // 2)
        else:
            # All read: bell hidden, text perfectly centered
            self.canvas.itemconfig(self.bell_id, state="hidden")
            self.canvas.coords(self.idle_text_id, w // 2, h // 2)

    @property
    def _popup_window(self) -> tk.Toplevel | None:
        """Expose popup window for backward compatibility with tests."""
        return self.popup_pill.window

    def _spawn_popup_pill(self, item: CapsuleNotification) -> None:
        """Display 3s popup capsule directly below main capsule."""
        if self._closed:
            return
        self.popup_pill.show(
            item=item,
            parent_x=self.root.winfo_x(),
            parent_y=self.root.winfo_y(),
            parent_w=self.width,
            parent_h=self.height,
        )

    def _dismiss_popup_pill(self) -> None:
        """Dismiss the 3-second popup pill window."""
        self.popup_pill.dismiss()

    def _poll_network_status(self) -> None:
        """Poll network connectivity and update indicator dot on capsule."""
        if self._closed:
            return

        eff = settings.load_effective_settings()
        if not eff.get("network_monitor_enabled", True):
            self.canvas.itemconfig(self.net_dot_id, state="hidden")
        else:
            self._net_monitor.probe_async()
            res = self._net_monitor.get_result()
            is_on = res if res is not None else self._net_monitor.last_status
            color = "#10b981" if is_on else "#ef4444"
            self.canvas.itemconfig(self.net_dot_id, fill=color, state="normal")
            self.canvas.coords(
                self.net_dot_id,
                self.width - 28,
                (self.height // 2) - 4,
                self.width - 20,
                (self.height // 2) + 4,
            )

        self._net_poll_timer_id = self.root.after(
            5000, self._poll_network_status
        )

    def close(self) -> None:
        """Destroy window and popup cleanly."""
        logger.info("Closing floating widget window.")
        self._closed = True
        self._dismiss_popup_pill()

        if self._beam_timer_id is not None:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._beam_timer_id)

        if self._net_poll_timer_id is not None:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._net_poll_timer_id)
            self._net_poll_timer_id = None

        if self.on_position_change:
            with contextlib.suppress(Exception):
                self.on_position_change(
                    self.root.winfo_x(), self.root.winfo_y()
                )
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
