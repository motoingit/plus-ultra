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
- **Planned Flags**:
  - `--smoke-test`: Headless/transient UI integration test (Phase 4).
  - `--install-autostart` / `--uninstall-autostart`: XDG autostart generator (Phase 6).

---

## Database Schema (SQLite 3NF)

Versioned via `PRAGMA user_version` with WAL journal mode:
- `categories`: `id`, `name`
- `tasks`: `id`, `title`, `notes`, `category_id`, `status` (`todo`, `doing`, `done`), `created_at`, `updated_at`, `synced_at`, `is_deleted`
- `reminders`: `id`, `task_id`, `remind_at`, `fired_at` (Partial index `idx_reminders_due`)
- `settings`: `key`, `value`

---

## Quick Start

```bash
# Sync environment dependencies
uv sync

# Launch application
uv run plus-ultra
```
