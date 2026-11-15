"""Preferences, Diagnostics, and System Settings view for PLUS-ULTRA."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

from plus_ultra import settings
from plus_ultra.config import get_platform_services
from plus_ultra.database import (
    seed_demo_workspace_data,
    wipe_database,
)
from plus_ultra.ui.components.scrollable import ScrollableFrame
from plus_ultra.ui.components.widgets import StyledButton
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
    FONT_SIZE_SM,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SPACING_XL,
    THEME,
    CapsuleTheme,
)
from plus_ultra.ui.views.settings_helpers import (
    build_data_card,
    build_system_card,
    card_header,
)

logger = logging.getLogger(__name__)


class SettingsView:
    """Comprehensive Preferences and Diagnostics workspace view."""

    _BOOL_SETTINGS: dict[str, tuple[str, bool]] = {
        "start_with_system_var": ("start_with_system", False),
        "start_minimized_var": ("start_minimized", False),
        "close_to_tray_var": ("close_to_tray", True),
        "capsule_visible_var": ("capsule_visible", True),
        "topmost_var": ("always_on_top", True),
        "glow_enabled_var": ("glow_enabled", True),
        "reminders_enabled_var": ("reminders_enabled", True),
        "desktop_notif_var": ("desktop_notifications_enabled", True),
        "dnd_mode_var": ("dnd_mode", False),
        "tray_enabled_var": ("tray_enabled", True),
        "net_monitor_var": ("network_monitor_enabled", True),
    }

    def __init__(
        self,
        container: tk.Widget,
        parent_window: tk.Tk | tk.Toplevel,
        theme: CapsuleTheme = THEME,
        on_reseed: Callable[[], None] | None = None,
        on_terminate: Callable[[], None] | None = None,
    ) -> None:
        self.container = container
        self.parent_window = parent_window
        self.theme = theme
        self.on_reseed = on_reseed
        self.on_terminate = on_terminate
        self.platform = get_platform_services()
        self._init_variables()
        self._build_ui()

    def _init_variables(self) -> None:
        """Initialize Tk variables bound to current effective settings."""
        eff = settings.load_effective_settings()
        for attr, (k, def_val) in self._BOOL_SETTINGS.items():
            setattr(self, attr, tk.BooleanVar(value=eff.get(k, def_val)))
        if self.platform.startup.is_supported:
            self.start_with_system_var.set(
                self.platform.startup.is_autostart_enabled()
            )
        dur = eff.get("notification_popup_duration_ms", 3000)
        self.popup_duration_var = tk.StringVar(value=str(dur))
        self.theme_var = tk.StringVar(value=eff.get("theme", "cyan"))

    def _build_ui(self) -> None:
        """Construct scrollable multi-card settings layout."""
        head = tk.Frame(
            self.container, bg=COLOR_SURFACE, padx=SPACING_XL, pady=SPACING_LG
        )
        head.pack(fill="x")
        self._gear_icon = get_icon("settings", 20)
        tk.Label(head, image=self._gear_icon, bg=COLOR_SURFACE).pack(
            side="left", padx=(0, SPACING_MD)
        )
        col = tk.Frame(head, bg=COLOR_SURFACE)
        col.pack(side="left")
        tk.Label(
            col,
            text="Preferences & Environmental Diagnostics",
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            col,
            text="Application behavior, display geometry, and storage",
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SM),
        ).pack(anchor="w")

        self.scroll = ScrollableFrame(self.container, bg=COLOR_BG_DARK)
        self.scroll.pack(
            fill="both", expand=True, padx=SPACING_LG, pady=SPACING_SM
        )
        c = self.scroll.interior
        self._build_general_card(c)
        self._build_appearance_card(c)
        self._build_notifications_card(c)
        self._build_system_card(c)
        self._build_data_card(c)

    def _add_check(
        self,
        parent: tk.Widget,
        text: str,
        var: tk.BooleanVar,
        save_key: str | None = None,
        command: Callable[[], None] | None = None,
    ) -> tk.Checkbutton:
        cmd = command or (lambda: self._save_bool(save_key or "", var))
        chk = tk.Checkbutton(
            parent,
            text=text,
            variable=var,
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_BG_DARK,
            activebackground=COLOR_SURFACE_CARD,
            activeforeground=COLOR_ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=cmd,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        )
        chk.pack(anchor="w", pady=SPACING_SM // 2)
        return chk

    def _build_general_card(self, parent: tk.Widget) -> None:
        c = card_header(parent, "General Application Behavior")
        self._add_check(
            c,
            "Start PLUS-ULTRA automatically upon OS login",
            self.start_with_system_var,
            command=self._on_start_with_system_toggled,
        )
        self._add_check(
            c,
            "Start application minimized to system tray",
            self.start_minimized_var,
            "start_minimized",
        )
        self._add_check(
            c,
            "Keep running in system tray when dashboard closes",
            self.close_to_tray_var,
            "close_to_tray",
        )

    def _build_appearance_card(self, parent: tk.Widget) -> None:
        c = card_header(parent, "Appearance & Floating Capsule Geometry")
        self._add_check(
            c,
            "Show floating desktop capsule presence",
            self.capsule_visible_var,
            "capsule_visible",
        )
        self._add_check(
            c,
            "Keep floating capsule always-on-top above all windows",
            self.topmost_var,
            command=self._toggle_topmost,
        )
        self._add_check(
            c,
            "Enable animated orbiting border beam on capsule hover",
            self.glow_enabled_var,
            "glow_enabled",
        )
        t_row = tk.Frame(c, bg=COLOR_SURFACE_CARD)
        t_row.pack(fill="x", pady=(SPACING_SM // 2, 0))
        tk.Label(
            t_row,
            text="Theme Accent: ",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, FONT_SIZE_BASE),
        ).pack(side="left")
        for key, label in (
            ("cyan", "Cyan"),
            ("emerald", "Emerald"),
            ("purple", "Violet"),
            ("amber", "Amber"),
        ):
            StyledButton(
                t_row,
                text=label,
                command=lambda k=key: self._on_theme_selected(k),
                role="secondary",
                font_size=FONT_SIZE_SM,
                padx=6,
                pady=2,
            ).pack(side="left", padx=2)
        tk.Label(
            c,
            text="Capsule: 350x30px (Radius: 15px) | Dashboard: 1380x840px",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            anchor="w",
        ).pack(fill="x", pady=(SPACING_SM // 2, 0))

    def _build_notifications_card(self, parent: tk.Widget) -> None:
        c = card_header(parent, "Notifications & Scheduled Reminders")
        self._add_check(
            c,
            "Enable background task deadline evaluation & reminders",
            self.reminders_enabled_var,
            "reminders_enabled",
        )
        self._add_check(
            c,
            "Dispatch native OS desktop notifications (notify-send / Toast)",
            self.desktop_notif_var,
            "desktop_notifications_enabled",
        )
        self._add_check(
            c,
            "Do Not Disturb (DND) mode: mute banner popups and alerts",
            self.dnd_mode_var,
            "dnd_mode",
        )
        row = tk.Frame(c, bg=COLOR_SURFACE_CARD)
        row.pack(anchor="w", pady=(SPACING_SM // 2, 0))
        tk.Label(
            row,
            text="Popup Pill Duration (ms): ",
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
        build_system_card(self, parent)

    def _build_data_card(self, parent: tk.Widget) -> None:
        build_data_card(self, parent)

    def _save_bool(self, key: str, var: tk.BooleanVar) -> None:
        val = var.get()
        settings.update_user_setting(key, val)
        logger.info("Setting '%s' updated to %s", key, val)

    def _on_start_with_system_toggled(self) -> None:
        val = self.start_with_system_var.get()
        settings.update_user_setting("start_with_system", val)
        if val and not self.platform.startup.enable_autostart():
            self.start_with_system_var.set(False)
            settings.update_user_setting("start_with_system", False)
            messagebox.showwarning(
                "Autostart",
                "Could not register autostart. Check permissions.",
                parent=self.parent_window,
            )
        elif not val:
            self.platform.startup.disable_autostart()

    def _on_theme_selected(self, key: str) -> None:
        self.theme_var.set(key)
        settings.update_user_setting("theme", key)
        messagebox.showinfo(
            "Theme Updated",
            f"Accent theme set to '{key.capitalize()}'. Restart to apply.",
            parent=self.parent_window,
        )

    def _toggle_topmost(self) -> None:
        settings.update_user_setting("always_on_top", self.topmost_var.get())

    def _toggle_net_monitor(self) -> None:
        settings.update_user_setting(
            "network_monitor_enabled", self.net_monitor_var.get()
        )

    def _apply_popup_duration(self) -> None:
        try:
            val = int(self.popup_duration_var.get().strip())
            if not 500 <= val <= 60000:
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
        for attr, (k, def_val) in self._BOOL_SETTINGS.items():
            getattr(self, attr).set(eff.get(k, def_val))
        if self.platform.startup.is_supported:
            self.start_with_system_var.set(
                self.platform.startup.is_autostart_enabled()
            )
        dur = eff.get("notification_popup_duration_ms", 3000)
        self.popup_duration_var.set(str(dur))
        self.theme_var.set(eff.get("theme", "cyan"))

    def reseed_demo_data(self) -> None:
        """Trigger workspace demo data reseed and notify user."""
        if not messagebox.askyesno(
            "Reseed Workspace",
            "Reseed demo workspace data across all categories?",
            parent=self.parent_window,
        ):
            return
        try:
            seed_demo_workspace_data()
            messagebox.showinfo(
                "Demo Data",
                "Reseeded demo data across all tabs!",
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

    def reset_config_settings(self) -> None:
        """Reset configuration preferences to defaults without data loss."""
        msg = "Reset preferences to defaults?\nUser data will be kept."
        if not messagebox.askyesno(
            "Reset Config Settings", msg, parent=self.parent_window
        ):
            return
        settings.reset_all_settings()
        self.refresh()
        messagebox.showinfo(
            "Config Reset",
            "Configuration restored to defaults.",
            parent=self.parent_window,
        )

    def factory_reset(self) -> None:
        """Permanently delete all workspace data and restore clean state."""
        msg = (
            "WARNING: This will PERMANENTLY DELETE all your data:\n"
            "• All tasks, categories, reminders, courses, and code\n"
            "• All user preferences and configurations\n\n"
            "This action CANNOT be undone. Proceed?"
        )
        if not messagebox.askyesno(
            "Factory Reset (Delete Everything)",
            msg,
            icon="warning",
            parent=self.parent_window,
        ):
            return
        try:
            wipe_database()
            settings.reset_all_settings()
            self.refresh()
            if self.on_reseed:
                self.on_reseed()
            messagebox.showinfo(
                "Factory Reset Complete",
                "All data and settings wiped.",
                parent=self.parent_window,
            )
        except Exception as exc:
            logger.error("Factory reset failed: %s", exc, exc_info=True)
            messagebox.showerror(
                "Factory Reset Failed",
                f"Could not reset: {exc}",
                parent=self.parent_window,
            )

    def terminate_application(self) -> None:
        """Prompt confirmation and terminate running application cleanly."""
        if not messagebox.askyesno(
            "Terminate Application",
            "Are you sure you want to exit PLUS-ULTRA?",
            parent=self.parent_window,
        ):
            return
        logger.info("Application termination requested via SettingsView.")
        if self.on_terminate:
            self.on_terminate()
        else:
            self.parent_window.quit()

    def reset_all_settings(self) -> None:
        """Backward compatibility alias for reset_config_settings."""
        self.reset_config_settings()
