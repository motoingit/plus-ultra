# Building Standalone Executables & Production Distribution

PLUS-ULTRA can be compiled into a self-contained, standalone production executable using `PyInstaller`.

---

## 1. How Persistent Storage & Configuration Work in the Executable

When you run `dist/plus-ultra.exe` (on Windows) or `dist/plus-ultra` (on Linux):

1. **Self-Contained Bundle**:
   - Python 3.12 runtime, Tkinter/Tcl/Tk libraries, Pillow, and static icons/metadata are packaged directly inside the executable.
   - No external Python installation or virtual environment is required on the user's machine.

2. **Persistent External Storage (Zero Data Loss on Rebuild/Update)**:
   - User database records, task notes, reminders, categories, and settings are **NOT** stored inside the executable or temporary directory.
   - The Platform Abstraction Layer (PAL) automatically persists data in the standard operating system profile directories:
     - **Windows**:
       - SQLite Database: `%LOCALAPPDATA%\plus-ultra\plus-ultra.sqlite3`
       - Ephemeral State / Locks: `%LOCALAPPDATA%\plus-ultra\state\`
       - Launcher Logs: `%LOCALAPPDATA%\plus-ultra\state\launcher.log`
       - User Preferences: `%APPDATA%\plus-ultra\user-settings.json`
     - **Linux (GNOME / Wayland / X11)**:
       - SQLite Database: `$XDG_DATA_HOME/plus-ultra/plus-ultra.sqlite3` (fallback: `~/.local/share/plus-ultra/`)
       - Ephemeral State / Locks: `$XDG_STATE_HOME/plus-ultra/` (fallback: `~/.local/state/plus-ultra/`)
       - Launcher Logs: `$XDG_STATE_HOME/plus-ultra/launcher.log`
       - User Preferences: `$XDG_CONFIG_HOME/plus-ultra/user-settings.json` (fallback: `~/.config/plus-ultra/`)
   - **Result**: You can replace, rebuild, or upgrade `plus-ultra.exe` at any time without resetting or losing any user data.

---

## 2. Building on Windows (`dist/plus-ultra.exe`)

Run from project root in PowerShell:

```powershell
uv run pyinstaller plus-ultra.spec --noconfirm
```

The resulting executable will be generated at:
```
dist\plus-ultra.exe
```

### Windows Production Features:
- **No Console Window**: Built with `console=False` (no flashing black command prompt).
- **System Tray Notification Area**: Registers icon beside system clock with interactive context menu.
- **Embedded Application Icon**: Includes 7-resolution `app.ico` (16x16 up to 256x256).
- **Single-Instance Enforcement**: Advisory file locking prevents duplicate processes.

---

## 3. Building on Linux (`dist/plus-ultra`)

Run in bash on Ubuntu / Linux:

```bash
uv run pyinstaller plus-ultra.spec --noconfirm
chmod +x dist/plus-ultra
./dist/plus-ultra
```

---

## 4. Automated Windows Setup & Installation Script

To install PLUS-ULTRA for the current Windows user without admin privileges:

```powershell
powershell -ExecutionPolicy Bypass -File .scripts/install.ps1
```

This installer:
1. Copies `dist/plus-ultra.exe` to `%LOCALAPPDATA%\Programs\plus-ultra\`.
2. Creates a Desktop Shortcut.
3. Creates a Start Menu Shortcut under `PLUS-ULTRA`.
4. Configures optional automatic startup on user login.
