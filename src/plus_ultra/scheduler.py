"""Background reminder evaluation scheduler for PLUS-ULTRA.

Applies OS concepts:
- Thread Isolation & Concurrency: Periodic reminder evaluation executes on a
  dedicated daemon thread without blocking the Tkinter UI event loop.
  The worker thread creates its own thread-isolated SQLite connection in WAL
  mode, preventing SQLite check_same_thread concurrency errors.
- Producer-Consumer Flow: The scheduler queries SQLite for due reminders,
  dispatches desktop notifications via subprocess, and enqueues in-app alerts
  to the main thread via thread-safe callbacks.
- Clean Lifecycle & Shutdown: Controlled cancellation using threading.Event.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from plus_ultra import desktop, settings
from plus_ultra.database import get_connection
from plus_ultra.models import Reminder, Task
from plus_ultra.repositories import ReminderRepository, TaskRepository
from plus_ultra.services import ReminderService

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL_S: float = 10.0  # 10,000 ms


class ReminderScheduler:
    """Background polling worker for evaluating due reminders."""

    def __init__(
        self,
        reminder_service: ReminderService,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        on_reminder_due: Callable[[Task, Reminder], None] | None = None,
        desktop_notify: bool = True,
        now_provider: Callable[[], str] | None = None,
        db_path: Path | None = None,
        conn_factory: Callable[[], sqlite3.Connection] | None = None,
    ) -> None:
        self.reminder_service = reminder_service
        self.poll_interval_s = poll_interval_s
        self.on_reminder_due = on_reminder_due
        self.desktop_notify = desktop_notify
        self.now_provider = now_provider
        self.db_path = db_path
        self.conn_factory = conn_factory

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        """Return True if background worker thread is active."""
        return self._thread is not None and self._thread.is_alive()

    def tick(
        self,
        now_iso: str | None = None,
        service: ReminderService | None = None,
    ) -> list[tuple[Reminder, Task]]:
        """Evaluate and dispatch reminders due at or before current time.

        Returns list of (Reminder, Task) pairs that were successfully fired.
        """
        # Respect user settings flag
        eff_settings = settings.load_effective_settings()
        if not eff_settings.get("reminders_enabled", True):
            logger.debug("Reminders disabled in settings; tick skipped.")
            return []

        active_service = service or self.reminder_service

        if now_iso is not None:
            now = now_iso
        elif self.now_provider is not None:
            now = self.now_provider()
        else:
            now = datetime.now(UTC).isoformat()

        due_items = active_service.get_due_reminders(now)
        fired: list[tuple[Reminder, Task]] = []

        for reminder, task in due_items:
            logger.info(
                "Firing reminder %s for task '%s' (due %s)",
                reminder.id,
                task.title,
                reminder.remind_at,
            )

            # 1. Native OS desktop notification via notify-send
            if self.desktop_notify:
                urgency = (
                    "critical" if task.critical_level == "High" else "normal"
                )
                body = (
                    f"Priority: {task.critical_level} | "
                    f"{task.description or 'Due now'}"
                )
                desktop.send_desktop_notification(
                    title=f"Reminder: {task.title}",
                    message=body,
                    urgency=urgency,
                    timeout_ms=5000,
                )

            # 2. In-app notification callback to UI thread
            if self.on_reminder_due is not None:
                try:
                    self.on_reminder_due(task, reminder)
                except Exception as exc:
                    logger.warning("Error in on_reminder_due callback: %s", exc)

            # 3. Mark fired in SQLite to prevent re-firing
            active_service.mark_fired(reminder.id)
            fired.append((reminder, task))

        return fired

    def _run_loop(self) -> None:
        """Internal background thread worker loop with isolated DB session."""
        logger.info(
            "Reminder scheduler started (polling every %.1fs)",
            self.poll_interval_s,
        )

        # Open thread-isolated connection if factory/path available
        thread_conn: sqlite3.Connection | None = None
        thread_service: ReminderService = self.reminder_service

        try:
            if self.conn_factory is not None:
                thread_conn = self.conn_factory()
            else:
                thread_conn = get_connection(self.db_path)

            rem_repo = ReminderRepository(thread_conn)
            task_repo = TaskRepository(thread_conn)
            thread_service = ReminderService(rem_repo, task_repo)
        except Exception as err:
            logger.debug(
                "Thread connection fallback to shared service: %s", err
            )

        try:
            while not self._stop_event.is_set():
                try:
                    self.tick(service=thread_service)
                except Exception as exc:
                    logger.error(
                        "Error during reminder scheduler tick: %s", exc
                    )

                # Sleep responsiveness: wakes immediately on stop_event set
                self._stop_event.wait(self.poll_interval_s)
        finally:
            if thread_conn is not None:
                thread_conn.close()

        logger.info("Reminder scheduler worker thread stopped.")

    def start(self) -> None:
        """Start the background daemon thread if not already running."""
        if self.is_running:
            logger.warning("Scheduler already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ReminderSchedulerThread",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal worker thread to stop and wait for termination."""
        if not self.is_running:
            return

        logger.info("Stopping reminder scheduler...")
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        logger.info("Reminder scheduler cleanly stopped.")
