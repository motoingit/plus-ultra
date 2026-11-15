# PLUS-ULTRA

A user-facing floating desktop assistant for Ubuntu (GNOME on Wayland) engineered as a Problem-Based Learning (PBL) project. PLUS-ULTRA starts with the user's session, displays a compact top-center hovering presence, manages tasks and reminders across customizable categories, and serves as an interactive demonstration of core Operating System (OS) concepts (process lifecycle, mutual exclusion via advisory locks, permissions, signals) and Database Management System (DBMS) concepts (clean architecture, repository pattern, unit of work, ACID transactions, Write-Ahead Logging, non-destructive schema initialization, cascading soft deletes, and indexed queries).

# Project Folder Structure

```text
plus-ultra/
├── .agents/                      # Agent rules, guidelines, and instructions
├── .docs/                        # Architecture, API specs, commands, and logs
│   ├── api.md                    # Public API and interface specifications
│   ├── architecture.MD           # Architecture, Tech-Stack, and Dependencies
│   ├── commands.md               # CLI commands, testing flags, and checklists
│   ├── features.md               # 6-tab workspace specifications & db schema
│   └── progress-log.md           # Chronological phase implementation log
├── .scripts/                     # Standalone maintenance and tooling utilities
│   ├── clear_db.py               # Table purging, soft/hard delete, vacuum utility
│   ├── install.py                # Cross-platform interactive TUI installer
│   ├── notify.py                 # Desktop notification testing CLI
│   ├── seed_data.py              # Demo dataset seeding and unseeding engine
│   └── uninstall.py              # Interactive TUI uninstaller
├── .tests/                       # Test suite (167 tests across 21 test suites)
│   ├── test_architecture_boundaries.py
│   ├── test_sqlalchemy_persistence.py
│   └── test_unit_of_work.py
├── pyproject.toml                # Project metadata, dependencies, and tool configs
├── README.md                     # High-level overview, architecture, and quick start
├── src/
│   └── plus_ultra/               # Core application package
│       ├── application/          # Application layer & use cases
│       │   ├── interfaces/       # Abstract interfaces (Unit of Work)
│       │   └── services/         # Application maintenance & data services
│       ├── concurrency/          # Concurrency & background workers (OS concepts)
│       ├── core/                 # Core DI container, lifecycle, event bus
│       ├── diagnostics/          # Health probes and network monitor
│       ├── domain/               # Enterprise domain entities & repository contracts
│       │   ├── entities/         # Pure Python dataclasses (Task, Category, etc.)
│       │   ├── repositories/     # Abstract Protocol repository contracts
│       │   └── notifications.py  # Capsule notification value objects & queue
│       ├── infrastructure/       # Persistence & external adapters
│       │   └── persistence/      # Database adapters (SQLAlchemy 2.x, MongoDB doc)
│       │       ├── database_config.py      # Centralized database configuration
│       │       ├── database_factory.py     # Pluggable persistence factory
│       │       ├── database_initializer.py # Non-destructive Base.metadata.create_all
│       │       ├── mongodb/                # Future MongoDB adapter documentation
│       │       └── sqlalchemy/             # SQLAlchemy 2.x ORM implementation
│       │           ├── base.py             # DeclarativeBase root
│       │           ├── mappers/            # ORM model <-> domain entity mappers
│       │           ├── models/             # 10 SQLAlchemy ORM table models
│       │           ├── repositories/       # Concrete repository implementations
│       │           ├── session.py          # Engine, events & session factories
│       │           └── unit_of_work.py     # SqlAlchemyUnitOfWork implementation
│       ├── services/             # Domain business logic services (decoupled)
│       ├── repositories/         # Compatibility facade for concrete repositories
│       ├── database/             # Compatibility facade for session and engine
│       ├── ui/                   # Modular presentation layer (Tkinter / XWayland)
│       └── main.py               # Application bootstrap and argument parsing
└── uv.lock                       # Deterministic dependency lockfile
```

# Project Tech-Stack

The technology choices are locked and adhere to Problem-Based Learning objectives:

| Component | Technology | Rationale & Concept |
|---|---|---|
| **Host Platform** | Ubuntu Linux (GNOME on Wayland) | Target OS. Tkinter runs via XWayland. |
| **Language Runtime** | CPython 3.12+ | Managed via `uv`. Modern typing, pattern matching. |
| **Package & Env Manager** | `uv` | High-performance virtualenv and dependency locking. |
| **GUI Toolkit** | `tkinter` & `tkinter.ttk` | Standard library GUI toolkit. Kept strictly on UI thread. |
| **Persistence Engine** | `SQLAlchemy >= 2.0.0` | Database-agnostic persistence layer (ORM / Core), Repository Pattern, and Unit of Work. |
| **Default Storage Engine** | SQLite 3 (via SQLAlchemy) | Default file and in-memory engine. WAL mode, foreign keys (`PRAGMA foreign_keys = ON`), 5s busy timeout via connection events. |
| **Schema Initialization** | Non-destructive `create_all` | No Alembic migration tables (`alembic_version` forbidden). Schema initializes non-destructively. |
| **Machine State** | `app_state` table | Dedicated key-value store for machine state (`widget_x`, `widget_y`). Kept separate from user preferences. |
| **User Settings Engine** | Custom JSON Engine | Atomic file replacement (`os.replace`, `0o600`), strict type safety, automatic quarantine of corrupt files. |
| **Process Management** | `fcntl.flock` (Standard Library) | Single-instance mutual exclusion via POSIX advisory file locking. |
| **Desktop Notifications** | `notify-send` via `subprocess` | Desktop notification dispatch without heavyweight dependencies. |
| **Code Quality & Testing** | `ruff` & `pytest` | Fast linting/formatting (strict 80-char line limit) and automated test suite. |

---

# Project Dependencies

All dependencies are defined in `pyproject.toml` and pinned in `uv.lock`.

## Runtime Dependencies
- **`sqlalchemy >= 2.0.0`**: Modern SQLAlchemy 2.x persistence engine providing ORM mapping, statement compilation, and connection pool management.
- **Python Standard Library**:
  - `argparse`: Command-line interface argument parsing.
  - `contextlib`: Resource management and exception suppression.
  - `dataclasses`: Pure domain entities (`Category`, `Task`, `Reminder`, `AppState`, workspace models).
  - `datetime`: ISO-8601 UTC timestamp generation (`datetime.UTC`).
  - `fcntl`: POSIX file locking (`flock`) for single-instance enforcement.
  - `importlib.metadata` & `importlib.resources`: Version discovery and packaged resource access.
  - `json`: User preference serialization and metadata decoding.
  - `logging`: Dual logging (console stdout and persistent `launcher.log`).
  - `os` & `stat`: Filesystem permissions (`0o700`, `0o600`) and atomic replace (`os.replace`).
  - `pathlib`: Object-oriented path resolution per XDG standards.
  - `queue`: Thread-safe cross-thread messaging.
  - `signal`: POSIX signal trapping (`SIGINT`, `SIGTERM`) for clean shutdown.
  - `sqlite3`: Standard library SQLite DBAPI driver used by SQLAlchemy SQLite dialect.
  - `subprocess`: Safe argument-list invocation of `notify-send`.
  - `threading`: Background task execution (scheduler, network monitor).
  - `tkinter`: Native desktop GUI rendering and event dispatch.

## Development Dependencies
- **`pytest >= 9.1.1`**: Automated test framework (167 tests across 21 test suites).
- **`ruff >= 0.17.0`**: Fast Python linter and formatter enforcing PEP 8, import sorting, and strict 80-character line lengths.

---

## Quick Start

```bash
# Sync environment dependencies
uv sync

# Run the test suite
uv run pytest -v

# Run linting and format verification
uv run ruff check .
uv run ruff format --check .

# Launch the floating desktop assistant
uv run plus-ultra

# Run transient smoke test (validates GUI, DB, and lock, then exits cleanly in 500ms)
uv run plus-ultra --smoke-test

# Seed demo dataset across all 6 workspace tabs
uv run python .scripts/seed_data.py --seed

# Unseed demo records cleanly
uv run python .scripts/seed_data.py --unseed

# Clear database tables (with safety confirmation or --force)
uv run python .scripts/clear_db.py --all --force

# Test instant desktop notification
uv run python .scripts/notify.py
```
