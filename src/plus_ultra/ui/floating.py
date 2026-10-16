"""Floating desktop capsule widget for PLUS-ULTRA.

Applies OS and UI concepts:
- Dynamic Notification Capsule: Idle compact pill horizontally expandable
  from the center outward when unread notifications arrive.
- Animated Border Beam: Smooth orbiting light beam around the perimeter.
- Event-driven programming: Non-blocking Tkinter animation timers (~40 FPS).
- XWayland Shape Masking: Hardware clipping to eliminate rectangular corners.
- Pointer tracking: Drag gesture delta math preserving center-anchor position.
"""

from __future__ import annotations

import contextlib
import logging
import math
import tkinter as tk
from collections.abc import Callable
from typing import Any

from plus_ultra import settings
from plus_ultra.desktop import apply_window_shape_mask
from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.ui.theme import GEOMETRY, THEME, CapsuleGeometry, CapsuleTheme

logger = logging.getLogger(__name__)


def generate_capsule_points(
    w: int, h: int, r: int, steps: int = 24
) -> list[float]:
    """Generate exact coordinates for a horizontal capsule polygon."""
    points: list[float] = []

    # 1. Top straight edge: left to right
    points.extend([float(r), 1.0, float(w - r), 1.0])

    # 2. Right semicircle: -pi/2 to pi/2
    cx, cy = float(w - r), float(h) / 2.0
    for i in range(steps + 1):
        theta = -math.pi / 2.0 + (math.pi * i / steps)
        points.extend(
            [cx + (r - 1) * math.cos(theta), cy + (r - 1) * math.sin(theta)]
        )

    # 3. Bottom straight edge: right to left
    points.extend([float(w - r), float(h - 1), float(r), float(h - 1)])

    # 4. Left semicircle: pi/2 to 3*pi/2
    cx, cy = float(r), float(h) / 2.0
    for i in range(steps + 1):
        theta = math.pi / 2.0 + (math.pi * i / steps)
        points.extend(
            [cx + (r - 1) * math.cos(theta), cy + (r - 1) * math.sin(theta)]
        )

    return points


def generate_perimeter_path(
    w: int, h: int, r: int, num_arc_points: int = 24
) -> list[tuple[float, float]]:
    """Generate ordered 2D perimeter points for the animated border beam."""
    path: list[tuple[float, float]] = []

    # 1. Top edge: left to right (step by 2px)
    for x in range(r, w - r + 1, 2):
        path.append((float(x), 1.5))

    # 2. Right semicircle: -pi/2 to pi/2
    cx, cy = float(w - r), float(h) / 2.0
    for i in range(1, num_arc_points + 1):
        theta = -math.pi / 2.0 + (math.pi * i / num_arc_points)
        path.append(
            (cx + (r - 1.5) * math.cos(theta), cy + (r - 1.5) * math.sin(theta))
        )

    # 3. Bottom edge: right to left (step by 2px)
    for x in range(w - r, r - 1, -2):
        path.append((float(x), float(h - 1.5)))

    # 4. Left semicircle: pi/2 to 3*pi/2
    cx, cy = float(r), float(h) / 2.0
    for i in range(1, num_arc_points + 1):
        theta = math.pi / 2.0 + (math.pi * i / num_arc_points)
        path.append(
            (cx + (r - 1.5) * math.cos(theta), cy + (r - 1.5) * math.sin(theta))
        )

    return path


class FloatingWidget:
    """Always-on-top hovering capsule widget with animated border beam."""

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

        # Dynamic Notification Queue
        self.notifications = CapsuleNotificationQueue(
            min_width=self.geometry.min_width,
            max_width=self.geometry.max_width,
        )

        # Dynamic Sizing & Center-Outward State
        self.current_width: float = float(self.geometry.min_width)
        self.target_width: float = float(self.geometry.min_width)
        self.height: int = self.geometry.height
        self.radius: int = self.geometry.radius

        # Mouse & Animation Tracking
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0
        self._dragged: bool = False
        self._is_hovered: bool = False
        self._active_toggle: bool = False
        self._beam_idx: int = 0
        self._beam_length: int = 34
        self._resize_timer_id: str | None = None
        self._beam_timer_id: str | None = None
        self._closed: bool = False

        self._load_preferences()
        self._setup_window()
        self._build_canvas()
        self._bind_events()
        self._start_animations()

    def _load_preferences(self) -> None:
        """Load user preferences for window stacking and animations."""
        eff: dict[str, Any] = settings.load_effective_settings()
        self.always_on_top: bool = eff.get("always_on_top", True)
        self.glow_enabled: bool = eff.get("glow_enabled", True)

    def _setup_window(self) -> None:
        """Configure borderless window placement at top-center of screen."""
        self.root.overrideredirect(True)
        if self.always_on_top:
            self.root.attributes("-topmost", True)

        screen_w = self.root.winfo_screenwidth()
        default_x = (screen_w - int(self.current_width)) // 2
        default_y = self.geometry.top_offset
        init_x = self.initial_x if self.initial_x is not None else default_x
        init_y = self.initial_y if self.initial_y is not None else default_y

        # Anchor center preserves center-outward resizing
        self.anchor_center_x: int = init_x + int(self.current_width // 2)

        self.root.geometry(
            f"{int(self.current_width)}x{self.height}+{init_x}+{init_y}"
        )
        self.root.configure(bg=self.theme.window_bg)

    def _build_canvas(self) -> None:
        """Construct canvas and draw capsule polygon, beam, and text."""
        w = int(self.current_width)
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

        # 1. Base capsule polygon
        points = generate_capsule_points(w, h, r)
        self.capsule_id = self.canvas.create_polygon(
            points,
            fill=self.theme.idle_fill,
            outline=self.theme.idle_border,
            width=2,
        )

        # 2. Animated Border Beam (smooth running beam orbiting the contour)
        self._perimeter_path = generate_perimeter_path(w, h, r)
        self.beam_body_id = self.canvas.create_line(
            0,
            0,
            0,
            0,
            fill=self.theme.beam_body,
            width=2.5,
            capstyle="round",
            joinstyle="round",
        )
        self.beam_head_id = self.canvas.create_line(
            0,
            0,
            0,
            0,
            fill=self.theme.beam_head,
            width=3.0,
            capstyle="round",
        )

        # 3. Content items
        self.idle_text_id = self.canvas.create_text(
            w // 2,
            h // 2,
            text="PLUS-ULTRA",
            fill=self.theme.idle_text,
            font=(self.theme.font_family, self.theme.font_size, "bold"),
        )

        self.icon_id = self.canvas.create_text(
            22,
            h // 2,
            text="",
            fill=self.theme.hover_border,
            font=(self.theme.font_family, self.theme.font_size + 2),
            state="hidden",
        )

        self.preview_text_id = self.canvas.create_text(
            44,
            h // 2,
            text="",
            anchor="w",
            fill=self.theme.hover_text,
            font=(self.theme.font_family, self.theme.font_size),
            state="hidden",
        )

        self.badge_id = self.canvas.create_text(
            w - 42,
            h // 2,
            text="",
            fill=self.theme.badge_bg,
            font=(self.theme.font_family, self.theme.font_size - 1, "bold"),
            state="hidden",
        )

        self.dismiss_id = self.canvas.create_text(
            w - 20,
            h // 2,
            text="✕",
            fill=self.theme.dismiss_fg,
            font=(self.theme.font_family, self.theme.font_size, "bold"),
            state="hidden",
            tags="dismiss_btn",
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
        self.canvas.bind("<Button-3>", lambda _e: self._demo_notification())
        self.root.bind("<n>", lambda _e: self._demo_notification())
        self.root.bind("<Escape>", lambda _e: self.close())

        # Specific binding for the dismiss button
        self.canvas.tag_bind("dismiss_btn", "<Enter>", self._on_dismiss_enter)
        self.canvas.tag_bind("dismiss_btn", "<Leave>", self._on_dismiss_leave)
        self.canvas.tag_bind(
            "dismiss_btn", "<Button-1>", self._on_dismiss_click
        )

    def _demo_notification(self) -> None:
        """Trigger a sample notification for interactive verification."""
        samples = [
            ("Assignment Due", "OS Lab 3 due in 30 mins", "📅"),
            ("LeetCode Daily", "Binary Search Trees challenge ready", "💻"),
            ("Hackathon Update", "Team application approved", "🚀"),
        ]
        sample = samples[self.notifications.count % len(samples)]
        self.post_notification(sample[0], sample[1], icon=sample[2])

    def _start_animations(self) -> None:
        """Launch continuous non-blocking animation loops."""
        self._tick_beam()

    def _tick_beam(self) -> None:
        """Advance Animated Border Beam along perimeter path (~40 FPS)."""
        if self._closed:
            return

        total_pts = len(self._perimeter_path)
        if total_pts > 0 and self.glow_enabled:
            # Advance beam index
            speed = 3 if self._is_hovered else 2
            self._beam_idx = (self._beam_idx + speed) % total_pts

            # Body coordinates (trailing tail)
            body_coords: list[float] = []
            for k in range(self._beam_length):
                idx = (self._beam_idx - k) % total_pts
                body_coords.extend(self._perimeter_path[idx])
            self.canvas.coords(self.beam_body_id, *body_coords)

            # Head coordinates (bright leading tip)
            head_coords: list[float] = []
            for k in range(6):
                idx = (self._beam_idx - k) % total_pts
                head_coords.extend(self._perimeter_path[idx])
            self.canvas.coords(self.beam_head_id, *head_coords)

        self._beam_timer_id = self.root.after(25, self._tick_beam)

    def _on_enter(self, _event: tk.Event[Any]) -> None:
        """Handle mouse hover entrance with glow styling."""
        self._is_hovered = True
        if self.glow_enabled:
            fill_color = (
                self.theme.notification_bg
                if not self.notifications.is_empty
                else self.theme.hover_fill
            )
            self.canvas.itemconfig(
                self.capsule_id,
                fill=fill_color,
                outline=self.theme.hover_border,
            )
            self.canvas.itemconfig(
                self.idle_text_id, fill=self.theme.hover_text
            )

    def _on_leave(self, _event: tk.Event[Any]) -> None:
        """Handle mouse hover exit returning to idle styling."""
        self._is_hovered = False
        fill_color = (
            self.theme.notification_bg
            if not self.notifications.is_empty
            else self.theme.idle_fill
        )
        idle_border = (
            self.theme.hover_border
            if self._active_toggle
            else self.theme.idle_border
        )
        self.canvas.itemconfig(
            self.capsule_id,
            fill=fill_color,
            outline=idle_border,
        )
        self.canvas.itemconfig(self.idle_text_id, fill=self.theme.idle_text)

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

        # Update anchor center during drag so future resizing respects location
        self.anchor_center_x = new_x + int(self.current_width // 2)

        self.root.geometry(
            f"{int(self.current_width)}x{self.height}+{new_x}+{new_y}"
        )

    def _on_button_release(self, _event: tk.Event[Any]) -> None:
        """Handle click when mouse was released without dragging."""
        if not self._dragged:
            self._on_click()
        elif self.on_position_change:
            self.on_position_change(self.root.winfo_x(), self.root.winfo_y())

    def _on_dismiss_enter(self, _event: tk.Event[Any]) -> None:
        """Highlight dismiss button on hover."""
        self.canvas.itemconfig(self.dismiss_id, fill=self.theme.dismiss_hover)

    def _on_dismiss_leave(self, _event: tk.Event[Any]) -> None:
        """Restore dismiss button idle color."""
        self.canvas.itemconfig(self.dismiss_id, fill=self.theme.dismiss_fg)

    def _on_dismiss_click(self, _event: tk.Event[Any]) -> None:
        """Dismiss current notification and recalculate dimensions."""
        self.dismiss_current()

    def _on_click(self) -> None:
        """Toggle active state and trigger click callback."""
        self._active_toggle = not self._active_toggle
        logger.info("Capsule clicked (active toggle: %s)", self._active_toggle)
        if self.on_click_callback:
            self.on_click_callback()

    # --- Dynamic Notification & Sizing Methods ---

    def post_notification(
        self,
        title: str,
        message: str = "",
        icon: str = "🔔",
        action_label: str = "View",
        notification_id: str | None = None,
    ) -> str:
        """Add notification (thread-safe); smoothly expands capsule outward."""
        item = self.notifications.push(
            title=title,
            message=message,
            icon=icon,
            action_label=action_label,
            notification_id=notification_id,
        )
        self.root.after_idle(self._trigger_layout_update)
        return item.id

    def dismiss_notification(self, notification_id: str) -> None:
        """Dismiss a specific notification by ID (thread-safe)."""
        self.notifications.dismiss(notification_id)
        self.root.after_idle(self._trigger_layout_update)

    def dismiss_current(self) -> None:
        """Dismiss the top notification (thread-safe)."""
        self.notifications.dismiss_current()
        self.root.after_idle(self._trigger_layout_update)

    def clear_notifications(self) -> None:
        """Clear all notifications and shrink back to idle pill."""
        self.notifications.clear()
        self.root.after_idle(self._trigger_layout_update)

    def _trigger_layout_update(self) -> None:
        """Update target width and initiate smooth resize animation."""
        if self._closed:
            return
        self.target_width = float(self.notifications.compute_target_width())
        self._step_resize()

    def _step_resize(self) -> None:
        """Smoothly interpolate current width toward target width."""
        if self._closed:
            return

        diff = self.target_width - self.current_width
        if abs(diff) > 0.8:
            step = diff * 0.28
            if abs(step) < 1.0:
                step = 1.0 if diff > 0 else -1.0
            self.current_width += step

            self._apply_geometry_and_layout()
            self._resize_timer_id = self.root.after(16, self._step_resize)
        else:
            self.current_width = self.target_width
            self._apply_geometry_and_layout()
            # Reapply shape mask on animation finish
            apply_window_shape_mask(
                self.root.winfo_id(),
                int(self.current_width),
                self.height,
                self.radius,
            )

    def _apply_geometry_and_layout(self) -> None:
        """Apply center-outward window coordinates and redraw canvas."""
        w = int(self.current_width)
        h = self.height
        r = self.radius

        # Center-outward calculation: anchor_center_x is preserved
        screen_w = self.root.winfo_screenwidth()
        new_x = int(round(self.anchor_center_x - w / 2))
        new_x = max(4, min(screen_w - w - 4, new_x))
        new_y = self.root.winfo_y()

        self.root.geometry(f"{w}x{h}+{new_x}+{new_y}")
        self.canvas.configure(width=w)

        # Redraw capsule polygon with true semicircles
        points = generate_capsule_points(w, h, r)
        self.canvas.coords(self.capsule_id, *points)

        # Rebuild perimeter path for the animated border beam
        self._perimeter_path = generate_perimeter_path(w, h, r)

        # Update content presentation
        self._update_content_presentation(w, h)

    def _update_content_presentation(self, w: int, h: int) -> None:
        """Update content visibility and text alignment based on state."""
        top = self.notifications.peek()
        if not top:
            # Idle Mode: centered PLUS-ULTRA
            self.canvas.coords(self.idle_text_id, w // 2, h // 2)
            self.canvas.itemconfig(self.idle_text_id, state="normal")
            self.canvas.itemconfig(self.icon_id, state="hidden")
            self.canvas.itemconfig(self.preview_text_id, state="hidden")
            self.canvas.itemconfig(self.badge_id, state="hidden")
            self.canvas.itemconfig(self.dismiss_id, state="hidden")
            self.canvas.itemconfig(
                self.capsule_id,
                fill=self.theme.hover_fill
                if self._is_hovered
                else self.theme.idle_fill,
            )
        else:
            # Notification Mode: icon, truncated text, optional badge, dismiss
            self.canvas.itemconfig(self.idle_text_id, state="hidden")
            self.canvas.itemconfig(
                self.capsule_id, fill=self.theme.notification_bg
            )

            # 1. Icon
            self.canvas.coords(self.icon_id, 24, h // 2)
            self.canvas.itemconfig(self.icon_id, text=top.icon, state="normal")

            # 2. Dismiss Button
            dismiss_x = w - 20
            self.canvas.coords(self.dismiss_id, dismiss_x, h // 2)
            self.canvas.itemconfig(self.dismiss_id, state="normal")

            # 3. Badge if multiple unread
            right_boundary = dismiss_x - 14
            if self.notifications.count > 1:
                badge_text = f"+{self.notifications.count - 1}"
                badge_x = dismiss_x - 22
                self.canvas.coords(self.badge_id, badge_x, h // 2)
                self.canvas.itemconfig(
                    self.badge_id, text=badge_text, state="normal"
                )
                right_boundary = badge_x - 16
            else:
                self.canvas.itemconfig(self.badge_id, state="hidden")

            # 4. Preview Text (Title + Message truncated)
            text_x = 44
            available_text_w = max(40, right_boundary - text_x)
            formatted = self.notifications.format_display_text(available_text_w)
            self.canvas.coords(self.preview_text_id, text_x, h // 2)
            self.canvas.itemconfig(
                self.preview_text_id, text=formatted, state="normal"
            )

    def close(self) -> None:
        """Destroy window and terminate animation loops cleanly."""
        logger.info("Closing floating widget window.")
        self._closed = True
        if self._beam_timer_id is not None:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._beam_timer_id)
        if self._resize_timer_id is not None:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._resize_timer_id)

        if self.on_position_change:
            with contextlib.suppress(Exception):
                self.on_position_change(
                    self.root.winfo_x(), self.root.winfo_y()
                )
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
