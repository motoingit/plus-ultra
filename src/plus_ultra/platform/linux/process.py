"""Linux process introspection provider.

Applies OS concepts:
- Linux /proc filesystem and POSIX kill signals (signal 0 probe).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class LinuxProcessManager:
    """Provides process introspection for Linux."""

    def get_current_pid(self) -> int:
        return os.getpid()

    def is_pid_running(self, pid: int) -> bool:
        """Check if process with PID exists and is running."""
        if pid <= 0:
            return False
        # Fast path via /proc
        proc_dir = Path(f"/proc/{pid}")
        if proc_dir.is_dir():
            return True
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
