# Project Folder Structure

PLUS-ULTRA adheres to a strict 3-layer decoupled architecture (`ui/` -> `services/` -> `repositories/`, `database/`) to isolate presentation from business logic and SQLite persistence.

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
├── .scripts/                      # Standalone maintenance and testing utilities
│   ├── __init__.py               # Scripts package marker
│   ├── clear_db.py               # Table purging, soft/hard delete, vacuum utility
│   ├── notify.py                 # Instant/delayed desktop notification testing CLI
│   ├── seed_data.py              # Demo dataset seeding and unseeding engine
│   └── seeds.py                  # Legacy wrapper delegating to seed_data.py
├── pyproject.toml                # Project packaging, CLI script, ruff and pytest configs
├── README.md                     # High-level overview, quick start, and layer summary
├── src/
│   └── plus_ultra/               # Core application package
│       ├── __init__.py           # Package marker
│       ├── config.py             # XDG Base Directory resolution, secure 0o700 permissions
│       ├── main.py               # Process bootstrap, dual logging, argument parsing
│       ├── settings.py           # Atomic JSON settings engine, strict type safety, recovery
│       ├── resources/            # Packaged static assets
│       │   ├── data/             # Packaged metadata and default configurations
│       │   │   ├── default-settings.json # Shipped defaults & configurable dimensions
│       │   │   └── metadata.json # App metadata
│       │   └── icons/            # Packaged raster/vector iconography
│       │       ├── fallback.png  # High-resolution master icon asset
│       │       └── fallback.svg  # Master vector artwork
│       ├── datetime_utils.py     # Timezone-aware datetime parsing for reminders
│       ├── desktop.py            # Single-instance lock (fcntl.flock), notifications
│       ├── network.py            # Thread-safe connectivity probe & status monitor
│       ├── notifications.py      # Capsule notification queue & width sizing
│       ├── models.py             # Strongly typed data models
│       ├── scheduler.py          # Background reminder evaluation thread
│       ├── sync.py               # [Phase 7] Differential online synchronization worker
│       ├── database/             # SQLite connection, schema, migrations
│       │   ├── __init__.py       # Package marker & public re-exports
│       │   ├── connection.py     # Connection factory, WAL pragma, transaction CM
│       │   ├── schema.py         # Schema v1 & v2 SQL statements
│       │   └── migrations.py     # Schema version discovery & runner
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
│           ├── icons.py          # Pure Tkinter PhotoImage caching & scaling
│           ├── theme.py          # Design tokens, color palettes, fonts
│           ├── geometry.py       # Mathematical capsule perimeter generator
│           ├── floating.py       # Dynamic capsule widget with auto-expansion & net dot
│           ├── panel.py          # Dashboard coordinator window with PanedWindow
│           ├── components/       # Reusable UI widgets
│           │   ├── __init__.py
│           │   ├── datetime_picker.py # Interactive DateTimePicker with Now & presets
│           │   ├── popup_pill.py # Transient 3s notification popup capsule pill
│           │   ├── scrollable.py # Scrollable canvas frame
│           │   ├── sidebar.py    # Draggable tab navigation bar with 80px settings icon
│           │   ├── task_card.py  # Decoupled task card component with action handlers
│           │   └── notifications_panel.py # Right drawer (Alerts stream)
│           ├── dialogs/          # Modal forms with generous dimensions
│           │   ├── __init__.py
│           │   ├── base.py       # Modal centering utility
│           │   ├── task_dialog.py # Interactive DateTimePicker & inline categories
│           │   ├── code_dialog.py # Predefined language dropdown
│           │   ├── course_dialog.py # Cleaned course platform options
│           │   ├── idea_dialog.py
│           │   ├── opportunity_dialog.py # Reusable DateTimePicker deadline
│           │   ├── quick_link_dialog.py
│           │   └── category_dialog.py
│           └── views/            # Specialized tab content views (2x cards)
│               ├── __init__.py
│               ├── tasks_view.py # Tasks view with rich logging & CRUD
│               ├── code_view.py  # Code c-p workspace
│               ├── dsa_view.py   # Dedicated DSA Problem Tracker view
│               ├── courses_view.py # Courses view (University, YouTube, Other)
│               ├── ideas_view.py # PS/I dual subtabs (Ideas & Doubts)
│               ├── opportunities_view.py
│               ├── quick_links_view.py
│               └── settings_view.py # Preferences & network monitor toggle
├── .tests/                       # Comprehensive test suite (103 tests, 100% pass)
│   ├── test_config.py            # XDG paths, fallback logic, mode 0o700, logging tests
│   ├── test_datetime_utils.py    # Timezone-aware, ISO, and space-separated date parsing
│   ├── test_refinements.py       # DateTimePicker, PS/I subtabs, popup pill, task card
│   ├── test_scripts.py           # Database clearing, seed/unseed, notify CLI tests
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