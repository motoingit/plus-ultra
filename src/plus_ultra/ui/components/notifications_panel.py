"""Right drawer component with Notifications and Network Status."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.services import CodeService
from plus_ultra.ui.icons import get_icon
from plus_ultra.ui.theme import THEME, CapsuleTheme


class NotificationsPanel:
    """Right-hand panel containing Notifications and Network Status monitor."""

    def __init__(
        self,
        container: tk.Widget,
        notification_queue: CapsuleNotificationQueue,
        theme: CapsuleTheme = THEME,
        on_notifications_cleared: Callable[[], None] | None = None,
        code_service: CodeService | None = None,
        parent_window: tk.Tk | tk.Toplevel | None = None,
    ) -> None:
        self.container = container
        self.notification_queue = notification_queue
        self.theme = theme
        self.on_notifications_cleared = on_notifications_cleared
        self.code_service = code_service
        self.parent_window = parent_window

        self.active_tab: str = "Notifications"
        self._build_ui()

    def _build_ui(self) -> None:
        # 1. Main Header Bar
        head_bar = tk.Frame(self.container, bg="#12151c", padx=16, pady=16)
        head_bar.pack(fill="x")

        icon = get_icon("fallback", 18)
        title_lbl = tk.Label(
            head_bar,
            text=" Recent Alerts",
            bg="#12151c",
            fg="#f8fafc",
            font=(self.theme.font_family, 13, "bold"),
            image=icon,
            compound="left",
        )
        title_lbl.image = icon  # type: ignore[attr-defined]
        title_lbl.pack(anchor="w")

        btn_box = tk.Frame(head_bar, bg="#12151c")
        btn_box.pack(fill="x", pady=(10, 0))

        tk.Button(
            btn_box,
            text="Mark All Read",
            bg="#1c212c",
            fg="#00e5ff",
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=5,
            command=self.mark_all_read,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_box,
            text="Clear",
            bg="#1c212c",
            fg="#94a3b8",
            activebackground="#2b3448",
            relief="flat",
            bd=0,
            font=(self.theme.font_family, 9),
            cursor="hand2",
            padx=10,
            pady=5,
            command=self.clear_all,
        ).pack(side="left")

        # 2. Notifications Listbox
        list_box_frame = tk.Frame(self.container, bg="#12151c", padx=16)
        list_box_frame.pack(fill="both", expand=True, pady=(6, 12))

        self.notif_listbox = tk.Listbox(
            list_box_frame,
            bg="#1c212c",
            fg="#f8fafc",
            selectbackground="#2b3448",
            selectforeground="#00e5ff",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.theme.font_family, 11),
        )
        self.notif_listbox.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self) -> None:
        """Update notification items displayed in the listbox."""
        self.notif_listbox.delete(0, tk.END)
        all_notifs = self.notification_queue.list_all()
        if not all_notifs:
            self.notif_listbox.insert(tk.END, "No recent alerts.")
            self.notif_listbox.itemconfig(0, fg="#64748b")
            return

        for idx, item in enumerate(all_notifs):
            prefix = "[Read] " if item.is_read else "[New] "
            line = f"{prefix}{item.title}"
            self.notif_listbox.insert(tk.END, line)
            if not item.is_read:
                self.notif_listbox.itemconfig(idx, fg="#00e5ff")
            else:
                self.notif_listbox.itemconfig(idx, fg="#94a3b8")

    def refresh_dsa(self) -> None:
        """Compatibility no-op method for DSA tab removal."""

    def mark_all_read(self) -> None:
        """Mark all notifications as read and fire callback."""
        self.notification_queue.mark_all_read()
        self.refresh()
        if self.on_notifications_cleared:
            self.on_notifications_cleared()

    def clear_all(self) -> None:
        """Clear all notifications from queue and fire callback."""
        self.notification_queue.clear()
        self.refresh()
        if self.on_notifications_cleared:
            self.on_notifications_cleared()
