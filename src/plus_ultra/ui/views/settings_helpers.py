"""Helper functions and card builders for SettingsView."""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from typing import Any

from plus_ultra import config
from plus_ultra.ui.components.widgets import Card, StyledButton
from plus_ultra.ui.theme import (
    COLOR_ACCENT,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_SIZE_BASE,
    FONT_SIZE_MD,
    FONT_SIZE_SM,
    SPACING_MD,
    SPACING_SM,
)


def open_folder_in_explorer(folder_path: Path) -> None:
    """Open folder in native desktop file manager (Explorer / Nautilus)."""
    with contextlib.suppress(Exception):
        folder_path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder_path)  # type: ignore[attr-defined]
        else:
            cmd = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.run([cmd, str(folder_path)], check=False)


def card_header(parent: tk.Widget, title: str) -> Card:
    """Create a standardized settings Card with accented header."""
    card = Card(parent)
    card.pack(fill="x", pady=SPACING_SM)
    tk.Label(
        card,
        text=title,
        bg=COLOR_SURFACE_CARD,
        fg=COLOR_ACCENT,
        font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
    ).pack(anchor="w", pady=(0, SPACING_SM))
    return card


def build_system_card(view: Any, parent: tk.Widget) -> None:
    """Build environmental diagnostics and system integration card."""
    c = card_header(parent, "System Integration & Environmental Diagnostics")
    view._add_check(
        c,
        "System tray integration (Background notification icon)",
        view.tray_enabled_var,
        "tray_enabled",
    )
    view._add_check(
        c,
        "Network monitor (Capsule status dot & background probe)",
        view.net_monitor_var,
        command=view._toggle_net_monitor,
    )
    caps = view.platform.capabilities
    p_name = caps.platform_type.value.upper()
    d_name = caps.desktop_environment.value
    srv = caps.display_server.value.upper()
    auto_st = "Yes" if view.platform.startup.is_autostart_enabled() else "No"
    diag_lines = [
        f"Host Platform: {p_name} (Desktop: {d_name})",
        f"Display Server: {srv}",
        f"Tray Backend: {caps.tray_backend_name} "
        f"(Supported: {caps.supports_system_tray})",
        f"Notification Backend: {caps.notification_backend_name}",
        f"Autostart on OS Login: {auto_st}",
    ]
    for line in diag_lines:
        tk.Label(
            c,
            text=f"•  {line}",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_MUTED,
            font=("courier", 9),
            anchor="w",
        ).pack(anchor="w", pady=1)

    StyledButton(
        c,
        text="Terminate Application",
        command=view.terminate_application,
        role="danger",
        font_size=FONT_SIZE_BASE,
        padx=14,
        pady=5,
    ).pack(anchor="w", pady=(SPACING_MD, 0))


def build_data_card(view: Any, parent: tk.Widget) -> None:
    """Build data storage, log paths, and factory reset actions card."""
    card = card_header(parent, "Local Data, Persistence & Storage Management")
    db_p = config.get_db_path()
    cfg_p = config.get_user_settings_path()
    log_p = config.get_log_path()
    for label, file_path, folder_path in (
        ("SQLite Store", db_p, db_p.parent),
        ("User Settings", cfg_p, cfg_p.parent),
        ("Persistent Log", log_p, log_p.parent),
    ):
        row = tk.Frame(card, bg=COLOR_SURFACE_CARD)
        row.pack(fill="x", pady=4)
        tk.Label(
            row,
            text=f"{label}:",
            bg=COLOR_SURFACE_CARD,
            fg=COLOR_TEXT_SECONDARY,
            width=14,
            anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_BASE, "bold"),
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
            command=lambda p=folder_path: open_folder_in_explorer(p),
            role="secondary",
            font_size=FONT_SIZE_SM,
            padx=10,
            pady=2,
        ).pack(side="right")

    actions_row = tk.Frame(card, bg=COLOR_SURFACE_CARD)
    actions_row.pack(anchor="w", pady=(SPACING_MD, 0))
    for title, handler, role in (
        ("Reset Config Settings", view.reset_config_settings, "secondary"),
        ("Factory Reset (Delete Everything)", view.factory_reset, "danger"),
        ("Reseed Demo Data", view.reseed_demo_data, "secondary"),
    ):
        StyledButton(
            actions_row,
            text=title,
            command=handler,
            role=role,
            font_size=FONT_SIZE_BASE,
            padx=14,
            pady=6,
        ).pack(side="left", padx=(0, SPACING_MD))
