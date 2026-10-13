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
  - `get_db_path() -> Path`: Path to `plus-ultra.sqlite3` in data dir.
  - `get_log_path() -> Path`: Path to `launcher.log` in state dir.
- **Planned Flags**:
  - `--smoke-test`: Headless/transient UI integration test (Phase 4).
  - `--install-autostart` / `--uninstall-autostart`: XDG autostart generator (Phase 6).

---

## Database Schema (SQLite 3NF, Local-First)

Versioned via `PRAGMA user_version` with WAL journal mode and foreign keys enabled:
- `categories`: `id` (UUID), `name`, `created_at`, `updated_at`, `synced_at`, `is_deleted`
  - Partial unique index `idx_categories_name_active` on `name` WHERE `is_deleted = 0`.
- `tasks`: `id` (UUID), `title`, `notes`, `category_id`, `status` (`todo`, `doing`, `done`), `created_at`, `updated_at`, `synced_at`, `is_deleted`
- `reminders`: `id` (UUID), `task_id`, `remind_at`, `created_at`, `updated_at`, `synced_at`, `is_deleted`
  - Partial index `idx_reminders_due` on `remind_at` WHERE `is_deleted = 0`.
- `reminder_fires`: `reminder_id` (UUID PK), `fired_at` (Device-local firing state).
- `settings`: `key` (PK), `value` (Local machine-written state: `widget_x`, `widget_y`, `last_synced_at`).

---

## Quick Start

```bash
# Sync environment dependencies
uv sync

# Launch application
uv run plus-ultra
```
