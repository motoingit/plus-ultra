# PLUS-ULTRA 🚀

A floating desktop assistant for Ubuntu (GNOME on Wayland) engineered as a Problem-Based Learning (PBL) project. PLUS-ULTRA features an always-on-top compact widget, task and reminder management panel, system tray integration, desktop notifications, and explicit implementations of core Operating System (OS) and Database Management System (DBMS) concepts.

---

## Architecture Overview (3-Layer Separation)

The codebase strictly enforces loose coupling and layer isolation:

```
[ UI Layer ]               ui/floating.py, ui/panel.py, ui/theme.py
      │ (calls)
[ Services Layer ]         services.py, scheduler.py (Zero Tkinter code)
      │ (calls)
[ Repository & DB Layer ]  repository.py, db.py (Raw parameterized SQL, SQLite WAL)
      │ (uses)
[ Desktop Adapter ]        desktop.py (notify-send, fcntl.flock)
```

- **UI (`ui/`)**: Displays widgets and handles user gestures. Never touches SQLite or SQL queries directly.
- **Services (`services.py`)**: Pure business logic (tasks, categories, reminders, filters). Decoupled from Tkinter for headless testing and future API extensions.
- **Repository (`repository.py`) & DB (`db.py`)**: Isolated persistence layer using SQLite standard library, transactions, and migration runner.

---

## Top APIs & Entry Points

- **Console CLI Entrypoint**:
  ```bash
  plus-ultra
  ```
  Runs `plus_ultra.main:main()`.
- **Core Config API (`plus_ultra.config`)**:
  - `get_data_dir() -> Path`: Resolves `$XDG_DATA_HOME/plus-ultra` (fallback `~/.local/share/plus-ultra`, mode `0o700`).
  - `get_state_dir() -> Path`: Resolves `$XDG_STATE_HOME/plus-ultra` (fallback `~/.local/state/plus-ultra`, mode `0o700`).
  - `get_config_dir() -> Path`: Resolves `$XDG_CONFIG_HOME/plus-ultra` (fallback `~/.config/plus-ultra`, mode `0o700`).
  - `get_db_path() -> Path`: Path to `plus-ultra.sqlite3` in data dir.
  - `get_log_path() -> Path`: Path to `launcher.log` in state dir.
  - `get_user_settings_path() -> Path`: Path to `user-settings.json` in config dir.
  - `get_app_version() -> str`: Returns installed package version.
  - `get_metadata() -> dict[str, Any]`: Loads application metadata from packaged resources.
- **Settings API (`plus_ultra.settings`)**:
  - `load_effective_settings() -> dict[str, Any]`: Defaults merged with user overrides.
  - `load_default_settings() -> dict[str, Any]`: Read-only package defaults.
  - `update_user_setting(key: str, value: Any) -> dict[str, Any]`: Validates types, persists atomically (mode `0o600`).
  - `reset_setting(key: str) -> None`: Restores default for a single setting.
  - `reset_all_settings() -> None`: Clears all user overrides.
  - `reload() -> dict[str, Any]`: Refreshes settings cache from disk.
- **Desktop Adapter (`plus_ultra.desktop`)**:
  - `SingleInstanceLock`: Advisory POSIX process locking (`fcntl.flock`) preventing duplicate concurrent instances.
- **Floating UI (`plus_ultra.ui.floating`)**:
  - `FloatingWidget`: Top-center hovering capsule widget with hover glow, smooth dragging, and topmost window stacking.
- **Supported Flags**:
  - `--smoke-test`: Transient UI launch (runs 500ms and exits 0 for automated verification).
  - `--no-ui`: Initialize logging and foundation without starting GUI.
- **Planned Flags**:
  - `--install-autostart` / `--uninstall-autostart`: XDG autostart generator (Phase 6).

---

## Quick Start

```bash
# Sync environment dependencies
uv sync

# Launch application
uv run plus-ultra
```
