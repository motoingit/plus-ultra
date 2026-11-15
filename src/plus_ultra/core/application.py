"""Central Application controller orchestrating lifecycle and subsystems.

Applies OS and Software Architecture concepts:
- Predictable lifecycle state machine (INITIALIZING -> RUNNING -> STOPPED).
- Resource Management: Database connections, single-instance file locks,
  background scheduler threads, and system tray thread all registered
  with explicit, idempotent shutdown hooks.
- Cross-thread synchronization: System tray and background scheduler callbacks
  are marshaled onto the Tkinter main thread via LifecycleManager.
"""

from __future__ import annotations

import contextlib
import logging
import signal
import tkinter as tk
from typing import Any

from plus_ultra.config import (
    APP_NAME,
    get_app_version,
    get_config_dir,
    get_data_dir,
    get_log_path,
    get_metadata,
    get_state_dir,
)
from plus_ultra.core.events import EventBus
from plus_ultra.core.lifecycle import LifecycleManager, LifecycleState
from plus_ultra.database import (
    init_db,
    seed_demo_workspace_data,
)
from plus_ultra.infrastructure.persistence.database_factory import (
    DatabaseFactory,
)
from plus_ultra.models import Reminder, Task
from plus_ultra.platform.factory import (
    PlatformServices,
    create_platform_services,
)
from plus_ultra.platform.interfaces.tray import TrayMenuItem
from plus_ultra.repositories import (
    AppStateRepository,
    CategoryRepository,
    CodeRepository,
    CourseRepository,
    IdeaDoubtRepository,
    OpportunityRepository,
    QuickLinkRepository,
    ReminderRepository,
    TaskRepository,
)
from plus_ultra.scheduler import ReminderScheduler
from plus_ultra.services import (
    CategoryService,
    CodeService,
    CourseService,
    IdeaDoubtService,
    OpportunityService,
    QuickLinkService,
    ReminderService,
    TaskService,
)

logger = logging.getLogger(APP_NAME)


class Application:
    """Manages the lifecycle, services, UI components, and tray integration."""

    def __init__(
        self,
        platform_services: PlatformServices | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.lifecycle = LifecycleManager()
        self.events = event_bus or EventBus()
        self.platform = platform_services or create_platform_services()
        self.db_conn: Any = None
        self.root: tk.Tk | None = None

        # Repositories & Services
        self.app_state_repo: AppStateRepository | None = None
        self.task_service: TaskService | None = None
        self.category_service: CategoryService | None = None
        self.reminder_service: ReminderService | None = None
        self.code_service: CodeService | None = None
        self.course_service: CourseService | None = None
        self.idea_service: IdeaDoubtService | None = None
        self.opportunity_service: OpportunityService | None = None
        self.quick_link_service: QuickLinkService | None = None

        # Subsystems
        self.scheduler: ReminderScheduler | None = None
        self.widget: Any = None
        self.dashboard: Any = None
        self._dispatch_timer_id: str | None = None

    def initialize(
        self,
        seed_data: bool = False,
        no_ui: bool = False,
        smoke_test: bool = False,
    ) -> bool:
        """Advance application through startup states.

        Returns:
            True if initialization succeeded, False if lock contention occurs.
        """
        self.lifecycle.transition_to(LifecycleState.INITIALIZING)

        meta = get_metadata()
        version = get_app_version()
        logger.info("PLUS-ULTRA initializing...")
        logger.info(
            "Application: %s v%s (%s)",
            meta.get("display_name", APP_NAME),
            version,
            meta.get("company", ""),
        )
        logger.info(
            "Host Platform: %s",
            self.platform.capabilities.platform_type.value,
        )
        logger.info("Data directory: %s", get_data_dir())
        logger.info("State directory: %s", get_state_dir())
        logger.info("Config directory: %s", get_config_dir())
        logger.info("Log file: %s", get_log_path())
        logger.info("PLUS-ULTRA foundation initialized successfully.")

        # 1. Platform Single-Instance Lock
        if not self.platform.instance_lock.acquire():
            logger.warning("Another instance of PLUS-ULTRA is already running.")
            return False

        self.lifecycle.register_shutdown_hook(
            self.platform.instance_lock.release
        )
        self.lifecycle.transition_to(LifecycleState.PLATFORM_READY)

        # 2. Database Readiness
        init_db()
        self.db_factory = DatabaseFactory()
        self.db_session = self.db_factory.create_session()
        self.db_conn = self.db_session
        self.lifecycle.register_shutdown_hook(self._safe_close_db)
        if seed_data:
            seed_demo_workspace_data(self.db_session)
        self.lifecycle.transition_to(LifecycleState.DATABASE_READY)

        # 3. Services Readiness
        self._setup_repositories_and_services()
        self.lifecycle.transition_to(LifecycleState.SERVICES_READY)

        if no_ui:
            logger.info("Running in --no-ui mode; foundation ready.")
            return True

        # 4. UI Readiness
        self._setup_ui()
        self._setup_system_tray()
        self._setup_signal_handlers()
        self._setup_scheduler()
        self.lifecycle.transition_to(LifecycleState.UI_READY)

        return True

    def _safe_close_db(self) -> None:
        """Close database session and persistence engine cleanly."""
        if getattr(self, "db_session", None) is not None:
            try:
                self.db_session.close()
                logger.info("Database session closed cleanly.")
            except Exception as exc:
                logger.error("Error closing database session: %s", exc)
            finally:
                self.db_session = None
                self.db_conn = None
        if getattr(self, "db_factory", None) is not None:
            self.db_factory.close()

    def _setup_repositories_and_services(self) -> None:
        """Instantiate data repositories and business services."""
        session = self.db_session
        self.app_state_repo = AppStateRepository(session)
        task_repo = TaskRepository(session)
        cat_repo = CategoryRepository(session)
        rem_repo = ReminderRepository(session)
        code_repo = CodeRepository(session)
        course_repo = CourseRepository(session)
        idea_repo = IdeaDoubtRepository(session)
        opp_repo = OpportunityRepository(session)
        link_repo = QuickLinkRepository(session)

        self.task_service = TaskService(task_repo, cat_repo)
        self.category_service = CategoryService(cat_repo)
        self.reminder_service = ReminderService(rem_repo, task_repo)
        self.code_service = CodeService(code_repo)
        self.course_service = CourseService(course_repo)
        self.idea_service = IdeaDoubtService(idea_repo)
        self.opportunity_service = OpportunityService(opp_repo)
        self.quick_link_service = QuickLinkService(link_repo)

    def _setup_ui(self) -> None:
        """Create FloatingWidget capsule and DashboardPanel."""
        from plus_ultra import settings
        from plus_ultra.ui.floating import FloatingWidget
        from plus_ultra.ui.panel import DashboardPanel
        from plus_ultra.ui.theme import get_theme_by_name

        eff = settings.load_effective_settings()
        active_theme = get_theme_by_name(eff.get("theme", "cyan"))

        saved_pos = (
            self.app_state_repo.get_widget_position()
            if self.app_state_repo
            else None
        )
        init_x = saved_pos[0] if saved_pos else None
        init_y = saved_pos[1] if saved_pos else None

        on_pos_change = (
            self.app_state_repo.set_widget_position
            if self.app_state_repo
            else None
        )

        self.widget = FloatingWidget(
            initial_x=init_x,
            initial_y=init_y,
            on_position_change=on_pos_change,
            theme=active_theme,
        )
        self.root = self.widget.root

        self.dashboard = DashboardPanel(
            parent=self.root,
            task_service=self.task_service,  # type: ignore[arg-type]
            category_service=self.category_service,  # type: ignore[arg-type]
            notification_queue=self.widget.notifications,
            reminder_service=self.reminder_service,  # type: ignore[arg-type]
            code_service=self.code_service,  # type: ignore[arg-type]
            course_service=self.course_service,  # type: ignore[arg-type]
            idea_doubt_service=self.idea_service,  # type: ignore[arg-type]
            opportunity_service=self.opportunity_service,
            quick_link_service=self.quick_link_service,
            theme=active_theme,
            on_notifications_cleared=self.widget._update_bell_state,
            on_open=self.widget.root.withdraw,
            on_close=self.widget.root.deiconify,
            on_terminate=self.shutdown,
        )
        self.widget.on_click_callback = self.dashboard.toggle

        # Override window close protocols so closing dashboard hides it
        self.dashboard.protocol("WM_DELETE_WINDOW", self.hide_dashboard)

        # Register shutdown hook for UI windows
        self.lifecycle.register_shutdown_hook(self._safe_destroy_ui)

    def _safe_destroy_ui(self) -> None:
        """Destroy UI windows cleanly."""
        if self._dispatch_timer_id is not None and self.root:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._dispatch_timer_id)
            self._dispatch_timer_id = None

        if self.dashboard and self.dashboard.winfo_exists():
            try:
                self.dashboard.destroy()
            except Exception as exc:
                logger.debug("Error destroying dashboard: %s", exc)

        if self.widget and not getattr(self.widget, "_closed", True):
            try:
                self.widget.close()
            except Exception as exc:
                logger.debug("Error closing floating widget: %s", exc)

    def _setup_system_tray(self) -> None:
        """Initialize the persistent system tray integration."""
        tray = self.platform.tray
        if not tray.is_supported:
            logger.info("System tray is not supported on this platform.")
            return

        def _make_safe_action(action: str) -> Any:
            return lambda: self.lifecycle.post_to_main_thread(
                lambda: self._handle_tray_action(action)
            )

        menu_items = [
            TrayMenuItem(
                label="Show Dashboard",
                action=_make_safe_action("show_dashboard"),
            ),
            TrayMenuItem(
                label="Hide Dashboard",
                action=_make_safe_action("hide_dashboard"),
            ),
            TrayMenuItem(is_separator=True, label=""),
            TrayMenuItem(
                label="Show Floating Capsule",
                action=_make_safe_action("show_capsule"),
            ),
            TrayMenuItem(
                label="Hide Floating Capsule",
                action=_make_safe_action("hide_capsule"),
            ),
            TrayMenuItem(is_separator=True, label=""),
            TrayMenuItem(
                label="Open Settings",
                action=_make_safe_action("open_settings"),
            ),
            TrayMenuItem(is_separator=True, label=""),
            TrayMenuItem(
                label="Exit PLUS-ULTRA",
                action=_make_safe_action("exit_app"),
            ),
        ]

        def _show_tray_popup(x: int, y: int) -> None:
            self.lifecycle.post_to_main_thread(
                lambda: self._display_tray_menu(x, y, menu_items)
            )

        tray.start(
            tooltip="PLUS-ULTRA Assistant",
            menu_items=menu_items,
            on_menu_popup=_show_tray_popup,
        )
        self.lifecycle.register_shutdown_hook(tray.stop)

    def _display_tray_menu(
        self, x: int, y: int, items: list[TrayMenuItem]
    ) -> None:
        """Display styled Tkinter context popup menu at screen position."""
        if not self.root or not self.root.winfo_exists():
            return
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#1a1f2c",
            fg="#f8fafc",
            activebackground="#00e5ff",
            activeforeground="#0a0e17",
            activeborderwidth=0,
            font=("Helvetica", 10),
        )
        for item in items:
            if not item.visible:
                continue
            if item.is_separator:
                menu.add_separator()
            else:
                action_fn = item.action
                menu.add_command(
                    label=item.label,
                    command=action_fn,
                    state="normal" if item.enabled else "disabled",
                )

        if x <= 0 or y <= 0:
            sw = self.root.winfo_screenwidth()
            x, y = sw - 220, 32

        self._active_tray_menu = menu
        menu.tk_popup(x, y)

    def _handle_tray_action(self, action: str) -> None:
        """Execute tray menu actions on the main UI thread."""
        logger.info("Executing tray action: %s", action)
        if action == "show_dashboard":
            self.show_dashboard()
        elif action == "hide_dashboard":
            self.hide_dashboard()
        elif action == "show_capsule":
            self.show_capsule()
        elif action == "hide_capsule":
            self.hide_capsule()
        elif action == "open_settings":
            self.open_settings()
        elif action == "exit_app":
            self.shutdown()

    def show_dashboard(self) -> None:
        """Show the main workspace dashboard."""
        if self.dashboard and self.dashboard.winfo_exists():
            self.dashboard.show()
            if self.widget and self.widget.root:
                self.widget.root.withdraw()

    def hide_dashboard(self) -> None:
        """Hide the dashboard and restore the capsule."""
        if self.dashboard and self.dashboard.winfo_exists():
            self.dashboard.hide()
            if self.widget and self.widget.root:
                self.widget.root.deiconify()

    def show_capsule(self) -> None:
        """Make the floating capsule visible."""
        if self.widget and self.widget.root:
            self.widget.root.deiconify()

    def hide_capsule(self) -> None:
        """Hide the floating capsule."""
        if self.widget and self.widget.root:
            self.widget.root.withdraw()

    def open_settings(self) -> None:
        """Show dashboard focused on the Settings view."""
        self.show_dashboard()
        if self.dashboard and hasattr(self.dashboard, "sidebar"):
            self.dashboard.sidebar._select("settings")

    def _setup_scheduler(self) -> None:
        """Initialize background reminder evaluation worker."""

        def _handle_reminder_due(task: Task, _rem: Reminder) -> None:
            logger.info(
                "Reminder triggered for '%s' [id=%s]", task.title, task.id
            )

            def _ui_action() -> None:
                if self.widget and not getattr(self.widget, "_closed", True):
                    msg = task.description or f"Priority: {task.critical_level}"
                    self.widget.post_notification(
                        title=f"Due: {task.title}",
                        message=msg,
                    )
                    if self.dashboard and self.dashboard.winfo_exists():
                        self.dashboard._refresh_tasks()
                        self.dashboard._refresh_notifications()

            self.lifecycle.post_to_main_thread(_ui_action)

        self.scheduler = ReminderScheduler(
            reminder_service=self.reminder_service,  # type: ignore[arg-type]
            session_factory=self.db_factory.create_session,
            on_reminder_due=_handle_reminder_due,
            desktop_notify=True,
        )
        self.scheduler.start()
        self.lifecycle.register_shutdown_hook(self.scheduler.stop)

    def _setup_signal_handlers(self) -> None:
        """Register POSIX and Windows termination signals."""

        def _sig_handler(_sig: int, _frame: object) -> None:
            logger.info("Received termination signal, shutting down.")
            self.lifecycle.post_to_main_thread(self.shutdown)

        try:
            signal.signal(signal.SIGINT, _sig_handler)
            signal.signal(signal.SIGTERM, _sig_handler)
        except (ValueError, OSError) as exc:
            logger.debug("Signal handler registration skipped: %s", exc)

    def _pump_main_thread_events(self) -> None:
        """Periodically drain the main-thread cross-thread dispatch queue."""
        if self.lifecycle.state == LifecycleState.STOPPED:
            return
        self.lifecycle.process_main_thread_queue()
        if self.root and self.root.winfo_exists():
            self._dispatch_timer_id = self.root.after(
                50, self._pump_main_thread_events
            )

    def run(self) -> int:
        """Start application main loop and transition to RUNNING state."""
        self.lifecycle.transition_to(LifecycleState.RUNNING)
        if self.root:
            self._pump_main_thread_events()
            try:
                self.root.mainloop()
            finally:
                self.shutdown()
        return 0

    def shutdown(self) -> None:
        """Execute deterministic shutdown and clean up all resources."""
        logger.info("Application shutdown requested.")
        self.lifecycle.shutdown()
        if self.root:
            with contextlib.suppress(Exception):
                self.root.quit()
