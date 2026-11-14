"""Application lifecycle state machine and shutdown orchestration.

Applies OS concepts:
- Deterministic process shutdown: cleans up locks, threads, sockets, and files.
- Graceful degradation: failing cleanups are logged without halting shutdown.
- Thread-safe dispatch: marshals background callbacks to the UI event loop.
"""

from __future__ import annotations

import enum
import logging
import queue
import threading
from collections.abc import Callable
from typing import Any

from plus_ultra.core.exceptions import LifecycleError

logger = logging.getLogger(__name__)


class LifecycleState(str, enum.Enum):
    """Explicit application lifecycle states."""

    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    PLATFORM_READY = "PLATFORM_READY"
    DATABASE_READY = "DATABASE_READY"
    SERVICES_READY = "SERVICES_READY"
    UI_READY = "UI_READY"
    RUNNING = "RUNNING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"


class LifecycleManager:
    """Orchestrates state transitions and manages cleanup handlers."""

    def __init__(self) -> None:
        self._state = LifecycleState.UNINITIALIZED
        self._lock = threading.RLock()
        self._shutdown_hooks: list[Callable[[], None]] = []
        self._dispatch_queue: queue.Queue[Callable[[], None]] = queue.Queue()

    @property
    def state(self) -> LifecycleState:
        """Return the current lifecycle state."""
        with self._lock:
            return self._state

    @property
    def is_running(self) -> bool:
        """Return True if application is in RUNNING state."""
        with self._lock:
            return self._state == LifecycleState.RUNNING

    def transition_to(self, new_state: LifecycleState) -> None:
        """Advance lifecycle state, validating valid progression."""
        with self._lock:
            if self._state == LifecycleState.STOPPED:
                logger.debug(
                    "Cannot transition from STOPPED to %s", new_state.value
                )
                return

            if self._state == LifecycleState.SHUTTING_DOWN and new_state not in (
                LifecycleState.SHUTTING_DOWN,
                LifecycleState.STOPPED,
            ):
                raise LifecycleError(
                    f"Cannot transition to {new_state.value} while shutting down"
                )

            logger.info(
                "Lifecycle transition: %s -> %s",
                self._state.value,
                new_state.value,
            )
            self._state = new_state

    def register_shutdown_hook(self, hook: Callable[[], None]) -> None:
        """Register a callback executed during shutdown (LIFO order)."""
        with self._lock:
            if hook not in self._shutdown_hooks:
                self._shutdown_hooks.append(hook)

    def shutdown(self) -> None:
        """Execute all shutdown hooks in reverse registration order.

        Idempotent: safe to call repeatedly.
        """
        with self._lock:
            if self._state in (
                LifecycleState.SHUTTING_DOWN,
                LifecycleState.STOPPED,
            ):
                return
            self.transition_to(LifecycleState.SHUTTING_DOWN)
            hooks_to_run = list(reversed(self._shutdown_hooks))

        logger.info("Executing %d shutdown hooks...", len(hooks_to_run))
        for hook in hooks_to_run:
            try:
                hook()
            except Exception as exc:
                logger.error(
                    "Error executing shutdown hook %s: %s",
                    hook,
                    exc,
                    exc_info=True,
                )

        with self._lock:
            self._state = LifecycleState.STOPPED
        logger.info("Application lifecycle STOPPED.")

    def post_to_main_thread(self, callback: Callable[[], None]) -> None:
        """Enqueue a callable to be processed on the main UI thread."""
        self._dispatch_queue.put(callback)

    def process_main_thread_queue(self) -> int:
        """Process all pending queued callbacks on the main UI thread.

        Returns:
            Count of callbacks executed.
        """
        count = 0
        while True:
            try:
                cb = self._dispatch_queue.get_nowait()
            except queue.Empty:
                break
            try:
                cb()
                count += 1
            except Exception as exc:
                logger.error("Error in dispatched main-thread callback: %s", exc)
            finally:
                self._dispatch_queue.task_done()
        return count
