"""Operating system startup / autostart management interface.

Applies OS concepts:
- Session autostart integration: XDG Autostart specification (.desktop file in
  ~/.config/autostart) on Linux; Windows CurrentVersion\\Run registry / Startup.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StartupManager(Protocol):
    """Protocol for configuring application launch on user login."""

    @property
    def is_supported(self) -> bool:
        """Return True if autostart can be managed on this platform."""
        ...

    def is_autostart_enabled(self) -> bool:
        """Return True if application is currently registered to autostart."""
        ...

    def enable_autostart(self) -> bool:
        """Register application to start automatically upon user session login.

        Returns:
            True if registration succeeded, False otherwise.
        """
        ...

    def disable_autostart(self) -> bool:
        """Unregister application from user session autostart.

        Returns:
            True if unregistration succeeded, False otherwise.
        """
        ...
