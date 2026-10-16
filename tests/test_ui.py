"""Tests for plus_ultra.ui (theme tokens, FloatingWidget, and popup capsule).

Validates:
- Theme tokens: Capsule dimensions, color palette, typography.
- FloatingWidget instantiation: borderless window flags, geometry placement.
- Mathematical capsule points and perimeter trajectory generation.
- Hover-driven Animated Border Beam (runs only on hover).
- Orange bell indicator visibility based on unread notification state.
- Position saving and restoration callbacks.
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any

from plus_ultra.ui.floating import (
    FloatingWidget,
    generate_capsule_points,
    generate_perimeter_path,
)
from plus_ultra.ui.theme import GEOMETRY, THEME


def test_theme_and_geometry_defaults() -> None:
    """Verify default styling tokens for the floating capsule."""
    assert GEOMETRY.min_width == 160
    assert GEOMETRY.max_width == 440
    assert GEOMETRY.width == 160
    assert GEOMETRY.height == 36
    assert GEOMETRY.radius == 18
    assert GEOMETRY.top_offset == 12

    assert THEME.hover_border == "#00e5ff"
    assert THEME.idle_border == "#2b3448"
    assert THEME.window_bg == "#12151c"
    assert THEME.beam_body == "#00e5ff"
    assert THEME.beam_head == "#ffffff"
    assert THEME.bell_orange == "#ff9800"


def test_capsule_points_and_perimeter_generators() -> None:
    """Verify mathematical capsule point and perimeter generation."""
    points = generate_capsule_points(160, 36, 18, steps=16)
    assert len(points) > 20
    xs = points[0::2]
    ys = points[1::2]
    assert min(xs) >= 0.0 and max(xs) <= 160.0
    assert min(ys) >= 0.0 and max(ys) <= 36.0

    path = generate_perimeter_path(160, 36, 18)
    assert len(path) > 50
    for px, py in path:
        assert 0.0 <= px <= 160.0
        assert 0.0 <= py <= 36.0


def test_floating_widget_creation_and_click() -> None:
    """Verify FloatingWidget initializes canvas, beam, and bell."""
    root = tk.Tk()
    try:
        clicked = False

        def _on_click() -> None:
            nonlocal clicked
            clicked = True

        widget = FloatingWidget(root=root, on_click_callback=_on_click)

        assert widget.canvas is not None
        assert widget.capsule_id is not None
        assert widget.beam_body_id is not None
        assert widget.beam_head_id is not None
        assert widget.idle_text_id is not None
        assert widget.bell_id is not None
        assert widget.always_on_top is True

        # Initially bell is hidden
        assert widget.canvas.itemcget(widget.bell_id, "state") == "hidden"

        # Test click triggering
        widget._dragged = False
        dummy_event: tk.Event[Any] = tk.Event()
        widget._on_button_release(dummy_event)
        assert clicked is True
        assert widget._active_toggle is True
        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_hover_runs_beam() -> None:
    """Verify beam runs exclusively when mouse hovers over the capsule."""
    root = tk.Tk()
    try:
        widget = FloatingWidget(root=root)
        dummy_event: tk.Event[Any] = tk.Event()

        # Idle: not hovered, beam timer stopped
        assert widget._is_hovered is False

        # Hover entrance: starts beam
        widget._on_enter(dummy_event)
        assert widget._is_hovered is True
        assert widget._beam_timer_id is not None

        # Hover exit: stops beam and clears beam coords
        widget._on_leave(dummy_event)
        assert widget._is_hovered is False
        assert widget._beam_timer_id is None
        assert widget.canvas.coords(widget.beam_body_id) == [0.0, 0.0, 0.0, 0.0]

        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_unread_bell_indicator() -> None:
    """Verify orange bell appears on unread notification and hides when read."""
    root = tk.Tk()
    try:
        widget = FloatingWidget(root=root)
        assert widget.notifications.has_unread is False
        assert widget.canvas.itemcget(widget.bell_id, "state") == "hidden"

        # Post notification -> unread bell visible
        widget.post_notification("Assignment Due", "OS Lab 3 due in 30m")
        assert widget.notifications.has_unread is True
        widget._update_bell_state()
        assert widget.canvas.itemcget(widget.bell_id, "state") == "normal"

        # Mark all read -> bell hides
        widget.mark_all_read()
        assert widget.notifications.has_unread is False
        widget._update_bell_state()
        assert widget.canvas.itemcget(widget.bell_id, "state") == "hidden"

        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_drag_calculation() -> None:
    """Verify drag offset calculation updates window geometry."""
    root = tk.Tk()
    try:
        widget = FloatingWidget(root=root)

        press_event: tk.Event[Any] = tk.Event()
        press_event.x_root = 200
        press_event.y_root = 100
        widget._on_button_press(press_event)

        assert widget._drag_start_x == press_event.x_root - root.winfo_x()
        assert widget._drag_start_y == press_event.y_root - root.winfo_y()

        motion_event: tk.Event[Any] = tk.Event()
        motion_event.x_root = 250
        motion_event.y_root = 120
        widget._on_motion(motion_event)

        assert widget._dragged is True
        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_saved_position_and_callback() -> None:
    """Verify FloatingWidget accepts initial position and fires callback."""
    root = tk.Tk()
    try:
        recorded_pos: list[tuple[int, int]] = []

        def _on_pos(x: int, y: int) -> None:
            recorded_pos.append((x, y))

        widget = FloatingWidget(
            root=root,
            initial_x=320,
            initial_y=45,
            on_position_change=_on_pos,
        )

        assert widget.initial_x == 320
        assert widget.initial_y == 45

        widget._dragged = True
        dummy_event: tk.Event[Any] = tk.Event()
        widget._on_button_release(dummy_event)

        assert len(recorded_pos) == 1
        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()
