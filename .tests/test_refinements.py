"""Unit tests for UI refinements: DateTimePicker, PS/I subtabs, and capsule."""

from __future__ import annotations

import contextlib
import datetime
import tkinter as tk
from pathlib import Path
from typing import Any

from plus_ultra.database import get_connection, init_db
from plus_ultra.models import Task
from plus_ultra.network import NetworkStatusMonitor, is_network_online
from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.repositories import (
    CodeRepository,
    CourseRepository,
    IdeaDoubtRepository,
    OpportunityRepository,
    QuickLinkRepository,
)
from plus_ultra.services import (
    CodeService,
    CourseService,
    IdeaDoubtService,
    OpportunityService,
    QuickLinkService,
)
from plus_ultra.ui.components.datetime_picker import DateTimePicker
from plus_ultra.ui.components.popup_pill import CapsulePopupPill
from plus_ultra.ui.components.task_card import TaskCard
from plus_ultra.ui.dialogs import CodeDialog, OpportunityDialog, TaskDialog
from plus_ultra.ui.floating import FloatingWidget
from plus_ultra.ui.views.code_view import CodeView
from plus_ultra.ui.views.courses_view import CoursesView
from plus_ultra.ui.views.ideas_view import IdeasView
from plus_ultra.ui.views.opportunities_view import OpportunitiesView
from plus_ultra.ui.views.quick_links_view import QuickLinksView


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


def test_capsule_popup_pill_lifecycle() -> None:
    """Verify CapsulePopupPill show, reposition, and dismiss lifecycle."""
    root = tk.Tk()
    try:
        queue = CapsuleNotificationQueue()
        item = queue.push(title="Test Alert", message="Test Body", icon="🔔")
        pill = CapsulePopupPill(parent=root, queue=queue)

        assert pill.is_visible is False
        pill.show(
            item=item,
            parent_x=100,
            parent_y=50,
            parent_w=320,
            parent_h=72,
            duration_ms=5000,
        )
        assert pill.is_visible is True
        assert pill.window is not None

        pill.reposition(parent_x=120, parent_y=60, parent_w=320, parent_h=72)
        assert pill.is_visible is True

        pill.dismiss()
        assert pill.is_visible is False
        assert pill.window is None
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_task_card_interactions() -> None:
    """Verify TaskCard renders attributes and triggers action callbacks."""
    root = tk.Tk()
    try:
        task = Task(
            id="t-1",
            category_id="c-1",
            title="Design Clean Architecture",
            description="Separate into 3 layers with tests",
            due_date="2026-10-30 18:00",
            status="Pending",
            critical_level="High",
            pace_level="Sprint",
            is_google_task=True,
            created_at="2026-10-17T00:00:00Z",
            updated_at="2026-10-17T00:00:00Z",
        )
        toggled: list[str] = []
        edited: list[Task] = []
        deleted: list[str] = []

        card = TaskCard(
            parent=root,
            task=task,
            category_name="Architecture",
            on_toggle=lambda tid: toggled.append(tid),
            on_edit=lambda t: edited.append(t),
            on_delete=lambda tid: deleted.append(tid),
        )

        card._handle_toggle()
        assert toggled == ["t-1"]

        card._handle_edit()
        assert len(edited) == 1
        assert edited[0].title == "Design Clean Architecture"

        card._handle_delete()
        assert deleted == ["t-1"]
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_all_category_views_have_search_inputs(tmp_path: Path) -> None:
    """Verify Code, Courses, Ideas, Opportunities, and Links support search."""
    db_path = tmp_path / "search_test.db"
    init_db(db_path)
    conn = get_connection(db_path)

    code_svc = CodeService(CodeRepository(conn))
    course_svc = CourseService(CourseRepository(conn))
    idea_svc = IdeaDoubtService(IdeaDoubtRepository(conn))
    opp_svc = OpportunityService(OpportunityRepository(conn))
    link_svc = QuickLinkService(QuickLinkRepository(conn))

    code_svc.create_item(category="Snippets", title="Fast Fourier Transform")
    course_svc.create_course(title="Distributed Systems MIT")
    idea_svc.create_item(kind="Idea", title="Wayland Window Manager")
    opp_svc.create_opportunity(
        title="Linux Kernel Intern", organization="Red Hat"
    )
    link_svc.create_link(
        name="Kernel Documentation", target_uri="https://kernel.org"
    )

    root = tk.Tk()
    try:
        # 1. CodeView Search
        cv = CodeView(root, root, code_service=code_svc)
        assert hasattr(cv, "search_entry")
        cv.search_entry.insert(0, "Fourier")
        cv.refresh()
        assert len(cv.code_scroll.interior.winfo_children()) == 1

        # 2. CoursesView Search
        crv = CoursesView(root, root, course_service=course_svc)
        assert hasattr(crv, "search_entry")
        crv.search_entry.insert(0, "Distributed")
        crv.refresh()
        assert len(crv.courses_scroll.interior.winfo_children()) == 1

        # 3. IdeasView Search
        iv = IdeasView(root, root, idea_doubt_service=idea_svc)
        assert hasattr(iv, "search_entry")
        iv.search_entry.insert(0, "Wayland")
        iv.refresh()
        assert len(iv.ideas_scroll.interior.winfo_children()) == 1

        # 4. OpportunitiesView Search
        ov = OpportunitiesView(root, root, opportunity_service=opp_svc)
        assert hasattr(ov, "search_entry")
        ov.search_entry.insert(0, "Kernel")
        ov.refresh()
        assert len(ov.opps_scroll.interior.winfo_children()) == 1

        # 5. QuickLinksView Search
        qv = QuickLinksView(root, root, quick_link_service=link_svc)
        assert hasattr(qv, "search_entry")
        qv.search_entry.insert(0, "Documentation")
        qv.refresh()
        assert len(qv.links_scroll.interior.winfo_children()) == 1
    finally:
        with contextlib.suppress(Exception):
            root.destroy()
        conn.close()


def test_floating_widget_auto_dismiss_notification() -> None:
    """Verify FloatingWidget auto-dismisses notification after duration."""
    root = tk.Tk()
    try:
        widget = FloatingWidget(root=root)
        widget.popup_duration_ms = 80
        base_w = widget.width

        widget.post_notification(title="Alert", message="Disappearing in 80ms")
        widget.root.update_idletasks()
        widget.root.update()

        assert widget.notifications.has_unread is True
        assert widget.width > base_w
        assert widget.canvas.itemcget(widget.bell_id, "state") == "normal"

        widget.root.after(130, widget.root.quit)
        widget.root.mainloop()

        assert widget.notifications.has_unread is False
        assert widget.width == base_w
        assert widget.canvas.itemcget(widget.bell_id, "state") == "hidden"
        assert widget.popup_pill.is_visible is False

        widget.close()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_capsule_popup_pill_on_dismiss_callback() -> None:
    """Verify CapsulePopupPill on_dismiss callback fires when dismissed."""
    root = tk.Tk()
    try:
        queue = CapsuleNotificationQueue()
        item = queue.push(title="Click Test", message="Dismiss me")
        dismiss_called = []
        pill = CapsulePopupPill(
            parent=root,
            queue=queue,
            default_duration_ms=100,
            on_dismiss=lambda: dismiss_called.append(True),
        )
        pill.show(item, parent_x=10, parent_y=10, parent_w=300, parent_h=50)
        assert pill.is_visible is True

        pill.dismiss()
        assert pill.is_visible is False
        assert dismiss_called == [True]
    finally:
        with contextlib.suppress(Exception):
            root.destroy()
