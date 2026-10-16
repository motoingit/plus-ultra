# Project Folder Structure

PLUS-ULTRA adheres to a strict 3-layer decoupled architecture (`ui/` -> `services/` -> `repository/`, `db.py`) to isolate presentation from business logic and SQLite persistence.

```text
plus-ultra/
├── .agents/                      # Agent rules, workflows, and phase execution plans
├── .docs/                        # Architecture, API specs, features, progress logs
│   ├── api.md                    # Public interfaces and exported module APIs
│   ├── architecture.MD           # Project architecture, tech-stack, and dependencies
│   ├── commands.md               # CLI commands, test flags, manual checklists
│   ├── features.md               # 6-tab workspace specifications & db schema
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
│       ├── notifications.py      # Capsule notification queue & width sizing
│       ├── models.py             # Strongly typed data models (Category, Task, Reminder, AppState)
│       ├── scheduler.py          # Background reminder evaluation thread
│       ├── sync.py               # [Phase 7] Differential online synchronization worker
│       ├── db.py                 # Facade re-exporting plus_ultra.database
│       ├── repository.py         # Facade re-exporting plus_ultra.repositories
│       ├── database/             # SQLite connection, schema, migrations, seeds
│       │   ├── __init__.py       # Package marker & public re-exports
│       │   ├── connection.py     # Connection factory, WAL pragma, transaction CM
│       │   ├── schema.py         # Schema v1 & v2 SQL statements
│       │   ├── migrations.py     # Schema version discovery & runner
│       │   └── seeds.py          # Rich demo seed dataset
│       ├── repositories/         # Parameterized SQL repositories (1 table per repo)
│       │   ├── __init__.py       # Package marker & re-exports
│       │   ├── base.py           # Base helpers & converters
│       │   ├── app_state_repository.py
│       │   ├── category_repository.py
│       │   ├── code_repository.py
│       │   ├── course_repository.py
│       │   ├── idea_doubt_repository.py
│       │   ├── opportunity_repository.py
│       │   ├── quick_link_repository.py
│       │   ├── reminder_repository.py
│       │   └── task_repository.py
│       ├── services/             # Pure business logic services (decoupled)
│       │   ├── __init__.py       # Package marker & re-exports
│       │   ├── category_service.py
│       │   ├── code_service.py
│       │   ├── course_service.py
│       │   ├── idea_doubt_service.py
│       │   ├── opportunity_service.py
│       │   ├── quick_link_service.py
│       │   ├── reminder_service.py
│       │   └── task_service.py
│       └── ui/                   # Modular presentation layer (zero direct SQL)
│           ├── __init__.py       # Package marker
│           ├── theme.py          # Design tokens, color palettes, fonts
│           ├── geometry.py       # Mathematical capsule perimeter generator
│           ├── floating.py       # Dynamic capsule widget with animated beam
│           ├── panel.py          # Dashboard coordinator window
│           ├── components/       # Reusable UI widgets
│           │   ├── __init__.py
│           │   ├── scrollable.py # Scrollable canvas frame
│           │   ├── sidebar.py    # Collapsible/tab navigation bar
│           │   └── notifications_panel.py # Right-hand alert stream
│           ├── dialogs/          # Modal forms with fixed bottom action bars
│           │   ├── __init__.py
│           │   ├── base.py       # Modal centering utility
│           │   ├── task_dialog.py
│           │   ├── code_dialog.py
│           │   ├── course_dialog.py
│           │   ├── idea_dialog.py
│           │   ├── opportunity_dialog.py
│           │   ├── quick_link_dialog.py
│           │   └── category_dialog.py
│           └── views/            # Specialized tab content views
│               ├── __init__.py
│               ├── tasks_view.py
│               ├── code_view.py
│               ├── courses_view.py
│               ├── ideas_view.py
│               ├── opportunities_view.py
│               ├── quick_links_view.py
│               └── settings_view.py
├── tests/                        # Comprehensive test suite (81 tests, 100% pass)
│   ├── test_config.py            # XDG paths, fallback logic, mode 0o700, logging tests
│   ├── test_settings.py          # Settings validation, type safety, corrupt file quarantine
│   ├── test_desktop.py           # Advisory locking, notify-send, and process contention
│   ├── test_notifications.py     # Queue management and popup sizing tests
│   ├── test_ui.py                # Mathematical capsule, beam, popup lifecycle
│   ├── test_db.py                # Schema migrations, foreign keys, rollback, pragmas, indexes
│   ├── test_repository.py        # CRUD queries, soft deletes, index verification, app state
│   ├── test_services.py          # Pure business logic, status cycling, and search query tests
│   ├── test_panel.py             # 3-column dashboard, Treeview table, modals, actions
│   └── test_scheduler.py         # Reminder evaluation, fake clocks, thread lifecycle
└── uv.lock                       # Locked dependency tree
```

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
| **System Tray Integration** | Dropped (Decision D1) | Dropped to maintain pure standard library runtime; floating capsule and native popups provide all controls. |
| **Remote Sync Engine** | Supabase (PostgreSQL / PostgREST) | Off-thread differential sync engine scheduled for Phase 7 using `updated_at > last_synced_at` conflict resolution. |
| **Code Quality & Testing** | `ruff` & `pytest` | Fast linting/formatting (`ruff`, strict 80-char line limit) and automated testing suite (`pytest`). |

# Project Dependencies

Dependencies are declared in [`pyproject.toml`](file:///home/moto/My-Drive/PBL/plus-ultra/pyproject.toml) and pinned in `uv.lock`.

## 1. Active Runtime Dependencies
The application runs entirely on the **Python Standard Library** with zero external network dependencies:
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

## 2. Development Dependencies
Declared in `[dependency-groups].dev`:
- **`pytest >= 9.1.1`**: Automated test framework covering unit tests, edge cases, permission checks, and failure recovery (81 tests across 10 test modules).
- **`ruff >= 0.17.0`**: Fast Python linter and formatter enforcing PEP 8, import order (`I`), simplification (`SIM`), bug prevention (`B`), and strict 80-character line lengths.


## 3. Scheduled Runtime Dependencies (Approved Phased Additions)
- **Phase 7**: Supabase client library (added only upon explicit user approval for cloud sync).