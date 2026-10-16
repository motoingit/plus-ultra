"""Theme definitions and visual styling tokens for PLUS-ULTRA.

Encapsulates color palettes, capsule dimensions, typography, and glow
animation properties for the floating desktop widget.
"""

from __future__ import annotations

from typing import NamedTuple


class CapsuleGeometry(NamedTuple):
    """Dimensions for the top-center floating capsule."""

    width: int = 140
    height: int = 36
    radius: int = 18
    top_offset: int = 12


class CapsuleTheme(NamedTuple):
    """Color tokens for the floating capsule."""

    window_bg: str = "#12151c"
    idle_fill: str = "#1a1f2c"
    idle_border: str = "#2b3448"
    idle_text: str = "#cbd5e1"
    hover_fill: str = "#242c3d"
    hover_border: str = "#00e5ff"  # Electric cyan glow
    hover_text: str = "#ffffff"
    font_family: str = "DejaVu Sans"
    font_size: int = 9


GEOMETRY = CapsuleGeometry()
THEME = CapsuleTheme()
