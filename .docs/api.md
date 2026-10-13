# PLUS-ULTRA API & Interface Documentation

This document records public APIs, module interfaces, and command-line entry points across each development phase.

---

## 1. CLI Entry Points

### `plus-ultra`
- **Module**: `plus_ultra.main:main`
- **Arguments**:
  - `argv: list[str] | None`: Command line arguments (defaults to `sys.argv[1:]`).
- **Return Code**: `0` on successful execution.
- **Behavior**: Initializes dual logging (`sys.stdout` and `$XDG_STATE_HOME/plus-ultra/launcher.log`), logs startup paths, and exits cleanly.

---

## 2. Implemented Module Specifications (Phase 1)

### `plus_ultra.config`
- `get_data_dir() -> Path`: Resolves `$XDG_DATA_HOME/plus-ultra` (fallback: `~/.local/share/plus-ultra`). Creates directory with mode `0o700`.
- `get_state_dir() -> Path`: Resolves `$XDG_STATE_HOME/plus-ultra` (fallback: `~/.local/state/plus-ultra`). Creates directory with mode `0o700`.
- `get_db_path() -> Path`: Returns `get_data_dir() / "plus-ultra.sqlite3"`.
- `get_log_path() -> Path`: Returns `get_state_dir() / "launcher.log"`.
- **Constants**:
  - `APP_NAME: str = "plus-ultra"`
  - `DB_FILENAME: str = "plus-ultra.sqlite3"`
  - `LOG_FILENAME: str = "launcher.log"`

### `plus_ultra.main`
- `configure_logging() -> Path`: Sets up dual logging handlers (FileHandler with UTF-8 encoding in state directory, StreamHandler to stdout) with ISO-8601 timestamps. Returns the active log file path.
- `parse_args(args: list[str] | None = None) -> argparse.Namespace`: Parses CLI arguments.
- `main(argv: list[str] | None = None) -> None`: Main application routine.

---

## 3. Upcoming Specifications

### `plus_ultra.settings` (Phase 1b)
- `load_settings() -> dict[str, Any]`: Overlays user overrides (`user-settings.json`) onto read-only defaults (`default-settings.json`).
- `update_setting(key: str, value: Any) -> None`: Atomically writes overridden key to `user-settings.json` (temp file + `os.replace`, mode `0o600`).
- `reload() -> dict[str, Any]`: Explicitly reloads settings from disk.

### `plus_ultra.services.TaskService` (Phase 4)
- `create_task(title: str, notes: str, category_id: str | None) -> Task`
- `update_task_status(task_id: str, status: str) -> Task`
- `soft_delete_task(task_id: str) -> None`: Soft-deletes task and associated reminders in a single transaction.
- `list_tasks(status: str | None, category_id: str | None) -> list[Task]`

### `plus_ultra.sync.SyncService` (Phase 7 - Supabase Differential Sync)
- `sync_delta() -> SyncResult`: Differential sync comparing `updated_at > last_synced_at`, pushing local mutations and pulling remote changes.
