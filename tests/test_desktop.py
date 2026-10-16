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
