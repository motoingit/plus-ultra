"""Unit tests for UI refinements: DateTimePicker, PS/I subtabs, and capsule."""

from __future__ import annotations

import contextlib
import datetime
import tkinter as tk
from pathlib import Path
from typing import Any

from plus_ultra.database import get_connection, init_db
from plus_ultra.network import NetworkStatusMonitor, is_network_online
from plus_ultra.repositories import (
    IdeaDoubtRepository,
)
from plus_ultra.services import (
    IdeaDoubtService,
)
from plus_ultra.ui.components.datetime_picker import DateTimePicker
from plus_ultra.ui.dialogs import CodeDialog, OpportunityDialog, TaskDialog
from plus_ultra.ui.floating import FloatingWidget
from plus_ultra.ui.views.ideas_view import IdeasView


def test_datetime_picker_interactive_actions() -> None:
    """Verify DateTimePicker Now, presets, time updates, and day steppers."""
    root = tk.Tk()
    try:
        picker = DateTimePicker(root, include_time=True)

        # 1. Test set_now
        picker.set_now()
        val = picker.get_value()
        today_prefix = datetime.date.today().strftime("%Y-%m-%d")
        assert val.startswith(today_prefix)
        assert len(val.split()) == 2

        # 2. Test set_time
        picker.set_time("15:30")
        assert picker.get_value() == f"{today_prefix} 15:30"

        # 3. Test add_days_from_today
        picker.add_days_from_today(2)
        target = (
            datetime.date.today() + datetime.timedelta(days=2)
        ).isoformat()
        assert picker.get_value().startswith(target)

        # 4. Test step_days
        picker.set_value(f"{today_prefix} 18:00")
        picker.step_days(1)
        expected_next = (
            datetime.date.today() + datetime.timedelta(days=1)
        ).isoformat()
        assert picker.get_value() == f"{expected_next} 18:00"

        picker.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_datetime_picker_date_only_mode() -> None:
    """Verify DateTimePicker date-only mode for deadlines."""
    root = tk.Tk()
    try:
        picker = DateTimePicker(root, include_time=False)
        picker.set_now()
        val = picker.get_value()
        today = datetime.date.today().strftime("%Y-%m-%d")
        assert val == today
        assert " " not in val

        picker.add_days_from_today(5)
        expected = (
            datetime.date.today() + datetime.timedelta(days=5)
        ).isoformat()
        assert picker.get_value() == expected

        picker.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_task_and_opportunity_dialogs_datetime_picker() -> None:
    """Verify TaskDialog and OpportunityDialog use DateTimePicker."""
    root = tk.Tk()
    try:
        task_data: dict[str, Any] = {}
        t_dlg = TaskDialog(
            parent=root,
            categories=[],
            on_save=lambda d: task_data.update(d),
        )
        assert isinstance(t_dlg.datetime_picker, DateTimePicker)
        t_dlg.title_entry.insert(0, "Complete Milestone")
        t_dlg.due_entry.insert(0, "2026-12-31 23:59")
        t_dlg._handle_save()
        assert task_data["due_date"] == "2026-12-31 23:59"

        opp_data: dict[str, Any] = {}
        o_dlg = OpportunityDialog(
            parent=root,
            on_save=lambda d: opp_data.update(d),
        )
        assert isinstance(o_dlg.datetime_picker, DateTimePicker)
        o_dlg.title_entry.insert(0, "Staff Engineer")
        o_dlg.org_entry.insert(0, "Mozilla")
        o_dlg.dead_entry.insert(0, "2026-11-15")
        o_dlg._handle_save()
        assert opp_data["deadline"] == "2026-11-15"
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_code_dialog_predefined_languages() -> None:
    """Verify CodeDialog offers predefined language selections."""
    root = tk.Tk()
    try:
        dlg = CodeDialog(parent=root)
        values = list(dlg.lang_combo["values"])
        assert "Python" in values
        assert "Rust" in values
        assert "JavaScript" in values
        assert "Go" in values
        assert "SQL" in values
        dlg.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_psi_ideas_view_subtabs(tmp_path: Path) -> None:
    """Verify PS/I IdeasView distinct sub-tabs for Ideas and Doubts."""
    db_path = tmp_path / "ideas_test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    repo = IdeaDoubtRepository(conn)
    svc = IdeaDoubtService(repo)

    svc.create_item(kind="Idea", title="Distributed Cache Architecture")
    svc.create_item(kind="Doubt", title="How does Raft handle partition?")

    root = tk.Tk()
    try:
        view = IdeasView(
            container=root, parent_window=root, idea_doubt_service=svc
        )

        # Default subtab is Idea
        assert view.active_subtab == "Idea"
        assert view.add_btn.cget("text") == "+ Add Idea"
        view.refresh()
        cards = view.ideas_scroll.interior.winfo_children()
        assert len(cards) == 1

        # Switch to Doubts subtab
        view.switch_subtab("Doubt")
        assert view.active_subtab == "Doubt"
        assert view.add_btn.cget("text") == "+ Add Doubt"
        view.refresh()
        doubt_cards = view.ideas_scroll.interior.winfo_children()
        assert len(doubt_cards) == 1

        view.container.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_floating_widget_dynamic_capsule_expansion() -> None:
    """Verify FloatingWidget expands width on unread alerts and restores."""
    root = tk.Tk()
    try:
        widget = FloatingWidget(root=root)
        initial_w = widget.width

        # Post an unread notification -> triggers expansion
        widget.post_notification(title="System Alert", message="Disk space low")
        widget.root.update_idletasks()
        widget._update_bell_state()

        assert widget.width > initial_w
        assert widget.notifications.has_unread is True

        # Mark all read -> restores default compact width
        widget.mark_all_read()
        widget.root.update_idletasks()
        widget._update_bell_state()

        assert widget.width == initial_w
        assert widget.notifications.has_unread is False

        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_network_monitor_probe() -> None:
    """Verify NetworkStatusMonitor puts probe results in queue without crash."""
    monitor = NetworkStatusMonitor()
    assert monitor.get_result() is None
    # Synchronous probe returns boolean
    res = is_network_online(timeout=0.8)
    assert isinstance(res, bool)
