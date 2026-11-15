"""Theme definitions, visual styling tokens, and design system for PLUS-ULTRA.

Encapsulates color palettes, capsule geometry, typography, spacing tokens,
and animation properties for the floating desktop widget and dashboard panel.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Spacing Tokens ---
SPACING_XS: int = 4
SPACING_SM: int = 8
SPACING_MD: int = 12
SPACING_LG: int = 16
SPACING_XL: int = 24
SPACING_2XL: int = 32

# --- Color Palette Tokens ---
COLOR_BG_DARK: str = "#12151c"
COLOR_SURFACE: str = "#161922"
COLOR_SURFACE_CARD: str = "#1c212c"
COLOR_SURFACE_HOVER: str = "#242b3a"
COLOR_BORDER: str = "#2b3448"
COLOR_BORDER_FOCUS: str = "#00e5ff"
COLOR_ACCENT: str = "#00e5ff"
COLOR_ACCENT_HOVER: str = "#33ebff"
COLOR_ACCENT_MUTED: str = "#0284c7"
COLOR_TEXT_PRIMARY: str = "#f8fafc"
COLOR_TEXT_SECONDARY: str = "#cbd5e1"
COLOR_TEXT_MUTED: str = "#94a3b8"
COLOR_SUCCESS: str = "#10b981"
COLOR_WARNING: str = "#f59e0b"
COLOR_BELL_ORANGE: str = "#ff9800"
COLOR_DANGER: str = "#ef4444"
COLOR_DANGER_HOVER: str = "#dc2626"

# --- Animation Timing Tokens ---
ANIMATION_FAST_MS: int = 25
ANIMATION_NORMAL_MS: int = 150
ANIMATION_NOTIFICATION_DEFAULT_MS: int = 3000

# --- Typography Tokens ---
FONT_FAMILY: str = "helvetica"
FONT_SIZE_SM: int = 9
FONT_SIZE_BASE: int = 11
FONT_SIZE_MD: int = 13
FONT_SIZE_LG: int = 16
FONT_SIZE_XL: int = 20


@dataclass(frozen=True, slots=True)
class CapsuleGeometry:
    """Mathematically derived dimensions for the top-center floating capsule."""

    width: int = 350
    height: int = 30
    min_width: int = 350
    max_width: int = 900
    top_offset: int = 16

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError(
                f"Capsule width must be positive, got {self.width}"
            )
        if self.height <= 0:
            raise ValueError(
                f"Capsule height must be positive, got {self.height}"
            )
        if self.min_width <= 0 or self.max_width <= 0:
            raise ValueError("Capsule min/max widths must be positive")
        if self.min_width > self.max_width:
            raise ValueError(
                f"min_width ({self.min_width}) "
                f"cannot exceed max_width ({self.max_width})"
            )

    @property
    def radius(self) -> int:
        """Corner radius mathematically derived from: min(w, h) / 2."""
        return min(self.width, self.height) // 2

    @property
    def center_x(self) -> int:
        return self.width // 2

    @property
    def center_y(self) -> int:
        return self.height // 2

    @property
    def bell_center_x(self) -> int:
        """Icon anchor derived relative to left curved semicircular cap."""
        return int(self.radius * 3.4)

    @property
    def net_dot_x(self) -> int:
        """Network dot anchor derived relative to right curved cap."""
        return self.width - int(self.radius * 1.8)


@dataclass(frozen=True, slots=True)
class CapsuleTheme:
    """Color tokens for the floating capsule."""

    window_bg: str = COLOR_BG_DARK
    idle_fill: str = COLOR_SURFACE_CARD
    idle_border: str = COLOR_BORDER
    idle_text: str = COLOR_TEXT_SECONDARY
    hover_fill: str = COLOR_SURFACE_CARD
    hover_border: str = COLOR_ACCENT
    hover_text: str = "#ffffff"
    beam_head: str = "#ffffff"
    beam_body: str = COLOR_ACCENT
    beam_tail: str = COLOR_ACCENT_MUTED
    bell_orange: str = COLOR_BELL_ORANGE
    notification_bg: str = "#182030"
    badge_bg: str = COLOR_ACCENT
    badge_fg: str = "#0a0e17"
    dismiss_fg: str = COLOR_TEXT_MUTED
    dismiss_hover: str = COLOR_DANGER
    popup_bg: str = "#141a24"
    popup_border: str = COLOR_BORDER
    popup_text: str = COLOR_TEXT_PRIMARY
    font_family: str = FONT_FAMILY
    font_size: int = FONT_SIZE_MD


GEOMETRY = CapsuleGeometry()
THEME = CapsuleTheme()

THEME_PALETTES: dict[str, dict[str, str]] = {
    "cyan": {
        "name": "Cyber Cyan",
        "accent": "#00e5ff",
        "hover": "#33ebff",
        "muted": "#0284c7",
    },
    "emerald": {
        "name": "Emerald Matrix",
        "accent": "#10b981",
        "hover": "#34d399",
        "muted": "#059669",
    },
    "purple": {
        "name": "Neon Violet",
        "accent": "#a855f7",
        "hover": "#c084fc",
        "muted": "#7c3aed",
    },
    "amber": {
        "name": "Sunset Amber",
        "accent": "#f59e0b",
        "hover": "#fbbf24",
        "muted": "#d97706",
    },
}


def get_theme_by_name(name: str = "cyan") -> CapsuleTheme:
    """Return a CapsuleTheme configured with the specified accent colors."""
    pal = THEME_PALETTES.get(name.lower(), THEME_PALETTES["cyan"])
    return CapsuleTheme(
        hover_border=pal["accent"],
        beam_body=pal["accent"],
        beam_tail=pal["muted"],
        badge_bg=pal["accent"],
    )

