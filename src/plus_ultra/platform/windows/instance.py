"""Windows single-instance lock implementation using msvcrt advisory locking.

Applies OS concepts:
- Mutual exclusion via Win32 / MSVCRT non-blocking file locking (`msvcrt.locking`).
- Process ID recording in lock file for diagnostic inspection.
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path

try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore[assignment]

from plus_ultra.platform.interfaces.paths import PathProvider

logger = logging.getLogger(__name__)

LOCK_OFFSET = 1024


class WindowsSingleInstanceLock:
    """Manages an exclusive advisory lock file on Windows."""

    def __init__(
        self,
        paths: PathProvider | None = None,
        lock_path: Path | None = None,
        lock_filename: str = "plus-ultra.lock",
    ) -> None:
        if lock_path is not None:
            self._lock_path = lock_path
        elif paths is not None:
            self._lock_path = paths.get_state_dir() / lock_filename
        else:
            self._lock_path = Path.cwd() / lock_filename

        self._fd: int | None = None
        self._is_acquired = False

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    @property
    def is_acquired(self) -> bool:
        return self._is_acquired

    def acquire(self) -> bool:
        """Attempt to acquire exclusive lock without blocking."""
        with contextlib.suppress(OSError):
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(
                self._lock_path,
                os.O_RDWR | os.O_CREAT,
                0o600,
            )
            if msvcrt is not None:
                os.lseek(fd, LOCK_OFFSET, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

            # Record PID at start of file for diagnostic inspection
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, f"{os.getpid()}\n".encode())
            os.lseek(fd, 0, os.SEEK_SET)

            self._fd = fd
            self._is_acquired = True
            logger.info(
                "Acquired Windows single-instance lock on %s (pid: %d)",
                self._lock_path,
                os.getpid(),
            )
            return True
        except (BlockingIOError, OSError) as exc:
            logger.warning(
                "Windows single-instance lock contention on %s: %s",
                self._lock_path,
                exc,
            )
            with contextlib.suppress(OSError):
                if "fd" in locals():
                    os.close(fd)
            self._is_acquired = False
            return False

    def release(self) -> None:
        """Release the advisory lock and remove lock file."""
        if self._fd is not None:
            try:
                if msvcrt is not None:
                    os.lseek(self._fd, LOCK_OFFSET, os.SEEK_SET)
                    with contextlib.suppress(OSError):
                        msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                os.close(self._fd)
                logger.info(
                    "Released Windows single-instance lock on %s",
                    self._lock_path,
                )
            except OSError as err:
                logger.error("Error releasing Windows lock: %s", err)
            finally:
                self._fd = None
                self._is_acquired = False
                with contextlib.suppress(OSError):
                    self._lock_path.unlink()

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        self.release()
