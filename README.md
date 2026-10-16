# PLUS-ULTRA 🚀

A user-facing floating desktop assistant for Ubuntu (GNOME on Wayland) engineered as a Problem-Based Learning (PBL) project. PLUS-ULTRA starts with the user's session, displays a compact top-center hovering presence, manages tasks and reminders across customizable categories, and serves as an interactive demonstration of core Operating System (OS) concepts (process lifecycle, mutual exclusion via advisory locks, permissions, signals) and Database Management System (DBMS) concepts (ACID transactions, Write-Ahead Logging, schema evolution, cascading soft deletes, indexed queries).

---

# Project Folder Structure

PLUS-ULTRA enforces a strict 3-layer decoupled architecture (`ui/` -> `services/` -> `repositories/`, `database/`) to isolate presentation from business logic and SQLite persistence:

```text
plus-ultra/
├── .agents/                      # AI rules, agent workflows, and guidelines
├── .docs/                        # Architecture, API specs, features, and logs
│   ├── api.md                    # Public interfaces and module specifications
│   ├── architecture.MD           # Project architecture, tech-stack, and deps
│   ├── commands.md               # CLI commands, test flags, manual checklists
│   ├── features.md               # 6-tab workspace & sub-section specs
│   └── progress-log.md           # Chronological development log
├── .env.sample                   # Sample secrets template (Supabase public key)
├── .scripts/                      # Standalone maintenance and seed utilities
│   ├── __init__.py               # Scripts package marker
│   └── seeds.py                  # Demo seed dataset & standalone CLI
├── pyproject.toml                # Project packaging, CLI script, ruff & pytest
├── README.md                     # Overview, structure, tech stack, and deps
├── src/
│   └── plus_ultra/               # Core application package
│       ├── __init__.py           # Package marker
│       ├── config.py             # XDG base directories, mode 0o700 permissions
│       ├── main.py               # Bootstrap, logging, locks, signal handling
│       ├── settings.py           # Atomic JSON settings engine (mode 0o600)
│       ├── resources/            # Packaged static assets
│       │   ├── data/             # Packaged metadata and default configurations
│       │   │   ├── default-settings.json # Shipped defaults
│       │   │   └── metadata.json # App metadata and versioning
│       │   └── icons/            # Packaged raster/vector iconography
│       │       ├── fallback.png  # Master raster icon asset
│       │       └── fallback.svg  # Master vector artwork
│       ├── desktop.py            # SingleInstanceLock (fcntl.flock), notifications
│       ├── network.py            # Thread-safe connectivity probe & status monitor
│       ├── notifications.py      # Capsule notification queue & width sizing
│       ├── models.py             # Strongly typed domain entities
│       ├── scheduler.py          # Background reminder evaluation thread
│       ├── sync.py               # [Phase 7] Cloud differential sync worker
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
│           ├── floating.py       # Dynamic capsule widget with auto-expansion
│           ├── panel.py          # Dashboard coordinator window with PanedWindow
│           ├── components/       # Reusable UI widgets
│           │   ├── __init__.py
│           │   ├── datetime_picker.py # Interactive DateTimePicker with Now & presets
│           │   ├── scrollable.py # Scrollable canvas frame
│           │   ├── sidebar.py    # Draggable tab navigation bar with 80px settings icon
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
│               ├── tasks_view.py # Tasks view with rich debug logging
│               ├── code_view.py  # Code c-p workspace
│               ├── dsa_view.py   # Dedicated DSA Problem Tracker view
│               ├── courses_view.py # Courses view (University, YouTube, Other)
│               ├── ideas_view.py # PS/I dual subtabs (Ideas & Doubts)
│               ├── opportunities_view.py
│               ├── quick_links_view.py
│               └── settings_view.py # Preferences & network monitor toggle
├── .tests/                       # Automated test suites (95 tests, 100% pass)
│   ├── test_config.py            # XDG paths, fallback, permissions, metadata
│   ├── test_datetime_utils.py    # Timezone-aware date parsing and formatting
│   ├── test_refinements.py       # DateTimePicker, PS/I subtabs, dynamic capsule
│   ├── test_settings.py          # Settings validation, atomic write, quarantine
│   ├── test_desktop.py           # Advisory locking, notify-send, PID tracking
│   ├── test_notifications.py     # Queue management and popup sizing
│   ├── test_ui.py                # Mathematical capsule, beam, popup lifecycle
│   ├── test_db.py                # Migrations, WAL pragma, ACID rollback, checks
│   ├── test_repository.py        # CRUD, soft deletes, due filtering, app state
│   ├── test_services.py          # Business logic, status state machine, search
│   ├── test_panel.py             # 3-column dashboard, Treeview, modals, actions
│   └── test_scheduler.py         # Reminder evaluation, fake clocks, thread lifecycle
└── uv.lock                       # Pinned dependency lockfile
```

---

# Project Tech-Stack

The technology choices are locked and adhere to Problem-Based Learning objectives:

| Component | Technology | Rationale & Concept |
|---|---|---|
| **Host Platform** | Ubuntu Linux (GNOME on Wayland) | Target OS. Tkinter runs via XWayland. |
| **Language Runtime** | CPython 3.12+ | Managed via `uv`. Modern typing, pattern matching. |
| **Package & Env Manager** | `uv` | High-performance virtualenv and dependency locking. |
| **GUI Toolkit** | `tkinter` & `tkinter.ttk` | Standard library GUI toolkit. Kept strictly on UI thread. |
| **Database Engine** | `sqlite3` (Standard Library) | Raw parameterized SQL only (no ORM). WAL mode, foreign keys (`PRAGMA foreign_keys = ON`), ACID transactions. |
| **Machine State Persistence** | SQLite `app_state` table | Dedicated key-value store for machine state (`widget_x`, `widget_y`). Kept separate from user preferences. |
| **User Settings Engine** | Custom JSON Engine | Atomic file replacement (`os.replace`, `0o600`), strict type safety, automatic quarantine of corrupt files. |
| **Process Management** | `fcntl.flock` (Standard Library) | Single-instance mutual exclusion via POSIX advisory file locking. |
| **Desktop Notifications** | `notify-send` via `subprocess` | Desktop notification dispatch without heavyweight dependencies. |
| **Code Quality & Testing** | `ruff` & `pytest` | Fast linting/formatting (strict 80-char line limit) and automated test suite. |

---

# Project Dependencies

All dependencies are defined in `pyproject.toml` and pinned in `uv.lock`.

## Runtime Dependencies
The core application currently relies entirely on the **Python Standard Library** with zero third-party packages:
- `argparse`: Command-line interface argument parsing.
- `contextlib`: Resource management and exception suppression.
- `dataclasses`: Strongly typed domain entities (`Category`, `Task`, `Reminder`, `AppState`).
- `datetime`: ISO-8601 UTC timestamp generation (`datetime.UTC`).
- `fcntl`: POSIX file locking (`flock`) for single-instance enforcement.
- `importlib.metadata` & `importlib.resources`: Version discovery and packaged resource access.
- `json`: User preference serialization and metadata decoding.
- `logging`: Dual logging (console stdout and persistent `launcher.log`).
- `os` & `stat`: Filesystem permissions (`0o700`, `0o600`) and atomic replace (`os.replace`).
- `pathlib`: Object-oriented path resolution per XDG standards.
- `queue`: Thread-safe cross-thread messaging.
- `signal`: POSIX signal trapping (`SIGINT`, `SIGTERM`) for clean shutdown.
- `sqlite3`: Direct ACID transactional database management and migrations.
- `subprocess`: Safe argument-list invocation of `notify-send`.
- `threading`: Background task execution (scheduler, sync).
- `tkinter`: Native desktop GUI rendering and event dispatch.

## Development Dependencies
- **`pytest >= 9.1.1`**: Automated test framework (81 tests across 10 test modules).
- **`ruff >= 0.17.0`**: Fast Python linter and formatter enforcing PEP 8, import sorting, and strict 80-character line lengths.


## Scheduled Runtime Dependencies (Phased)
- **Phase 5**: Decision D1 resolved to drop external tray libraries (`pystray`/`Pillow`) to maintain a 100% pure Python standard library stack with zero C-binding dependencies.
- **Phase 7**: Supabase client library (Incremental cloud sync).

---

## Quick Start

```bash
# Sync environment dependencies
uv sync

# Run the test suite
uv run pytest -v

# Launch the floating desktop assistant
uv run plus-ultra

# Run transient smoke test (validates GUI, DB, and lock, then exits cleanly in 500ms)
uv run plus-ultra --smoke-test
```
