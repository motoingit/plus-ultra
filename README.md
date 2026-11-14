# PLUS-ULTRA 🚀

A user-facing floating desktop assistant for Ubuntu (GNOME on Wayland) engineered as a Problem-Based Learning (PBL) project. PLUS-ULTRA starts with the user's session, displays a compact top-center hovering presence, manages tasks and reminders across customizable categories, and serves as an interactive demonstration of core Operating System (OS) concepts (process lifecycle, mutual exclusion via advisory locks, permissions, signals) and Database Management System (DBMS) concepts (ACID transactions, Write-Ahead Logging, schema evolution, cascading soft deletes, indexed queries).

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
- **`pytest >= 9.1.1`**: Automated test framework (145 tests across 18 test suites).
- **`ruff >= 0.17.0`**: Fast Python linter and formatter enforcing PEP 8, import sorting, and strict 80-character line lengths.


## Scheduled Runtime Dependencies (Phased)
- **Phase 5**: Decision D1 resolved to drop external tray libraries (`pystray`/`Pillow`) to maintain a 100% pure Python standard library stack with zero C-binding dependencies.
- **Phase 7**: Supabase client library (Incremental cloud sync).

---

## Quick Start

```bash
# Interactive TUI Installer (Linux & Windows 11)
uv run python .scripts/install.py
# Or use the platform-specific scripts:
./.scripts/install.sh            # Linux (or ./.scripts/linux/install.sh)
powershell .scripts/install.ps1  # Windows 11 (or .\.scripts\windows\install.ps1)

# Interactive TUI Uninstaller (Remove app & optional data purge)
uv run python .scripts/uninstall.py
# Or use the platform-specific uninstaller:
./.scripts/uninstall.sh            # Linux (or ./.scripts/linux/uninstall.sh)
powershell .scripts/uninstall.ps1  # Windows 11 (or .\.scripts\windows\uninstall.ps1)

# Sync environment dependencies
uv sync

# Run the test suite
uv run pytest -v

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

# Test delayed desktop notification after 2 minutes (or -s for seconds)
uv run python .scripts/notify.py 2
uv run python .scripts/notify.py -s 10
```
