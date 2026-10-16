---
trigger: always_on
description: Enforce the project's locked technology stack and require approval before changing it
---

---
trigger: always_on
description: Enforce the project's locked technology stack and require approval before changing it
---

# Project Tech Stack Rules

The following technology decisions are locked and are the source of truth for technology choices. Do not replace, remove, or introduce competing technologies without explaining the reason, alternatives, and trade-offs, then asking the user for approval.

If another project instruction (including `GEMINI.md`) conflicts with this file, do not guess which instruction to follow. Treat the conflict as unresolved, explain it to the user, and request approval before making stack-related changes. Do not silently change this file or another instruction file to resolve a conflict.

## Platform
- Target: Ubuntu with GNOME on **Wayland**. Tkinter runs through XWayland, not as a native Wayland client.
- Respect the limits documented in the "GUI limitations (Wayland / XWayland)" section 
- if that file and section exist. If they do not exist, report this gap rather than inventing their contents.
- Do not use X11-only window hacks (`xdotool`, `wmctrl`, `xprop`, raw Xlib calls) without asking. They do not control Wayland-native windows reliably and may not work for this application.

## Tooling
- Use `uv` for Python environment and dependency management.
- Use CPython 3.12.
- The `uv`-managed Python distribution used by this project is expected to bundle Tk. Do not recommend `apt install python3-tk` by default; reassess only if the actual environment demonstrates that Tk is unavailable.

## GUI
- Use Tkinter (`tkinter` and `tkinter.ttk`).
- Tkinter was chosen for simplicity. Do not silently replace it with PySide6, Qt, GTK, or another toolkit.
- Be honest about Wayland/XWayland limitations, especially always-on-top behavior, global positioning, transparency, and window-manager control. Do not promise unsupported behavior; explain constraints and ask before adopting a workaround that changes the approved approach.

## Storage
- Use the Python standard-library `sqlite3` module.
- Do not add an ORM; write SQL directly, with parameterized queries only.
- SQLite is the chosen upgrade from the previous JSON-based storage approach.
- Keep database access behind a clear persistence/data-access layer. Use transactions where multiple related changes must succeed or fail together, and preserve user data during schema changes and migrations.

## System Tray
- Use `pystray` for system-tray integration.
- Use `Pillow` for image handling.
- On Linux, pystray's AppIndicator backend needs system bindings (PyGObject and AppIndicator typelibs) that a plain `uv` virtual environment may not see. If the tray icon does not appear, diagnose and report the actual issue, then stop and follow Change Control. Do not swap the library or install system packages on your own.

## Notifications
- Send desktop notifications by invoking `notify-send` through Python's `subprocess` module, with an argument list and never `shell=True`.
- Check whether `notify-send` is available and handle failure gracefully without crashing the application.
- Do not add another Python notification dependency unless the user approves a change.

## Standard Library
These need no approval: `argparse`, `dataclasses`, `datetime`, `fcntl`, `logging`, `pathlib`, `queue`, `signal`, `sqlite3`, `subprocess`, `threading`, `tkinter`.

## Packaging and Launching
- Do not package this PBL project as a Snap or `.deb` package; that overhead has been explicitly rejected.
- Use `uv run plus-ultra` to launch the application. The only console script is `plus-ultra`.
- Use a `.desktop` entry for autostart.
- Keep autostart paths and commands valid for the actual checkout and `uv` environment; do not hard-code a different user's home directory.

## Development Tools
- Use `ruff` for linting and formatting.
- Use `pytest` for tests.
- Tool configuration lives in `pyproject.toml`.

## Change Control
1. Before implementation, inspect the repository and relevant instructions so these decisions are applied consistently.
2. If a locked choice appears unsuitable or impossible in the actual environment, explain why and present clear alternatives with trade-offs.
3. Ask the user before changing any locked decision. Do not treat a recommendation, convenience, or assumption as approval.
4. Keep project files and dependencies consistent with the approved stack. Do not silently edit `pyproject.toml` or related files to introduce an unapproved alternative.
5. If a change would require editing another instruction file, ask the user first unless the user explicitly requested that specific file be edited.

## Stack Summary
- Ubuntu with GNOME on Wayland; account for Tkinter/XWayland limitations.
- `uv` and CPython 3.12.
- Tkinter/ttk for the GUI.
- Standard-library `sqlite3`, raw parameterized SQL, no ORM.
- `pystray` and Pillow for the system tray.
- `notify-send` invoked through `subprocess` for desktop notifications.
- `ruff` and `pytest` for development.
- Launch with `uv run plus-ultra`; autostart with a `.desktop` entry.
- No Snap or `.deb` packaging.