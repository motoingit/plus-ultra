"""Application-level exception hierarchy for PLUS-ULTRA.

Applies OS and Software Architecture concepts:
- Explicit exception typing prevents concealing unexpected programmer errors.
- Clean separation between platform, persistence, configuration, and UI errors.
"""

from __future__ import annotations


class PlusUltraError(Exception):
    """Base exception for all domain errors within PLUS-ULTRA."""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class PlatformError(PlusUltraError):
    """Raised when an operating system or platform adapter operation fails."""


class UnsupportedPlatformError(PlatformError):
    """Raised when the host operating system is unsupported."""


class SingleInstanceError(PlatformError):
    """Raised when another application instance holds exclusive execution."""


class TrayError(PlatformError):
    """Raised when the system tray backend fails to initialize or update."""


class NotificationError(PlatformError):
    """Raised when dispatching a desktop notification fails."""


class SettingsError(PlusUltraError):
    """Raised when settings validation, loading, or serialization fails."""


class LifecycleError(PlusUltraError):
    """Raised when an invalid application lifecycle state transition occurs."""


class StorageError(PlusUltraError):
    """Raised when database or filesystem persistence fails."""
