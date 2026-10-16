"""Tests for plus_ultra.ui (theme tokens, FloatingWidget, and Dynamic Capsule).

Validates:
- Theme tokens: Capsule dimensions, color palette, typography.
- FloatingWidget instantiation: borderless window flags, geometry placement.
- Mathematical capsule points and perimeter trajectory generation.
- Animated Border Beam canvas elements.
- Dynamic notification expansion, badge display, and dismissal.
- Center-outward expansion anchor calculation.
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


def test_capsule_points_and_perimeter_generators() -> None:
    """Verify mathematical capsule point and perimeter generation."""
    points = generate_capsule_points(160, 36, 18, steps=16)
    assert len(points) > 20
    # Coordinates must be within bounds [0, 160] and [0, 36]
    xs = points[0::2]
    ys = points[1::2]
    assert min(xs) >= 0.0 and max(xs) <= 160.0
    assert min(ys) >= 0.0 and max(ys) <= 36.0

    path = generate_perimeter_path(160, 36, 18)
    assert len(path) > 50
    # Path forms a continuous closed perimeter
    for px, py in path:
        assert 0.0 <= px <= 160.0
        assert 0.0 <= py <= 36.0


def test_floating_widget_creation() -> None:
    """Verify FloatingWidget initializes canvas, beam, and text."""
    root = tk.Tk()
    try:
        clicked = False

        def _on_click() -> None:
            nonlocal clicked
            clicked = True

        widget = FloatingWidget(root=root, on_click_callback=_on_click)

        # Check canvas and visual items
        assert widget.canvas is not None
        assert widget.capsule_id is not None
        assert widget.beam_body_id is not None
        assert widget.beam_head_id is not None
        assert widget.idle_text_id is not None
        assert widget.always_on_top is True

        # Test hover event handling
        dummy_event: tk.Event[Any] = tk.Event()
        widget._on_enter(dummy_event)
        assert widget._is_hovered is True

        widget._on_leave(dummy_event)
        assert widget._is_hovered is False

        # Test click triggering
        widget._dragged = False
        widget._on_button_release(dummy_event)
        assert clicked is True
        assert widget._active_toggle is True
        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_drag_calculation() -> None:
    """Verify drag offset calculation updates anchor center."""
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
        # Anchor center must reflect dragged location
        expected_center = (
            motion_event.x_root
            - widget._drag_start_x
            + int(widget.current_width // 2)
        )
        assert widget.anchor_center_x == expected_center
        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_notification_expansion_and_dismiss() -> None:
    """Verify posting a notification expands the capsule and dismiss shrinks."""
    root = tk.Tk()
    try:
        widget = FloatingWidget(root=root)
        assert widget.notifications.is_empty is True
        assert widget.target_width == widget.geometry.min_width

        # Post a notification
        nid = widget.post_notification(
            "Task Deadline", "Complete Phase 3 tests", icon="📌"
        )
        assert widget.notifications.count == 1
        widget._trigger_layout_update()
        assert widget.target_width > widget.geometry.min_width

        # Step resize to completion
        widget.current_width = widget.target_width
        widget._apply_geometry_and_layout()
        assert widget.canvas.itemcget(widget.idle_text_id, "state") == "hidden"
        assert (
            widget.canvas.itemcget(widget.preview_text_id, "state") == "normal"
        )

        # Dismiss notification
        widget.dismiss_notification(nid)
        assert widget.notifications.is_empty is True
        widget._trigger_layout_update()
        assert widget.target_width == widget.geometry.min_width

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
        assert widget.anchor_center_x == 320 + int(widget.current_width // 2)

        # Simulate release after drag
        widget._dragged = True
        dummy_event: tk.Event[Any] = tk.Event()
        widget._on_button_release(dummy_event)

        assert len(recorded_pos) == 1
        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()
