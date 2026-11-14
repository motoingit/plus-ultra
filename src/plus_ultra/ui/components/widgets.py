"""Reusable modern UI widgets and design-system components for PLUS-ULTRA.

Applies UI design system concepts:
- Consistent states: hover, active, pressed, and disabled visual feedback.
- Design tokens: colors, spacing, borders, and typography derived from theme.py.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

from plus_ultra.ui.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_BG_DARK,
    COLOR_BORDER,
    COLOR_BORDER_FOCUS,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_SURFACE,
    COLOR_SURFACE_CARD,
    COLOR_SURFACE_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_SIZE_BASE,
    FONT_SIZE_SM,
    SPACING_MD,
    SPACING_SM,
)


class StyledButton(tk.Button):
    """Button widget with modern flat styling, hover transitions, and semantic roles."""

    def __init__(
        self,
        master: tk.Widget,
        text: str = "",
        command: Callable[[], None] | None = None,
        role: str = "primary",  # primary, secondary, danger, ghost
        font_size: int = FONT_SIZE_BASE,
        padx: int = 14,
        pady: int = 6,
        **kwargs: Any,
    ) -> None:
        self.role = role
        self._normal_bg, self._hover_bg, self._fg = self._resolve_colors(role)

        super().__init__(
            master,
            text=text,
            command=command,
            bg=self._normal_bg,
            fg=self._fg,
            activebackground=self._hover_bg,
            activeforeground=self._fg,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_BORDER_FOCUS,
            font=(FONT_FAMILY, font_size, "bold" if role != "ghost" else "normal"),
            cursor="hand2",
            padx=padx,
            pady=pady,
            **kwargs,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _resolve_colors(self, role: str) -> tuple[str, str, str]:
        if role == "primary":
            return COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_BG_DARK
        if role == "danger":
            return COLOR_DANGER, COLOR_DANGER_HOVER, COLOR_TEXT_PRIMARY
        if role == "ghost":
            return "transparent", COLOR_SURFACE_HOVER, COLOR_TEXT_SECONDARY
        # secondary
        return COLOR_SURFACE_CARD, COLOR_SURFACE_HOVER, COLOR_TEXT_PRIMARY

    def _on_enter(self, _e: tk.Event[Any]) -> None:
        if self["state"] != "disabled":
            self.configure(bg=self._hover_bg)

    def _on_leave(self, _e: tk.Event[Any]) -> None:
        if self["state"] != "disabled":
            self.configure(bg=self._normal_bg)


class Card(tk.Frame):
    """Uniform container card with dark styling, border outline, and padding."""

    def __init__(
        self,
        master: tk.Widget,
        padx: int = 20,
        pady: int = 16,
        bg: str = COLOR_SURFACE_CARD,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            bg=bg,
            padx=padx,
            pady=pady,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            **kwargs,
        )


class SearchBar(tk.Frame):
    """Reusable search bar with input entry, label icon, and clear action."""

    def __init__(
        self,
        master: tk.Widget,
        placeholder: str = "Search...",
        on_search: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, bg=COLOR_SURFACE_CARD, **kwargs)
        self.on_search = on_search

        self.configure(
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            padx=SPACING_SM,
            pady=SPACING_SM // 2,
        )

        tk.Label(
            self,
            text="🔍",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        ).pack(side="left", padx=(0, 6))

        self.entry = tk.Entry(
            self,
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_ACCENT,
            relief="flat",
            bd=0,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<KeyRelease>", self._on_key_release)

    def _on_key_release(self, _e: tk.Event[Any]) -> None:
        if self.on_search:
            self.on_search(self.get_text())

    def get_text(self) -> str:
        return self.entry.get().strip()

    def set_text(self, text: str) -> None:
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        if self.on_search:
            self.on_search(text)

    def clear(self) -> None:
        self.set_text("")
