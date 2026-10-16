"""Sidebar navigation component for PLUS-ULTRA workspace panel."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class Sidebar:
    """Left navigation sidebar with draggable tabs and clean styling."""

    def __init__(
        self,
        container: tk.Widget,
        theme: CapsuleTheme = THEME,
        on_switch_tab: Callable[[str], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self.container = container
        self.theme = theme
        self.on_switch_tab = on_switch_tab
        self.on_close = on_close
        self.tab_buttons: dict[str, tk.Button] = {}

        self.nav_items: list[tuple[str, str]] = [
            ("Tasks", "Tasks"),
            ("Code", "Code c-p"),
            ("DSA", "DSA Tracker"),
            ("Courses", "Courses"),
            ("Ideas-Doubt", "PS/I"),
            ("Opportunities", "Opportunities"),
            ("Quick Links", "Quick Links"),
        ]

        self._drag_tab_id: str | None = None
        self._drag_start_y: int = 0
        self._is_dragging: bool = False
        self._active_tab: str = "Tasks"

        self._build_ui()

    def _build_ui(self) -> None:
        # App brand header
        brand_frame = tk.Frame(self.container, bg="#12151c", padx=20, pady=24)
        brand_frame.pack(fill="x")

        icon = get_icon("fallback", 24)
        brand_label = tk.Label(
            brand_frame,
            text=" PLUS-ULTRA",
            bg="#12151c",
            fg="#00e5ff",
            font=(self.theme.font_family, 16, "bold"),
            image=icon,
            compound="left",
        )
        brand_label.image = icon  # type: ignore[attr-defined]
        brand_label.pack(anchor="w")

        tk.Label(
            brand_frame,
            text="Workspace & System Assistant",
            bg="#12151c",
            fg="#64748b",
            font=(self.theme.font_family, 10),
        ).pack(anchor="w", pady=(4, 0))

        # Nav items container
        self.nav_frame = tk.Frame(
            self.container, bg="#12151c", padx=12, pady=10
        )
        self.nav_frame.pack(fill="both", expand=True)

        self._render_tabs()

        # Bottom section: 5x Enlarge Icon-only Settings button on bottom-left
        bottom_frame = tk.Frame(self.container, bg="#12151c", padx=16, pady=16)
        bottom_frame.pack(side="bottom", fill="x")

        # Fallback to fallback icon if settings icon is missing (5x scale)
        settings_icon = get_icon("settings", 80) or get_icon("fallback", 80)
        self.settings_btn = tk.Button(
            bottom_frame,
            image=settings_icon,
            bg="#12151c",
            activebackground="#1e2433",
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            padx=12,
            pady=12,
            command=lambda: self._on_tab_click("Settings"),
        )
        self.settings_btn.image = settings_icon  # type: ignore[attr-defined]
        self.settings_btn.pack(side="left")

    def _render_tabs(self) -> None:
        """Render navigation tab buttons in current order."""
        for child in self.nav_frame.winfo_children():
            child.destroy()
        self.tab_buttons.clear()

        for tab_id, tab_label in self.nav_items:
            is_active = tab_id == self._active_tab
            btn = tk.Button(
                self.nav_frame,
                text=tab_label,
                anchor="w",
                bg="#1e2433" if is_active else "#12151c",
                fg="#00e5ff" if is_active else "#94a3b8",
                activebackground="#1e2433",
                activeforeground="#00e5ff",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=(
                    self.theme.font_family,
                    13,
                    "bold" if is_active else "normal",
                ),
                cursor="hand2",
                padx=20,
                pady=16,
            )
            btn.pack(fill="x", pady=3)
            self.tab_buttons[tab_id] = btn

            btn.bind(
                "<ButtonPress-1>",
                lambda e, tid=tab_id: self._on_press(e, tid),
            )
            btn.bind("<B1-Motion>", self._on_motion)
            btn.bind(
                "<ButtonRelease-1>",
                lambda e, tid=tab_id: self._on_release(e, tid),
            )

    def _on_press(self, event: tk.Event, tab_id: str) -> None:
        self._drag_tab_id = tab_id
        self._drag_start_y = event.y_root
        self._is_dragging = False

    def _on_motion(self, event: tk.Event) -> None:
        if abs(event.y_root - self._drag_start_y) > 12:
            self._is_dragging = True

    def _on_release(self, event: tk.Event, tab_id: str) -> None:
        if self._is_dragging and self._drag_tab_id:
            self._reorder_tab(self._drag_tab_id, event.y_root)
        else:
            self._on_tab_click(tab_id)
        self._drag_tab_id = None
        self._is_dragging = False

    def _reorder_tab(self, tab_id: str, release_y: int) -> None:
        """Move dragged tab to the slot corresponding to release_y."""
        if not self.tab_buttons:
            return

        current_idx = next(
            (i for i, (tid, _) in enumerate(self.nav_items) if tid == tab_id),
            None,
        )
        if current_idx is None:
            return

        target_idx = current_idx
        for idx, (tid, _) in enumerate(self.nav_items):
            btn = self.tab_buttons.get(tid)
            if btn and btn.winfo_exists() and btn.winfo_rooty() > 0:
                y_center = btn.winfo_rooty() + (btn.winfo_height() // 2)
                if release_y < y_center:
                    target_idx = idx
                    break
        else:
            target_idx = len(self.nav_items) - 1

        if target_idx != current_idx:
            item = self.nav_items.pop(current_idx)
            self.nav_items.insert(target_idx, item)
            self._render_tabs()

    def _on_tab_click(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self.highlight_tab(tab_id)
        if self.on_switch_tab:
            self.on_switch_tab(tab_id)

    def highlight_tab(self, active_tab: str) -> None:
        """Update active button styling across navigation items."""
        self._active_tab = active_tab
        for name, btn in self.tab_buttons.items():
            if name == active_tab:
                btn.configure(
                    bg="#1e2433",
                    fg="#00e5ff",
                    font=(self.theme.font_family, 13, "bold"),
                )
            else:
                btn.configure(
                    bg="#12151c",
                    fg="#94a3b8",
                    font=(self.theme.font_family, 13),
                )
        if hasattr(self, "settings_btn"):
            self.settings_btn.configure(
                bg="#1e2433" if active_tab == "Settings" else "#12151c"
            )
