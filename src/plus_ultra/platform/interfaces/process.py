"""Process lifecycle and system resource introspection interface.

Applies OS concepts:
- Process management: PID resolution, signal handling, process existence.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ProcessManager(Protocol):
    """Protocol for process introspection and signal operations."""

    def get_current_pid(self) -> int:
        """Return process identifier (PID) of current running process."""
        ...

    def is_pid_running(self, pid: int) -> bool:
        """Check whether a process with given PID exists and is active."""
        ...
