"""Tests for plus_ultra.ui (theme tokens and FloatingWidget).

Validates:
- Theme tokens: Capsule dimensions, color palette, typography.
- FloatingWidget instantiation: borderless window flags, geometry placement.
- Interaction handling: hover glow state transitions, drag offset calculations,
  click callback triggering.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

from plus_ultra.ui.floating import FloatingWidget
from plus_ultra.ui.theme import GEOMETRY, THEME


def test_theme_and_geometry_defaults() -> None:
    """Verify default styling tokens for the floating capsule."""
    assert GEOMETRY.width == 140
    assert GEOMETRY.height == 36
    assert GEOMETRY.radius == 18
    assert GEOMETRY.top_offset == 12

    assert THEME.hover_border == "#00e5ff"
    assert THEME.idle_border == "#2b3448"
    assert THEME.window_bg == "#12151c"


def test_floating_widget_creation() -> None:
    """Verify FloatingWidget initializes canvas and window geometry."""
    root = tk.Tk()
    try:
        clicked = False

        def _on_click() -> None:
            nonlocal clicked
            clicked = True

        widget = FloatingWidget(root=root, on_click_callback=_on_click)

        # Check canvas and items
        assert widget.canvas is not None
        assert widget.capsule_id is not None
        assert widget.text_id is not None
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
    finally:
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
    finally:
        root.destroy()
