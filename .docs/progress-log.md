# Project Progress Log

## Phase 0: Repo Hygiene & Baseline Setup

- **Status**: Completed
- **Date**: 2026-10-12

### Phase To-do List:
- [x] Optimize `pyproject.toml` by removing duplicate console script alias `plus_ultra` and keeping `plus-ultra = "plus_ultra.main:main"`.
- [x] Remove stray comments in `pyproject.toml` and verify tool configs.
- [x] Protect user private space by adding `.my/` to `.gitignore`.
- [x] Preserve `.docs/` and `.agents/` intact as per user instruction.
- [x] Verify package build and run with `uv run plus-ultra`.
- [x] Stage baseline project files and create initial Git commit on `main`.

### Issues & Status:
- **Duplicate console script**: Resolved by removing `plus_ultra` entry in `pyproject.toml`.
- **Private files exposure risk**: Mitigated by explicitly ignoring `.my/` in `.gitignore`.

### Important Points:
- System Python is 3.14.4; `uv` manages CPython 3.12.14 at `~/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12`.
- Tkinter version 9.0 is verified working in the uv CPython 3.12 environment.
- Single entrypoint `plus-ultra` is operational and runs `plus_ultra.main:main`.
- Architecture rule locked: 3-layer architecture (`ui` -> `services` -> `repository/db`) strictly loosely coupled.
- Online Cloud Sync: Incremental differential sync with Supabase scheduled for Phase 7, with delta metadata columns prepared in Phase 3 SQLite schema.

---

## Phase 1: Foundation (Paths, Secure Permissions, Logging)

- **Status**: Completed
- **Date**: 2026-10-13

### Phase 1 To-do List:
- [x] Add development tools `ruff` and `pytest` via `uv add --dev ruff pytest`.
- [x] Implement `src/plus_ultra/config.py`:
  - [x] Implement XDG base directory paths (`$XDG_DATA_HOME`, `$XDG_STATE_HOME`).
  - [x] Enforce POSIX permission mode `0o700` (`rwx------`) on directory creation.
  - [x] Export application constants (`APP_NAME`, `DB_FILENAME`, `LOG_FILENAME`).
  - [x] Helper functions `get_db_path()` and `get_log_path()`.
- [x] Implement dual logging in `src/plus_ultra/main.py` (`launcher.log` in state dir + console stdout) with ISO-8601 timestamps.
- [x] Implement unit tests in `tests/test_config.py` verifying fallback, overridden paths, mode `0o700` permissions, unicode names, empty variables, and startup logging.
- [x] Verify gate: `uv run plus-ultra` writes startup lines and exits 0; `uv run ruff check .` and `uv run pytest` pass cleanly (9 tests passed).
- [x] Update documentation (`README.md`, `.docs/api.md`, `.docs/progress-log.md`).

### Issues & Status:
- **Line length and import sorting**: Resolved by configuring imports and wrapping docstrings to satisfy `ruff` 80-character limit.
- **Exception handling style**: Replaced `try-except-pass` with `contextlib.suppress(OSError)` in `_ensure_private_directory()` per ruff rule `SIM105`.
- **Package import structure**: Cleaned `src/plus_ultra/__init__.py` to avoid shadowing `plus_ultra.main:main`.

### Important Points:
- Verified on disk: `/home/moto/.local/share/plus-ultra` and `/home/moto/.local/state/plus-ultra` created with permissions `drwx------` (`0o700`).
- Gate passed: `uv run plus-ultra` executed cleanly with exit code 0 and populated `/home/moto/.local/state/plus-ultra/launcher.log`.
- All 9 unit tests in `tests/test_config.py` passed in 0.02s.

---

## Phase 1b: Secrets, Metadata, Settings

- **Status**: Completed
- **Date**: 2026-10-13

### Phase 1b To-do List:
- [x] Create `.env.sample` with public placeholders (`SUPABASE_URL`, `SUPABASE_ANON_KEY`); verify `.env` is uncommitted and protected in `.gitignore`.
- [x] Add package metadata resource (`src/plus_ultra/resources/metadata.json`) and dynamic version lookup via `importlib.metadata`.
- [x] Add locked default settings resource (`src/plus_ultra/resources/default-settings.json`) with keys: `settings_version`, `always_on_top`, `glow_enabled`, `glow_pulse_period_ms`, `reminders_enabled`.
- [x] Implement `src/plus_ultra/config.py` helpers: `get_config_dir()`, `get_user_settings_path()`, `get_app_version()`, `get_metadata()`.
- [x] Implement `src/plus_ultra/settings.py` settings manager:
  - [x] Strict type validation (`type(val) is type(default_val)`).
  - [x] Ignore unknown keys and ignore type-mismatched values.
  - [x] Defensive recovery for corrupted JSON by quarantining to `.bad-<timestamp>` without crashing.
  - [x] Atomic writes using temporary file in same directory + `os.replace` + `fsync` with mode `0o600`.
  - [x] Reject machine state keys (`widget_x`, `widget_y`).
  - [x] Exposed APIs: `load_effective_settings()`, `load_default_settings()`, `update_user_setting()`, `reset_setting()`, `reset_all_settings()`, `reload()`.
- [x] Implement unit tests in `tests/test_settings.py` and expand `tests/test_config.py` (23 total tests passing).
- [x] Verify formatter, linter, test suite, and CLI execution.

### Issues & Status:
- **Type safety for booleans**: `isinstance(True, int)` evaluates to `True` in Python. Resolved by enforcing strict identity check `type(user_val) is type(default_val)`.
- **Linting rule UP017**: Used `datetime.UTC` alias in place of `timezone.utc`.
- **Ruff line length**: Formatted all docstrings, assertions, and functions to fit strictly within 80 characters.

### Important Points:
- Atomic replacement guarantees settings file integrity during power-loss or crash.
- Filesystem permissions: Config directory mode `0o700` (`drwx------`), user settings file mode `0o600` (`-rw-------`).
- Total test suite now runs 23 tests in 0.04s with 100% pass rate.

---

## Next: Phase 2: Wayland/XWayland Spike + Single Instance Lock

- **Status**: Pending Gate Approval
- **Target**: Evaluate Tkinter floating behavior under GNOME Wayland/XWayland and implement single-instance process lock using standard-library `fcntl.flock`.
