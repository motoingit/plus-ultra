# PLUS-ULTRA 🚀

A user-facing floating desktop assistant for Ubuntu (GNOME on Wayland) engineered as a Problem-Based Learning (PBL) project. PLUS-ULTRA starts with the user's session, displays a compact top-center hovering presence, manages tasks and reminders across customizable categories, and serves as an interactive demonstration of core Operating System (OS) concepts (process lifecycle, mutual exclusion via advisory locks, permissions, signals) and Database Management System (DBMS) concepts (ACID transactions, Write-Ahead Logging, schema evolution, cascading soft deletes, indexed queries).

---

# Project Folder Structure

PLUS-ULTRA enforces a strict 3-layer decoupled architecture (`ui/` -> `services/` -> `repository/`, `db.py`) to isolate presentation from business logic and SQLite persistence:

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
├── pyproject.toml                # Project packaging, CLI script, ruff & pytest
├── README.md                     # Overview, structure, tech stack, and deps
├── src/
│   └── plus_ultra/               # Core application package
│       ├── __init__.py           # Package marker
│       ├── config.py             # XDG base directories, mode 0o700 permissions
│       ├── main.py               # Bootstrap, logging, locks, signal handling
│       ├── settings.py           # Atomic JSON settings engine (mode 0o600)
│       ├── resources/            # Packaged read-only static resources
│       │   ├── default-settings.json # Shipped defaults
│       │   └── metadata.json     # App metadata and versioning
│       ├── desktop.py            # SingleInstanceLock (fcntl.flock), notifications
│       ├── ui/                   # Presentation layer (zero direct DB queries)
│       │   ├── __init__.py       # Package marker
│       │   ├── floating.py       # Dynamic capsule with animated border beam
│       │   ├── theme.py          # Geometry tokens and color palettes
│       │   └── panel.py          # 3-column dashboard window with 6 tabs
│       ├── notifications.py      # Capsule notification queue & width sizing
│       ├── db.py                 # SQLite connection, WAL mode, transactions
│       ├── models.py             # Domain models (Category, Task, Reminder)
│       ├── repository.py         # Parameterized SQL CRUD & soft delete cascades
│       ├── services.py           # Pure business logic (TaskService, CategoryService)
│       ├── scheduler.py          # [Phase 5] Background reminder evaluation
│       └── sync.py               # [Phase 7] Cloud differential sync worker
├── tests/                        # Automated test suites
│   ├── test_config.py            # XDG paths, fallback, permissions, metadata
│   ├── test_settings.py          # Settings validation, atomic write, quarantine
│   ├── test_desktop.py           # Advisory locking and PID tracking
│   ├── test_notifications.py     # Queue management and popup sizing
│   ├── test_ui.py                # Mathematical capsule, beam, popup lifecycle
│   ├── test_db.py                # Migrations, WAL pragma, ACID rollback, checks
│   ├── test_repository.py        # CRUD, soft deletes, due filtering, app state
│   ├── test_services.py          # Business logic, status state machine, search
│   └── test_panel.py             # 3-column dashboard, Treeview, modals, actions
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
- **`pytest >= 9.1.1`**: Automated test framework (70 tests across 9 test modules).
- **`ruff >= 0.17.0`**: Fast Python linter and formatter enforcing PEP 8, import sorting, and strict 80-character line lengths.

## Scheduled Runtime Dependencies (Phased)
- **Phase 5**: `pystray` and `Pillow` (System tray integration).
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
