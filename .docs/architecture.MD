# Project Folder Structure

PLUS-ULTRA adheres to Clean Architecture and Domain-Driven Design principles, organizing code across domain entities, repository contracts, application interfaces, and infrastructure persistence adapters.

```text
plus-ultra/
├── .agents/                      # Agent rules, workflows, and guidelines
├── .docs/                        # Architecture, API specs, features, progress logs
│   ├── api.md                    # Public interfaces and exported module APIs
│   ├── architecture.MD           # Project architecture, tech-stack, and dependencies
│   ├── commands.md               # CLI commands, test flags, manual checklists
│   ├── features.md               # 6-tab workspace specifications & db schema
│   └── progress-log.md           # Chronological phase implementation log
├── .env.sample                   # Sample credentials template
├── .scripts/                     # Standalone maintenance and testing utilities
│   ├── clear_db.py               # Table purging, soft/hard delete, vacuum utility
│   ├── install.py                # Cross-platform interactive TUI installer
│   ├── notify.py                 # Instant/delayed desktop notification testing CLI
│   ├── seed_data.py              # Demo dataset seeding and unseeding engine
│   └── uninstall.py              # Cross-platform interactive TUI uninstaller
├── .tests/                       # Automated test suite (167 passing tests)
│   ├── test_architecture_boundaries.py
│   ├── test_sqlalchemy_persistence.py
│   └── test_unit_of_work.py
├── pyproject.toml                # Project packaging, CLI script, ruff and pytest configs
├── README.md                     # High-level overview, quick start, and layer summary
├── src/
│   └── plus_ultra/               # Core application package
│       ├── application/          # Application layer & use cases
│       │   ├── interfaces/       # Abstract contracts (UnitOfWork, UnitOfWorkFactory)
│       │   │   └── unit_of_work.py
│       │   └── services/         # Application maintenance & data management
│       │       └── maintenance_service.py
│       ├── concurrency/          # Background workers & concurrency (OS concepts)
│       │   ├── __init__.py
│       │   └── scheduler.py      # Background reminder evaluation daemon thread
│       ├── core/                 # Core domain orchestrator, lifecycle, event bus
│       │   ├── application.py    # Main DI container and lifecycle bootstrap
│       │   ├── events.py         # Thread-safe pub/sub event bus
│       │   ├── exceptions.py     # Domain and system exception hierarchy
│       │   └── lifecycle.py      # State machine transitions and shutdown hooks
│       ├── diagnostics/          # Health probes and environmental telemetry
│       │   ├── __init__.py
│       │   └── network.py        # Lightweight socket connectivity monitor
│       ├── domain/               # Enterprise domain entities & repository contracts
│       │   ├── entities/         # Pure Python dataclasses (Task, Category, etc.)
│       │   │   ├── app_state.py
│       │   │   ├── category.py
│       │   │   ├── reminder.py
│       │   │   ├── task.py
│       │   │   └── workspace.py
│       │   ├── repositories/     # Abstract Protocol repository contracts
│       │   │   ├── app_state_repository.py
│       │   │   ├── category_repository.py
│       │   │   ├── reminder_repository.py
│       │   │   ├── task_repository.py
│       │   │   └── workspace_repositories.py
│       │   └── notifications.py  # Capsule notification value objects & queue
│       ├── infrastructure/       # Persistence & external adapters
│       │   └── persistence/      # Database adapters (SQLAlchemy 2.x, MongoDB doc)
│       │       ├── database_config.py      # Database URL, backend & pool config
│       │       ├── database_factory.py     # Pluggable persistence factory
│       │       ├── database_initializer.py # Base.metadata.create_all non-destructive
│       │       ├── mongodb/                # Architectural blueprint for MongoDB
│       │       └── sqlalchemy/             # SQLAlchemy 2.x ORM implementation
│       │           ├── base.py             # DeclarativeBase root
│       │           ├── mappers/            # ORM model <-> domain entity mappers
│       │           ├── models/             # 10 SQLAlchemy ORM table models
│       │           ├── repositories/       # Concrete repository implementations
│       │           ├── session.py          # Engine, events & session factories
│       │           └── unit_of_work.py     # SqlAlchemyUnitOfWork implementation
│       ├── repositories/         # Compatibility facade for repositories
│       ├── database/             # Compatibility facade for connection/session
│       ├── services/             # Pure business logic services (decoupled)
│       │   ├── category_service.py
│       │   ├── code_service.py
│       │   ├── course_service.py
│       │   ├── idea_doubt_service.py
│       │   ├── opportunity_service.py
│       │   ├── quick_link_service.py
│       │   ├── reminder_service.py
│       │   └── task_service.py
│       ├── ui/                   # Modular presentation layer (zero direct SQL)
│       │   ├── components/       # Custom reusable Tkinter widgets
│       │   ├── dialogs/          # Modal data entry dialogs
│       │   ├── views/            # Workspace tab views (Tasks, Code, etc.)
│       │   ├── floating.py       # Floating pill UI presence
│       │   ├── panel.py          # Main dashboard window
│       │   └── theme.py          # Color schemes, typography, spacing
│       ├── utils/                # Cross-cutting utility helpers
│       ├── config.py             # XDG base directories and permissions
│       ├── main.py               # Application bootstrap and argument parsing
│       └── settings.py           # Atomic JSON user preferences engine
└── uv.lock                       # Pinned dependency lockfile
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
