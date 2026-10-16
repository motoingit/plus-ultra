"""Tests for plus_ultra.desktop module (POSIX single instance lock).

Validates:
- Mutual Exclusion: First process acquires lock; second process fails.
- Re-acquisition: Lock can be acquired again after release.
- Context manager protocol support.
- File security: Lock file created with mode 0o600.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from plus_ultra.desktop import SingleInstanceLock


def test_lock_acquire_and_release(tmp_path: Path) -> None:
    """Verify exclusive lock acquisition and clean release."""
    lock_file = tmp_path / "test.lock"
    lock1 = SingleInstanceLock(lock_file)

    assert lock1.acquire() is True
    assert lock_file.is_file()

    # Verify mode 0o600
    file_mode = stat.S_IMODE(lock_file.stat().st_mode)
    assert file_mode == 0o600, f"Expected 0o600, got {oct(file_mode)}"

    # Second instance attempting same lock must fail (contention)
    lock2 = SingleInstanceLock(lock_file)
    assert lock2.acquire() is False

    # Release first lock
    lock1.release()

    # Now second instance should successfully acquire
    assert lock2.acquire() is True
    lock2.release()


def test_lock_context_manager(tmp_path: Path) -> None:
    """Verify lock functions cleanly as a context manager."""
    lock_file = tmp_path / "ctx.lock"
    lock1 = SingleInstanceLock(lock_file)

    with lock1 as acquired:
        assert acquired is True
        # Contention while inside context
        lock2 = SingleInstanceLock(lock_file)
        assert lock2.acquire() is False

    # After exiting context, lock is released
    lock3 = SingleInstanceLock(lock_file)
    assert lock3.acquire() is True
    lock3.release()


def test_lock_stores_current_pid(tmp_path: Path) -> None:
    """Verify lock file records process ID of holding process."""
    lock_file = tmp_path / "pid.lock"
    lock = SingleInstanceLock(lock_file)

    assert lock.acquire() is True
    pid_text = lock_file.read_text(encoding="utf-8").strip()
    assert pid_text.isdigit()
    lock.release()


def test_send_desktop_notification_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify notify-send called with argument list and shell=False."""
    from unittest.mock import MagicMock

    from plus_ultra.desktop import send_desktop_notification

    monkeypatch.setattr("shutil.which", lambda _cmd: "/usr/bin/notify-send")
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)

    result = send_desktop_notification(
        title="Lab Deadline",
        message="Operating Systems Assignment 2",
        urgency="critical",
        timeout_ms=3000,
    )
    assert result is True
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd[0] == "/usr/bin/notify-send"
    assert "-u" in cmd and "critical" in cmd
    assert "-t" in cmd and "3000" in cmd
    assert "Lab Deadline" in cmd
    assert "Operating Systems Assignment 2" in cmd
    assert kwargs.get("check") is True


def test_send_desktop_notification_missing_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing notify-send returns False gracefully."""
    from plus_ultra.desktop import send_desktop_notification

    monkeypatch.setattr("shutil.which", lambda _cmd: None)
    result = send_desktop_notification(title="Test", message="Body")
    assert result is False


def test_send_desktop_notification_subprocess_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify subprocess error is caught without crashing."""
    import subprocess

    from plus_ultra.desktop import send_desktop_notification

    monkeypatch.setattr("shutil.which", lambda _cmd: "/usr/bin/notify-send")

    def _mock_raise(*_args: object, **_kwargs: object) -> None:
        raise subprocess.SubprocessError("Command failed")

    monkeypatch.setattr("subprocess.run", _mock_raise)
    result = send_desktop_notification(title="Test", message="Body")
    assert result is False
