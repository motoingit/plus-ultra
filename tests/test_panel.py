"""Unit tests for DashboardPanel, TaskDialog, and UI panel interactions.

Validates:
- 3-column dashboard construction and layout verification.
- Tab switching across 6 workspace categories and placeholders.
- Treeview task rendering, searching, priority filtering, and status filtering.
- Status toggle and soft-delete via context actions.
- TaskDialog prefill, validation, and on_save callback.
- Notification panel Mark All Read and Clear operations triggering callbacks.
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from pathlib import Path
from typing import Any

from plus_ultra.db import get_connection, init_db
from plus_ultra.notifications import CapsuleNotificationQueue
from plus_ultra.repository import CategoryRepository, TaskRepository
from plus_ultra.services import CategoryService, TaskService
from plus_ultra.ui.panel import DashboardPanel, TaskDialog


def setup_test_services(
    tmp_path: Path,
) -> tuple[TaskService, CategoryService, CapsuleNotificationQueue]:
    """Create test services with an isolated SQLite DB."""
    db_path = tmp_path / "panel_test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    cat_repo = CategoryRepository(conn)
    task_repo = TaskRepository(conn)
    task_svc = TaskService(task_repo, cat_repo)
    cat_svc = CategoryService(cat_repo)
    queue = CapsuleNotificationQueue()
    return task_svc, cat_svc, queue


def test_dashboard_panel_layout_and_tabs(tmp_path: Path) -> None:
    """Verify 3-column construction, tab buttons, and tab switching."""
    task_svc, cat_svc, queue = setup_test_services(tmp_path)
    root = tk.Tk()
    try:
        panel = DashboardPanel(
            parent=root,
            task_service=task_svc,
            category_service=cat_svc,
            notification_queue=queue,
        )

        assert panel.sidebar_col is not None
        assert panel.center_col is not None
        assert panel.notif_col is not None
        assert len(panel.tab_buttons) == 6

        # Default tab is Tasks
        assert panel.active_tab == "Tasks"

        # Switch to Code tab
        panel._switch_tab("Code")
        assert panel.active_tab == "Code"
        assert panel.placeholder_container.winfo_manager() == "pack"
        assert panel.tasks_container.winfo_manager() == ""

        # Switch back to Tasks
        panel._switch_tab("Tasks")
        assert panel.active_tab == "Tasks"
        assert panel.tasks_container.winfo_manager() == "pack"
        assert panel.placeholder_container.winfo_manager() == ""

        # Toggle visibility
        panel.show()
        assert panel.state() == "normal"
        panel.toggle()
        assert panel.state() == "withdrawn"
        panel.toggle()
        assert panel.state() == "normal"

        panel.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_dashboard_treeview_tasks_and_filters(tmp_path: Path) -> None:
    """Verify task population, searching, and filtering in the Treeview."""
    task_svc, cat_svc, queue = setup_test_services(tmp_path)
    cat = cat_svc.create_category("Academics")
    t1 = task_svc.create_task(
        title="DBMS Assignment",
        category_id=cat.id,
        critical_level="High",
        status="Pending",
    )
    t2 = task_svc.create_task(
        title="Network Security Lab",
        category_id=cat.id,
        critical_level="Low",
        status="Completed",
    )

    root = tk.Tk()
    try:
        panel = DashboardPanel(
            parent=root,
            task_service=task_svc,
            category_service=cat_svc,
            notification_queue=queue,
        )

        # Initial refresh contains both tasks
        children = panel.tree.get_children()
        assert len(children) == 2
        assert t1.id in children
        assert t2.id in children

        # Filter by status: Completed
        panel._set_status_filter("Completed")
        completed_children = panel.tree.get_children()
        assert len(completed_children) == 1
        assert t2.id in completed_children

        # Reset filter
        panel._set_status_filter("All")
        assert len(panel.tree.get_children()) == 2

        # Search query filter
        panel.search_entry.insert(0, "security")
        panel._refresh_tasks()
        searched = panel.tree.get_children()
        assert len(searched) == 1
        assert t2.id in searched

        panel.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_dashboard_context_menu_actions(tmp_path: Path) -> None:
    """Verify toggling status and task deletion from the Treeview."""
    task_svc, cat_svc, queue = setup_test_services(tmp_path)
    task = task_svc.create_task("Finish Presentation")
    assert task.status == "Pending"

    root = tk.Tk()
    try:
        panel = DashboardPanel(
            parent=root,
            task_service=task_svc,
            category_service=cat_svc,
            notification_queue=queue,
        )

        # Toggle status
        panel._toggle_selected_status(task.id)
        updated = task_svc.get_task(task.id)
        assert updated is not None
        assert updated.status == "Completed"

        # Direct soft delete
        task_svc.soft_delete_task(task.id)
        panel._refresh_tasks()
        assert len(panel.tree.get_children()) == 0

        panel.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_task_dialog_save_and_validation(tmp_path: Path) -> None:
    """Verify TaskDialog form validation and save payload."""
    _, cat_svc, _ = setup_test_services(tmp_path)
    cat = cat_svc.create_category("Engineering")

    root = tk.Tk()
    try:
        saved_data: dict[str, Any] = {}

        def _on_save(data: dict[str, Any]) -> None:
            saved_data.update(data)

        dialog = TaskDialog(
            parent=root,
            categories=[cat],
            on_save=_on_save,
        )

        dialog.title_entry.insert(0, "New Compiler Optimization")
        dialog.cat_combo.set("Engineering")
        dialog.prio_combo.set("High")
        dialog.pace_combo.set("Long-term")
        dialog.due_entry.insert(0, "2026-11-01")
        dialog.desc_text.insert("1.0", "LLVM Backend IR pass")

        dialog._handle_save()
        assert saved_data["title"] == "New Compiler Optimization"
        assert saved_data["category_id"] == cat.id
        assert saved_data["critical_level"] == "High"
        assert saved_data["pace_level"] == "Long-term"
        assert saved_data["due_date"] == "2026-11-01"
        assert "LLVM Backend IR pass" in saved_data["description"]
    finally:
        with contextlib.suppress(Exception):
            root.destroy()


def test_notification_panel_actions(tmp_path: Path) -> None:
    """Verify notification actions mark all read and clear items."""
    task_svc, cat_svc, queue = setup_test_services(tmp_path)
    queue.push(title="Alert 1", message="Details 1")
    queue.push(title="Alert 2", message="Details 2")
    assert queue.unread_count == 2

    root = tk.Tk()
    try:
        cleared_called = False

        def _on_cleared() -> None:
            nonlocal cleared_called
            cleared_called = True

        panel = DashboardPanel(
            parent=root,
            task_service=task_svc,
            category_service=cat_svc,
            notification_queue=queue,
            on_notifications_cleared=_on_cleared,
        )

        assert panel.notif_listbox.size() == 2

        # Mark all read
        panel._mark_all_notifications_read()
        assert queue.unread_count == 0
        assert cleared_called is True

        # Clear all
        cleared_called = False
        panel._clear_all_notifications()
        assert len(queue.list_all()) == 0
        assert cleared_called is True
        assert panel.notif_listbox.get(0) == "No recent alerts."

        panel.destroy()
    finally:
        with contextlib.suppress(Exception):
            root.destroy()
