# PLUS-ULTRA API & Interface Documentation

This document records the public APIs, module interfaces, and command-line entry points across each development phase.

---

## 1. CLI Entry Points

### `plus-ultra`
- **Module**: `plus_ultra.main:main`
- **Current Parameters**: None (launches main process, prints greeting / runs startup).
- **Return Code**: `0` on success.

---

## 2. Module Specifications (Phase 1+)

### `plus_ultra.config` (Phase 1)
- `get_data_dir() -> Path`: Resolves `$XDG_DATA_HOME/plus-ultra` (default: `~/.local/share/plus-ultra`) with `0o700` permissions.
- `get_state_dir() -> Path`: Resolves `$XDG_STATE_HOME/plus-ultra` (default: `~/.local/state/plus-ultra`) with `0o700` permissions.
- `get_runtime_dir() -> Path`: Resolves `$XDG_RUNTIME_DIR/plus-ultra` with fallback to state directory.

---

## 3. Planned Domain & Service Interfaces (Phases 3–7)

### `TaskService` (Phase 4)
- `create_task(title: str, notes: str, category_id: int | None) -> Task`
- `update_task_status(task_id: int, status: str) -> Task`
- `delete_task(task_id: int) -> None`
- `list_tasks(status: str | None, category_id: int | None) -> list[Task]`

### `SyncService` (Phase 7 - Supabase Differential Sync)
- `sync_delta() -> SyncResult`: Compares local changes (`updated_at > last_synced_at`) against remote Supabase records, pushes local deltas, pulls remote mutations, and updates the local sync cursor.
