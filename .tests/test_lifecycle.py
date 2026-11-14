"""Automated tests for Application lifecycle, shutdown, and threading dispatch.

Validates:
- Lifecycle state transitions.
- Idempotent shutdown and reverse (LIFO) hook execution.
- Exception resilience during shutdown hooks.
- Thread-safe dispatch queue to main UI loop.
- Single-instance contention prevention.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plus_ultra.core.application import Application
from plus_ultra.core.exceptions import LifecycleError
from plus_ultra.core.lifecycle import LifecycleManager, LifecycleState
from plus_ultra.platform.factory import create_platform_services


def test_lifecycle_state_progression() -> None:
    """Verify standard forward state progression."""
    lm = LifecycleManager()
    assert lm.state == LifecycleState.UNINITIALIZED
    assert lm.is_running is False

    lm.transition_to(LifecycleState.INITIALIZING)
    assert lm.state == LifecycleState.INITIALIZING

    lm.transition_to(LifecycleState.RUNNING)
    assert lm.is_running is True

    lm.shutdown()
    assert lm.state == LifecycleState.STOPPED
    assert lm.is_running is False


def test_invalid_lifecycle_transition() -> None:
    """Transitioning while shutting down raises LifecycleError."""
    lm = LifecycleManager()
    lm.transition_to(LifecycleState.SHUTTING_DOWN)

    with pytest.raises(LifecycleError):
        lm.transition_to(LifecycleState.RUNNING)


def test_shutdown_hooks_lifo_order() -> None:
    """Hooks run in reverse order of registration (LIFO)."""
    lm = LifecycleManager()
    order = []

    lm.register_shutdown_hook(lambda: order.append("first_registered"))
    lm.register_shutdown_hook(lambda: order.append("second_registered"))
    lm.register_shutdown_hook(lambda: order.append("third_registered"))

    lm.shutdown()

    assert order == [
        "third_registered",
        "second_registered",
        "first_registered",
    ]


def test_shutdown_is_idempotent() -> None:
    """Calling shutdown repeatedly executes hooks only once."""
    lm = LifecycleManager()
    runs = 0

    def _hook() -> None:
        nonlocal runs
        runs += 1

    lm.register_shutdown_hook(_hook)
    lm.shutdown()
    lm.shutdown()
    lm.shutdown()

    assert runs == 1
    assert lm.state == LifecycleState.STOPPED


def test_shutdown_resilient_to_failing_hook() -> None:
    """A failing hook does not prevent subsequent hooks from running."""
    lm = LifecycleManager()
    ran = []

    def _failing_hook() -> None:
        raise RuntimeError("Cleanup failed")

    lm.register_shutdown_hook(lambda: ran.append("safe_hook_1"))
    lm.register_shutdown_hook(_failing_hook)
    lm.register_shutdown_hook(lambda: ran.append("safe_hook_2"))

    lm.shutdown()

    assert "safe_hook_2" in ran
    assert "safe_hook_1" in ran
    assert lm.state == LifecycleState.STOPPED


def test_main_thread_dispatch_queue() -> None:
    """Items queued via post_to_main_thread are processed in order."""
    lm = LifecycleManager()
    results = []

    lm.post_to_main_thread(lambda: results.append(1))
    lm.post_to_main_thread(lambda: results.append(2))
    lm.post_to_main_thread(lambda: results.append(3))

    processed = lm.process_main_thread_queue()
    assert processed == 3
    assert results == [1, 2, 3]


def test_application_initialization_no_ui(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Application initializes cleanly in --no-ui mode."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    app = Application()
    success = app.initialize(no_ui=True)
    assert success is True
    assert app.lifecycle.state == LifecycleState.SERVICES_READY
    app.shutdown()
    assert app.lifecycle.state == LifecycleState.STOPPED


def test_application_lock_contention() -> None:
    """When another instance holds the lock, initialize returns False."""
    mock_lock = MagicMock()
    mock_lock.acquire.return_value = False

    services = create_platform_services(instance_lock=mock_lock)
    app = Application(platform_services=services)

    success = app.initialize(no_ui=True)
    assert success is False
    assert app.lifecycle.state == LifecycleState.INITIALIZING
