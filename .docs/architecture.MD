# Architecture Documentation

This document describes the architectural layout, technology stack, and dependency structure of **PLUS-ULTRA**.

---

# Project Folder Structure

PLUS-ULTRA adheres to a strict 3-layer decoupled architecture (`ui/` -> `services/` -> `repository/`, `db.py`) to isolate presentation from business logic and SQLite persistence.

```text
plus-ultra/
├── .agents/                      # Agent rules, workflows, and phase execution plans
├── .docs/                        # Architecture, API specs, data sources, progress logs
│   ├── api.md                    # Public interfaces and exported module APIs
│   ├── architecture.MD           # Project architecture, tech-stack, and dependencies
│   ├── data-sources.md           # External data tracking specifications
│   └── progress-log.md           # Chronological phase implementation log
├── .env.sample                   # Sample credentials template (Supabase public anon key)
├── pyproject.toml                # Project packaging, CLI script, ruff and pytest configs
├── README.md                     # High-level overview, quick start, and layer summary
├── src/
│   └── plus_ultra/               # Core application package
│       ├── __init__.py           # Package marker
│       ├── config.py             # XDG Base Directory resolution, secure 0o700 permissions
│       ├── main.py               # Process bootstrap, dual logging, argument parsing
│       ├── settings.py           # Atomic JSON settings engine, strict type safety, recovery
│       ├── resources/            # Packaged static assets
│       │   ├── default-settings.json # Shipped defaults (always_on_top, glow, reminders)
│       │   └── metadata.json     # App metadata (app_name, display_name, company, desc)
│       ├── desktop.py            # Single-instance lock (fcntl.flock), notifications
│       ├── ui/                   # Presentation layer (Zero direct DB access)
│       │   ├── __init__.py       # Package marker
│       │   ├── floating.py       # Circular always-on-top draggable floating pill
│       │   ├── theme.py          # UI styling tokens, color palettes, capsule geometry
│       │   └── panel.py          # [Phase 4] Main dashboard window (Treeview, forms, filters)
│       ├── db.py                 # [Phase 3] SQLite connection, WAL mode, transaction context
│       ├── models.py             # [Phase 3] Data classes (Task, Category, Reminder, AppState)
│       ├── repository.py         # [Phase 3] Parameterized SQL CRUD operations
│       ├── services.py           # [Phase 4] Business logic decoupled from GUI
│       ├── scheduler.py          # [Phase 5] Background reminder evaluation thread
│       └── sync.py               # [Phase 7] Differential online synchronization worker
├── tests/                        # Comprehensive test suite (Happy path, edge, failure paths)
│   ├── test_config.py            # XDG paths, fallback logic, mode 0o700, logging tests
│   ├── test_settings.py          # Settings validation, type safety, corrupt file quarantine
│   ├── test_desktop.py           # Single instance lock and process contention tests
│   ├── test_ui.py                # FloatingWidget geometry, hover glow, and drag calculations
│   ├── test_db.py                # [Phase 3] Schema migrations, foreign keys, rollback tests
│   ├── test_repository.py        # [Phase 3] CRUD queries, soft deletes, index verification
│   └── test_services.py          # [Phase 4] Service layer logic tests
└── uv.lock                       # Locked dependency tree
```

# Data Runtime Data Directories (POSIX / XDG)
User state is segregated per the XDG Base Directory specification:
- **`$XDG_CONFIG_HOME/plus-ultra/user-settings.json`** (`~/.config/plus-ultra/`): User configuration overrides. Enforced mode `0o700` on directory, `0o600` on file. Atomic write with crash-resilient `.bad-<timestamp>` quarantine.
- **`$XDG_DATA_HOME/plus-ultra/plus-ultra.sqlite3`** (`~/.local/share/plus-ultra/`): SQLite application database (tasks, reminders, local app_state).
- **`$XDG_STATE_HOME/plus-ultra/launcher.log`** (`~/.local/state/plus-ultra/`): Persistent execution and diagnostic logs.

---

# Project Dependencies

Dependencies are declared in [`pyproject.toml`](file:///home/moto/My-Drive/PBL/plus-ultra/pyproject.toml) and pinned in `uv.lock`.

## 1. Active Runtime Dependencies
Currently, the application runs entirely on the **Python Standard Library** with zero external network dependencies:
- `argparse`: Command-line interface argument parsing.
- `contextlib`: Resource cleanup and exception suppression (`contextlib.suppress`).
- `dataclasses`: Lightweight domain models.
- `datetime`: Timezone-aware timestamp handling (`datetime.UTC`).
- `fcntl`: POSIX file locking (`flock`) for single-instance enforcement.
- `importlib.metadata` & `importlib.resources`: Dynamic version lookup and packaged resource loading.
- `json`: Serialization and parsing of settings and metadata.
- `logging`: Dual-stream logging (stdout and rotating file logs).
- `os` & `stat`: POSIX filesystem permission enforcement (`0o700`, `0o600`) and atomic replacement (`os.replace`).
- `pathlib`: Object-oriented filesystem path manipulation.
- `queue`: Thread-safe communication between background workers and the Tkinter main thread.
- `signal`: OS signal trapping (`SIGINT`, `SIGTERM`) for graceful process termination.
- `sqlite3`: Direct ACID transactional database management.
- `subprocess`: Non-blocking invocation of external system utilities (`notify-send`).
- `threading`: Background execution of scheduler and sync workers off the UI event loop.
- `tkinter`: Native desktop GUI rendering and event dispatch.

## Development Dependencies
Declared in `[dependency-groups].dev`:
- **`pytest >= 9.1.1`**: Automated test framework covering unit tests, edge cases, permission checks, and failure recovery.
- **`ruff >= 0.17.0`**: Fast Python linter and formatter enforcing PEP 8, import order (`I`), simplification (`SIM`), bug prevention (`B`), and strict 80-character line lengths.


## Scheduled Runtime Dependencies (Approved Phased Additions)
- **Phase 5**: `pystray` and `Pillow` (System tray integration).
- **Phase 7**: Supabase client library (added only upon explicit user approval for cloud sync).

---

# Project Tech-Stack

The technology stack is locked to fulfill Problem-Based Learning (PBL) objectives emphasizing Operating Systems (OS) and Database Management Systems (DBMS) fundamentals:

| Component | Technology | Rationale & Concept |
|---|---|---|
| **Host Platform** | Ubuntu Linux (GNOME on Wayland) | Target desktop operating system. Tkinter executes via XWayland. |
| **Language Runtime** | CPython 3.12+ | Managed via `uv`. Modern standard library typing, pattern matching, and performance. |
| **Package & Env Manager** | `uv` | High-performance virtual environment creation, dependency resolution, and locking (`uv.lock`). |
| **GUI Framework** | `tkinter` & `tkinter.ttk` | Standard library GUI toolkit. Decoupled from business logic; isolated to main event loop thread. |
| **Database Engine** | `sqlite3` (Standard Library) | Raw parameterized SQL only (no ORM). Enforces ACID transactions, WAL journal mode, Foreign Keys (`PRAGMA foreign_keys = ON`), and partial indexes. |
| **Machine State Persistence** | SQLite `app_state` table | Dedicated key-value store for machine-written runtime state (`widget_x`, `widget_y`, `last_synced_at`). Kept strictly separate from user preferences. |
| **User Settings Engine** | Custom JSON Layer | Package defaults (`default-settings.json`) overlaid with atomic user overrides (`user-settings.json`). Enforces `0o600` permissions and crash-safe rename (`os.replace`). |
| **Process Management** | `fcntl.flock` (Linux Standard Library) | Single-instance mutual exclusion locking via advisory file locks. |
| **Desktop Notifications** | `notify-send` via `subprocess` | Direct desktop notification dispatch without heavyweight third-party libraries. |
| **System Tray Integration** | `pystray` + `Pillow` | System tray icon integration with status menu. |
| **Remote Sync Engine** | Supabase (PostgreSQL / PostgREST) | Off-thread differential sync engine scheduled for Phase 7 using `updated_at > last_synced_at` conflict resolution. |
| **Code Quality & Testing** | `ruff` & `pytest` | Fast linting/formatting (`ruff`, strict 80-char line limit) and automated testing suite (`pytest`). |