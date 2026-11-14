"""Preferences, Diagnostics, and System Settings view for PLUS-ULTRA.

Applies Software Architecture & OS concepts:
- Settings categorization: General, Appearance, Notifications, System Integration,
  and Data & Maintenance.
- Runtime application behavior: Updating settings alters active platform state
  (e.g., autostart registry/.desktop, topmost attributes, tray, network monitor).
- Filesystem & Diagnostic transparency: Displays real paths, engine info,
  and provides directory opening actions.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from plus_ultra import config, settings
from plus_ultra.config import get_platform_services
from plus_ultra.database import get_connection, seed_demo_workspace_data
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.components.widgets import Card, StyledButton
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import (
    COLOR_ACCENT,
    COLOR_BG_DARK,
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_SIZE_BASE,
    FONT_SIZE_LG,
    FONT_SIZE_MD,
    FONT_SIZE_SM,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SPACING_XL,
    THEME,
    CapsuleTheme,
)

logger = logging.getLogger(__name__)


def _open_folder_in_explorer(folder_path: Path) -> None:
    """Open folder in native desktop file manager (Explorer / Nautilus)."""
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder_path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder_path)], check=False)
        else:
            subprocess.run(["xdg-open", str(folder_path)], check=False)
    except Exception as exc:
        logger.warning("Could not open folder %s: %s", folder_path, exc)


class SettingsView:
    """Comprehensive Preferences and Diagnostics workspace view."""

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        theme: CapsuleTheme = THEME,
        on_reseed: Callable[[], None] | None = None,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.theme = theme
        self.on_reseed = on_reseed
        self.platform = get_platform_services()

        self._init_variables()
        self._build_ui()

    def _init_variables(self) -> None:
        """Initialize Tk variables bound to current effective settings."""
        eff = settings.load_effective_settings()

        # General
        self.start_with_system_var = tk.BooleanVar(
            value=eff.get("start_with_system", False)
        )
        self.start_minimized_var = tk.BooleanVar(
            value=eff.get("start_minimized", False)
        )
        self.close_to_tray_var = tk.BooleanVar(
            value=eff.get("close_to_tray", True)
        )

        # Appearance
        self.capsule_visible_var = tk.BooleanVar(
            value=eff.get("capsule_visible", True)
        )
        self.topmost_var = tk.BooleanVar(
            value=eff.get("always_on_top", True)
        )
        self.glow_enabled_var = tk.BooleanVar(
            value=eff.get("glow_enabled", True)
        )

        # Notifications
        self.reminders_enabled_var = tk.BooleanVar(
            value=eff.get("reminders_enabled", True)
        )
        self.desktop_notif_var = tk.BooleanVar(
            value=eff.get("desktop_notifications_enabled", True)
        )
        self.dnd_mode_var = tk.BooleanVar(
            value=eff.get("dnd_mode", False)
        )
        self.popup_duration_var = tk.StringVar(
            value=str(eff.get("notification_popup_duration_ms", 3000))
        )

        # System Integration
        self.tray_enabled_var = tk.BooleanVar(
            value=eff.get("tray_enabled", True)
        )
        self.net_monitor_var = tk.BooleanVar(
            value=eff.get("network_monitor_enabled", True)
        )

    def _build_ui(self) -> None:
        """Construct scrollable multi-card settings layout."""
        # Top banner
        head_bar = tk.Frame(
            self.container, bg=COLOR_SURFACE, padx=SPACING_XL, pady=SPACING_LG
        )
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 24)
        title_lbl = tk.Label(
            head_bar,
            text=" Preferences & System Diagnostics",
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            image=icon,
            compound="left",
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(side="left")

        # Scrollable content area
        self.scroll = ScrollableFrame(self.container, bg=COLOR_SURFACE)
        self.scroll.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_SM)
        content = self.scroll.interior

        # 1. General Settings Card
        self._build_general_card(content)

        # 2. Appearance & Geometry Card
        self._build_appearance_card(content)

        # 3. Notifications & Reminders Card
        self._build_notifications_card(content)

        # 4. System Integration & Diagnostics Card
        self._build_system_card(content)

        # 5. Data & Storage Maintenance Card
        self._build_data_card(content)

    def _create_checkbox(
        self, parent: tk.Widget, text: str, variable: tk.BooleanVar, command: Callable[[], None]
    ) -> tk.Checkbutton:
        chk = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_BG_DARK,
            activebackground=COLOR_SURFACE_CARD,
            activeforeground=COLOR_ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=command,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        )
        chk.pack(anchor="w", pady=SPACING_SM // 2)
        return chk

    def _build_general_card(self, parent: tk.Widget) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=SPACING_SM)

        tk.Label(
            card,
            text="General Application Behavior",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_ACCENT,
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
        ).pack(anchor="w", pady=(0, SPACING_SM))

        self._create_checkbox(
            card,
            "Start PLUS-ULTRA automatically upon operating system login",
            self.start_with_system_var,
            self._on_start_with_system_toggled,
        )
        self._create_checkbox(
            card,
            "Start application minimized directly to system tray",
            self.start_minimized_var,
            lambda: self._save_bool("start_minimized", self.start_minimized_var),
        )
        self._create_checkbox(
            card,
            "Keep PLUS-ULTRA running in system tray when dashboard window closes",
            self.close_to_tray_var,
            lambda: self._save_bool("close_to_tray", self.close_to_tray_var),
        )

    def _build_appearance_card(self, parent: tk.Widget) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=SPACING_SM)

        tk.Label(
            card,
            text="Appearance & Floating Capsule Geometry",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_ACCENT,
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
        ).pack(anchor="w", pady=(0, SPACING_SM))

        self._create_checkbox(
            card,
            "Show floating desktop capsule presence",
            self.capsule_visible_var,
            lambda: self._save_bool("capsule_visible", self.capsule_visible_var),
        )
        self._create_checkbox(
            card,
            "Keep floating capsule always-on-top above all windows",
            self.topmost_var,
            self._toggle_topmost,
        )
        self._create_checkbox(
            card,
            "Enable animated orbiting border beam on capsule hover",
            self.glow_enabled_var,
            lambda: self._save_bool("glow_enabled", self.glow_enabled_var),
        )

        dims_lbl = tk.Label(
            card,
            text="Capsule Dimensions: 350x30px (Derived radius: 15px) | Dashboard: 1380x840px",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            anchor="w",
        )
        dims_lbl.pack(fill="x", pady=(SPACING_SM // 2, 0))

    def _build_notifications_card(self, parent: tk.Widget) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=SPACING_SM)

        tk.Label(
            card,
            text="Notifications & Scheduled Reminders",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_ACCENT,
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
        ).pack(anchor="w", pady=(0, SPACING_SM))

        self._create_checkbox(
            card,
            "Enable background task deadline evaluation & reminders",
            self.reminders_enabled_var,
            lambda: self._save_bool("reminders_enabled", self.reminders_enabled_var),
        )
        self._create_checkbox(
            card,
            "Dispatch native OS desktop notifications (Notification Area / notify-send)",
            self.desktop_notif_var,
            lambda: self._save_bool(
                "desktop_notifications_enabled", self.desktop_notif_var
            ),
        )
        self._create_checkbox(
            card,
            "Do Not Disturb (DND) mode: mute banner popups and sound alerts",
            self.dnd_mode_var,
            lambda: self._save_bool("dnd_mode", self.dnd_mode_var),
        )

        row = tk.Frame(card, bg=COLOR_SURFACE_CARD)
        row.pack(anchor="w", pady=(SPACING_SM // 2, 0))

        tk.Label(
            row,
            text="Popup Pill Banner Duration (ms): ",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        ).pack(side="left")

        duration_entry = tk.Entry(
            row,
            textvariable=self.popup_duration_var,
            width=8,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        )
        duration_entry.pack(side="left", padx=SPACING_SM)

        StyledButton(
            row,
            text="Apply Duration",
            command=self._apply_popup_duration,
            role="secondary",
            font_size=FONT_SIZE_SM,
            padx=10,
            pady=3,
        ).pack(side="left")

    def _build_system_card(self, parent: tk.Widget) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=SPACING_SM)

        tk.Label(
            card,
            text="System Integration & Environmental Diagnostics",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_ACCENT,
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
        ).pack(anchor="w", pady=(0, SPACING_SM))

        self._create_checkbox(
            card,
            "System tray icon integration (Notification area background presence)",
            self.tray_enabled_var,
            lambda: self._save_bool("tray_enabled", self.tray_enabled_var),
        )
        self._create_checkbox(
            card,
            "Network connectivity monitor (Capsule status dot & background probe)",
            self.net_monitor_var,
            self._toggle_net_monitor,
        )

        caps = self.platform.capabilities
        diag_lines = [
            f"Host Platform: {caps.platform_type.value.upper()} (Desktop: {caps.desktop_environment.value})",
            f"Display Server: {caps.display_server.value.upper()}",
            f"Tray Backend: {caps.tray_backend_name} (Supported: {caps.supports_system_tray})",
            f"Notification Backend: {caps.notification_backend_name} (Available: {caps.supports_desktop_notifications})",
        ]
        for line in diag_lines:
            tk.Label(
                card,
                text=f"•  {line}",
                bg=COLOR_SURFACE_CARD,
                fg=COLOR_TEXT_MUTED,
                font=(FONT_FAMILY, FONT_SIZE_SM),
                anchor="w",
            ).pack(fill="x", pady=1)

    def _build_data_card(self, parent: tk.Widget) -> None:
        card = Card(parent)
        card.pack(fill="x", pady=SPACING_SM)

        tk.Label(
            card,
            text="Local Data, Persistence & Storage Management",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_ACCENT,
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
        ).pack(anchor="w", pady=(0, SPACING_SM))

        db_path = config.get_db_path()
        cfg_path = config.get_user_settings_path()
        log_path = config.get_log_path()

        paths_info = [
            ("SQLite Store", db_path, db_path.parent),
            ("User Settings", cfg_path, cfg_path.parent),
            ("Persistent Log", log_path, log_path.parent),
        ]

        for label, file_path, folder_path in paths_info:
            row = tk.Frame(card, bg=COLOR_SURFACE_CARD)
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=f"{label}:",
                bg=COLOR_SURFACE_CARD,
                fg=COLOR_TEXT_SECONDARY,
                font=(FONT_FAMILY, FONT_SIZE_BASE, "bold"),
                width=14,
                anchor="w",
            ).pack(side="left")

            tk.Label(
                row,
                text=str(file_path),
                bg=COLOR_SURFACE_CARD,
                fg=COLOR_TEXT_MUTED,
                font=("courier", 9),
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=SPACING_SM)

            StyledButton(
                row,
                text="Open Folder",
                command=lambda p=folder_path: _open_folder_in_explorer(p),
                role="secondary",
                font_size=FONT_SIZE_SM,
                padx=10,
                pady=2,
            ).pack(side="right")

        # Action Buttons
        actions_row = tk.Frame(card, bg=COLOR_SURFACE_CARD)
        actions_row.pack(anchor="w", pady=(SPACING_MD, 0))

        StyledButton(
            actions_row,
            text="Reseed Demo Workspace Data",
            command=self.reseed_demo_data,
            role="secondary",
            font_size=FONT_SIZE_BASE,
            padx=16,
            pady=6,
        ).pack(side="left", padx=(0, SPACING_MD))

        StyledButton(
            actions_row,
            text="Reset All Settings to Defaults",
            command=self.reset_all_settings,
            role="danger",
            font_size=FONT_SIZE_BASE,
            padx=16,
            pady=6,
        ).pack(side="left")

    def _save_bool(self, key: str, var: tk.BooleanVar) -> None:
        val = var.get()
        settings.update_user_setting(key, val)
        logger.info("Setting '%s' updated to %s", key, val)

    def _on_start_with_system_toggled(self) -> None:
        val = self.start_with_system_var.get()
        settings.update_user_setting("start_with_system", val)
        if val:
            ok = self.platform.startup.enable_autostart()
            if not ok:
                messagebox.showwarning(
                    "Autostart",
                    "Could not register system autostart. Check operating system permissions.",
                    parent=self.parent_window,
                )
        else:
            self.platform.startup.disable_autostart()

    def _toggle_topmost(self) -> None:
        val = self.topmost_var.get()
        settings.update_user_setting("always_on_top", val)
        logger.info("Setting 'always_on_top' changed to %s", val)

    def _toggle_net_monitor(self) -> None:
        val = self.net_monitor_var.get()
        settings.update_user_setting("network_monitor_enabled", val)
        logger.info("Setting 'network_monitor_enabled' changed to %s", val)

    def _apply_popup_duration(self) -> None:
        try:
            val = int(self.popup_duration_var.get().strip())
            if val < 500 or val > 60000:
                raise ValueError("Must be between 500 and 60000 ms")
            settings.update_user_setting("notification_popup_duration_ms", val)
            messagebox.showinfo(
                "Settings",
                f"Notification popup duration updated to {val} ms.",
                parent=self.parent_window,
            )
        except Exception as exc:
            messagebox.showerror(
                "Invalid Duration",
                f"Please enter an integer between 500 and 60000 ms: {exc}",
                parent=self.parent_window,
            )

    def refresh(self) -> None:
        """Reload settings from disk into UI variables."""
        eff = settings.load_effective_settings()
        self.topmost_var.set(eff.get("always_on_top", True))
        self.net_monitor_var.set(eff.get("network_monitor_enabled", True))
        self.start_with_system_var.set(eff.get("start_with_system", False))
        self.start_minimized_var.set(eff.get("start_minimized", False))
        self.close_to_tray_var.set(eff.get("close_to_tray", True))
        self.capsule_visible_var.set(eff.get("capsule_visible", True))
        self.glow_enabled_var.set(eff.get("glow_enabled", True))
        self.reminders_enabled_var.set(eff.get("reminders_enabled", True))
        self.desktop_notif_var.set(eff.get("desktop_notifications_enabled", True))
        self.dnd_mode_var.set(eff.get("dnd_mode", False))
        self.tray_enabled_var.set(eff.get("tray_enabled", True))
        self.popup_duration_var.set(str(eff.get("notification_popup_duration_ms", 3000)))

    def reseed_demo_data(self) -> None:
        """Trigger workspace demo data reseed and notify user."""
        if not messagebox.askyesno(
            "Reseed Workspace",
            "Are you sure you want to reseed demo workspace data? "
            "This will add demo tasks, code snippets, DSA problems, and courses.",
            parent=self.parent_window,
        ):
            return

        conn = get_connection()
        try:
            seed_demo_workspace_data(conn)
            messagebox.showinfo(
                "Demo Data",
                "Successfully reseeded demo workspace data across all tabs!",
                parent=self.parent_window,
            )
            if self.on_reseed:
                self.on_reseed()
        except Exception as exc:
            messagebox.showerror(
                "Reseed Error",
                f"Failed to reseed workspace data: {exc}",
                parent=self.parent_window,
            )

    def reset_all_settings(self) -> None:
        """Reset all user preferences to defaults after confirmation."""
        if not messagebox.askyesno(
            "Reset All Settings",
            "Are you sure you want to reset all preferences to application defaults?",
            parent=self.parent_window,
        ):
            return

        settings.reset_all_settings()
        self.refresh()
        messagebox.showinfo(
            "Settings Reset",
            "All settings have been successfully reset to defaults.",
            parent=self.parent_window,
        )
