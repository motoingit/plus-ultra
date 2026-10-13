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

## Next: Phase 1b: Secrets, Metadata, Settings

- **Status**: Ready for Planning & Key Approval
- **Target**: Static metadata JSON, read-only default settings, and atomic user overrides in `$XDG_CONFIG_HOME/plus-ultra/user-settings.json`.
