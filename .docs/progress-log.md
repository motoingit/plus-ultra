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

- **Status**: Ready to Implement (Waiting for Go)
- **Target**: Foundation and OS XDG paths

### Phase 1 Planned To-do List:
- [ ] Add development tools `ruff` and `pytest` via `uv add --dev ruff pytest`.
- [ ] Implement `src/plus_ultra/config.py`:
  - [ ] Implement XDG base directory paths (`$XDG_DATA_HOME`, `$XDG_STATE_HOME`, `$XDG_RUNTIME_DIR`).
  - [ ] Enforce POSIX permission mode `0o700` (`rwx------`) on directory creation.
  - [ ] Export application constants (`APP_NAME`, `DB_FILENAME`, `LOG_FILENAME`).
- [ ] Implement dual logging in `src/plus_ultra/main.py` (`launcher.log` in state dir + console).
- [ ] Implement unit tests in `tests/test_config.py` verifying fallback and overridden paths with `pytest` `monkeypatch`.
- [ ] Verify `uv run plus-ultra`, `uv run ruff check .`, and `uv run pytest`.
- [ ] Update documentation (`README.md`, `.docs/api.md`, `.docs/progress-log.md`).
