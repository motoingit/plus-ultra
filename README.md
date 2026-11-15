# PLUS-ULTRA

**A Cross-Platform Floating Desktop Assistant**

PLUS-ULTRA is a desktop assistant built as a Problem-Based Learning (PBL) project. It provides a compact floating interface for managing tasks, reminders, and customizable categories.

The application is designed for **Windows 11 and Ubuntu Linux**, with a shared application core and separate platform-specific implementations.

The architecture aims to keep application logic independent of operating-system details, allowing platform features such as system tray integration, notifications, process management, and startup behavior to be handled through dedicated interfaces.

---

# Tech Stack

The following table describes the technologies currently used by the project.

| Component | Technology | Purpose |
|---|---|---|
| Package & Environment Manager | `uv` | Dependency management, virtual environments, and execution |
| Programming Language | CPython 3.12+ | Main application runtime |
| GUI Toolkit | `tkinter` and `tkinter.ttk` | Floating desktop interface and application windows |
| Database | SQLite (`sqlite3`) | Persistent storage using parameterized SQL |
| Database Access | Raw SQL | Database operations without an ORM |
| User Configuration | Custom JSON engine | Persistent user preferences and configuration |
| System Tray | `pystray` | System tray icon, menus, and interactions |
| Image Processing | Pillow | Loading and preparing tray icon images |
| Platform Integration | Python platform adapters | OS-specific system functionality |
| Linux Process Locking | `fcntl.flock` | Single-instance enforcement on Linux |
| Logging | Python `logging` | Application and diagnostic logs |
| Testing | `pytest` | Automated testing |
| Code Quality | Ruff | Python linting and formatting |
| Packaging | PyInstaller | Freezing the Python application into distributable executables |

## Application Architecture

PLUS-ULTRA follows a shared-core, platform-specific-adapter architecture.

The application uses common interfaces to communicate with operating-system features rather than directly depending on platform-specific implementations.

```text
PLUS-ULTRA
│
├── Application Core
│   ├── Business Logic
│   ├── Task Management
│   ├── Reminder Management
│   ├── Database Operations
│   └── User Interface (Tkinter)
│
└── Platform Services
    │
    ├── Common Interfaces
    │   ├── System Tray
    │   ├── Notifications
    │   ├── Process Management
    │   ├── Startup Management
    │   ├── Window Management
    │   └── Application Paths
    │
    ├── Linux Implementation
    │   ├── Linux System Tray
    │   ├── Linux Notifications
    │   ├── Linux Process Lock
    │   └── Linux Startup Integration
    │
    └── Windows Implementation
        ├── Windows System Tray
        ├── Windows Notifications
        ├── Windows Process Lock
        └── Windows Startup Integration
```

The platform factory selects the appropriate implementation at runtime.

**Platform support:**
- Windows: Platform implementation available.
- Linux: Platform implementation available.
- macOS: Platform detection exists, but native application support is not currently implemented.

---

# Project Dependencies

Dependencies are declared in `pyproject.toml` and resolved through `uv.lock`.

## Runtime Dependencies

### Third-party packages

The application uses the following third-party runtime dependencies:

| Package | Purpose |
|---|---|
| `pystray` | System tray icon and interaction management |
| `Pillow` | Image loading, processing, and resizing for tray icons |

These packages are used together: Pillow prepares the icon image, while pystray manages its presentation and interactions with the desktop environment.

### Python Standard Library

The application also relies on Python's standard library for its core functionality.

| Module | Purpose |
|---|---|
| `argparse` | Command-line argument parsing |
| `contextlib` | Resource and context management |
| `dataclasses` | Structured application entities |
| `datetime` | Date and time handling |
| `fcntl` | Linux file locking |
| `importlib.metadata` | Installed package metadata |
| `importlib.resources` | Accessing packaged resources |
| `json` | Configuration serialization |
| `logging` | Application logging |
| `os` and `stat` | Filesystem operations and permissions |
| `pathlib` | Filesystem path management |
| `queue` | Thread-safe communication |
| `signal` | Process signal handling |
| `sqlite3` | Database operations |
| `subprocess` | External process invocation |
| `threading` | Background execution |
| `tkinter` | Desktop GUI rendering |

**Important:** Platform-specific modules are not necessarily used on every operating system. For example, `fcntl` is used for Linux process locking and is not a cross-platform Windows API.

## Development Dependencies

| Package | Purpose |
|---|---|
| `pytest` | Automated testing |
| `ruff` | Linting and code formatting |

---

# Database and Configuration

## SQLite

PLUS-ULTRA uses SQLite through Python's built-in `sqlite3` module.

- Direct SQL queries; no ORM.
- Parameterized SQL statements.
- Foreign-key enforcement.
- WAL journal mode.
- Transaction-based database operations.
- Persistent application data.

## Application State

Machine-specific application state is stored separately from user preferences.

Examples include:
- Floating widget position.
- Window coordinates.
- Other machine-specific state.

## User Settings

A custom JSON configuration engine handles user preferences.

Its responsibilities include:
- Atomic configuration file replacement using `os.replace`.
- Restrictive file permissions where supported.
- Configuration validation.
- Handling and quarantining corrupted configuration files.

---

# System Integration

## System Tray

The application uses `pystray` and Pillow for system tray functionality.

- Tray icon creation and display.
- Context menu integration.
- Tray interactions.
- Platform-specific tray implementations.

**Linux note:** System tray availability depends on the desktop environment and its indicator support. GNOME on Wayland may require a compatible AppIndicator extension and supporting system libraries. Installing Python dependencies alone does not guarantee that an indicator will appear.

## Desktop Notifications

Notifications are implemented through platform-specific services.

- Linux: Desktop notification integration using `notify-send`.
- Windows: Windows-specific notification implementation.

## Process Management

The application uses platform-specific process management implementations to support single-instance execution and clean shutdown behavior.

Linux uses `fcntl.flock` for advisory file locking.

---

# Packaging and Installation

The project includes a PyInstaller specification for freezing the Python application.

**Packaging and installation are separate concerns:**

- PyInstaller creates a frozen application executable.
- Platform-specific installation scripts handle application installation and removal.
- Windows and Linux require their respective installation mechanisms.

The PyInstaller specification alone does not create a conventional Windows setup wizard or a Linux `.deb` package.

---

# Quick Start

## Prerequisites

- Python 3.12+
- `uv`
- Git
- Required operating-system GUI and tray integration support

## Install Dependencies

```bash
uv sync
```

## Run the Application

```bash
uv run plus-ultra
```

## Run Tests

```bash
uv run pytest -v
```

## Run a Smoke Test

```bash
uv run plus-ultra --smoke-test
```

The smoke test validates essential application components and exits automatically.

## Installation

### Linux

```bash
./.scripts/install.sh
```

Alternatively:

```bash
./.scripts/linux/install.sh
```

### Windows

```powershell
powershell .scripts/install.ps1
```

Alternatively:

```powershell
powershell .scripts/windows/install.ps1
```

## Uninstallation

### Linux

```bash
./.scripts/uninstall.sh
```

### Windows

```powershell
powershell .scripts/uninstall.ps1
```

---

# Development Utilities

## Seed Demo Data

```bash
uv run python .scripts/seed_data.py --seed
```

## Remove Demo Data

```bash
uv run python .scripts/seed_data.py --unseed
```

## Clear Database

```bash
uv run python .scripts/clear_db.py --all --force
```

## Test Desktop Notifications

```bash
uv run python .scripts/notify.py
```

## Test Delayed Notifications

```bash
uv run python .scripts/notify.py 2
```

Or specify seconds:

```bash
uv run python .scripts/notify.py -s 10
```

---

# Future Development

The following items are planned rather than current runtime requirements.

| Phase | Planned Feature | Status |
|---|---|---|
| Phase 7 | Supabase-based incremental cloud synchronization | Planned |
| Future | Native macOS platform implementation | Not implemented |

Future platform support should follow the existing adapter architecture instead of introducing operating-system-specific logic into the application core.

---

# Project Philosophy

PLUS-ULTRA follows these architectural principles:

1. **Separation of Concerns:** Keep business logic independent of platform-specific functionality.
2. **Cross-Platform Design:** Share application logic while maintaining separate OS implementations.
3. **Maintainability:** Prefer reusable interfaces and modular components.
4. **Data Integrity:** Use transactional database operations and validated configuration.
5. **Reliability:** Implement proper error handling, logging, and graceful shutdown.
6. **Extensibility:** Make it possible to introduce additional platform implementations without rewriting the application core.

**Project Goal:** Build a maintainable, reliable, and extensible desktop assistant while demonstrating practical concepts from Operating Systems, Database Management Systems, and Software Engineering.
