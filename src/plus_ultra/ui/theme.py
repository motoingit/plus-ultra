"""Theme definitions and visual styling tokens for PLUS-ULTRA.

Encapsulates color palettes, capsule dimensions, typography, and glow
animation properties for the floating desktop widget.
"""

from __future__ import annotations

from typing import NamedTuple


class CapsuleGeometry(NamedTuple):
    """Dimensions for the top-center floating capsule."""

    min_width: int = 320
    width: int = 320
    max_width: int = 880
    height: int = 72
    radius: int = 36
    top_offset: int = 16


class CapsuleTheme(NamedTuple):
    """Color tokens for the floating capsule."""

    window_bg: str = "#12151c"
    idle_fill: str = "#1a1f2c"
    idle_border: str = "#2b3448"
    idle_text: str = "#cbd5e1"
    hover_fill: str = "#1a1f2c"  # Clean dark fill (no static glow)
    hover_border: str = "#00e5ff"
    hover_text: str = "#ffffff"
    beam_head: str = "#ffffff"  # Luminous tip of running beam
    beam_body: str = "#00e5ff"  # Core electric cyan running beam
    beam_tail: str = "#0284c7"  # Smooth gradient tail
    bell_orange: str = "#ff9800"  # Unread notification bell indicator
    notification_bg: str = "#182030"
    badge_bg: str = "#00e5ff"
    badge_fg: str = "#0a0e17"
    dismiss_fg: str = "#94a3b8"
    dismiss_hover: str = "#f43f5e"
    popup_bg: str = "#141a24"
    popup_border: str = "#2b3448"
    popup_text: str = "#f8fafc"
    font_family: str = "helvetica"
    font_size: int = 13


GEOMETRY = CapsuleGeometry()
THEME = CapsuleTheme()
