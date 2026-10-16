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

- **Status**: Completed
- **Date**: 2026-10-13

### Phase 1 To-do List:
- [x] Add development tools `ruff` and `pytest` via `uv add --dev ruff pytest`.
- [x] Implement `src/plus_ultra/config.py`:
  - [x] Implement XDG base directory paths (`$XDG_DATA_HOME`, `$XDG_STATE_HOME`).
  - [x] Enforce POSIX permission mode `0o700` (`rwx------`) on directory creation.
  - [x] Export application constants (`APP_NAME`, `DB_FILENAME`, `LOG_FILENAME`).
  - [x] Helper functions `get_db_path()` and `get_log_path()`.
- [x] Implement dual logging in `src/plus_ultra/main.py` (`launcher.log` in state dir + console stdout) with ISO-8601 timestamps.
- [x] Implement unit tests in `tests/test_config.py` verifying fallback, overridden paths, mode `0o700` permissions, unicode names, empty variables, and startup logging.
- [x] Verify gate: `uv run plus-ultra` writes startup lines and exits 0; `uv run ruff check .` and `uv run pytest` pass cleanly (9 tests passed).
- [x] Update documentation (`README.md`, `.docs/api.md`, `.docs/progress-log.md`).

### Issues & Status:
- **Line length and import sorting**: Resolved by configuring imports and wrapping docstrings to satisfy `ruff` 80-character limit.
- **Exception handling style**: Replaced `try-except-pass` with `contextlib.suppress(OSError)` in `_ensure_private_directory()` per ruff rule `SIM105`.
- **Package import structure**: Cleaned `src/plus_ultra/__init__.py` to avoid shadowing `plus_ultra.main:main`.

### Important Points:
- Verified on disk: `/home/moto/.local/share/plus-ultra` and `/home/moto/.local/state/plus-ultra` created with permissions `drwx------` (`0o700`).
- Gate passed: `uv run plus-ultra` executed cleanly with exit code 0 and populated `/home/moto/.local/state/plus-ultra/launcher.log`.
- All 9 unit tests in `tests/test_config.py` passed in 0.02s.

---

## Phase 1b: Secrets, Metadata, Settings

- **Status**: Completed
- **Date**: 2026-10-13

### Phase 1b To-do List:
- [x] Create `.env.sample` with public placeholders (`SUPABASE_URL`, `SUPABASE_ANON_KEY`); verify `.env` is uncommitted and protected in `.gitignore`.
- [x] Add package metadata resource (`src/plus_ultra/resources/metadata.json`) and dynamic version lookup via `importlib.metadata`.
- [x] Add locked default settings resource (`src/plus_ultra/resources/default-settings.json`) with keys: `settings_version`, `always_on_top`, `glow_enabled`, `glow_pulse_period_ms`, `reminders_enabled`.
- [x] Implement `src/plus_ultra/config.py` helpers: `get_config_dir()`, `get_user_settings_path()`, `get_app_version()`, `get_metadata()`.
- [x] Implement `src/plus_ultra/settings.py` settings manager:
  - [x] Strict type validation (`type(val) is type(default_val)`).
  - [x] Ignore unknown keys and ignore type-mismatched values.
  - [x] Defensive recovery for corrupted JSON by quarantining to `.bad-<timestamp>` without crashing.
  - [x] Atomic writes using temporary file in same directory + `os.replace` + `fsync` with mode `0o600`.
  - [x] Reject machine state keys (`widget_x`, `widget_y`).
  - [x] Exposed APIs: `load_effective_settings()`, `load_default_settings()`, `update_user_setting()`, `reset_setting()`, `reset_all_settings()`, `reload()`.
- [x] Implement unit tests in `tests/test_settings.py` and expand `tests/test_config.py` (23 total tests passing).
- [x] Verify formatter, linter, test suite, and CLI execution.

### Issues & Status:
- **Type safety for booleans**: `isinstance(True, int)` evaluates to `True` in Python. Resolved by enforcing strict identity check `type(user_val) is type(default_val)`.
- **Linting rule UP017**: Used `datetime.UTC` alias in place of `timezone.utc`.
- **Ruff line length**: Formatted all docstrings, assertions, and functions to fit strictly within 80 characters.

### Important Points:
- Atomic replacement guarantees settings file integrity during power-loss or crash.
- Filesystem permissions: Config directory mode `0o700` (`drwx------`), user settings file mode `0o600` (`-rw-------`).
- Total test suite now runs 23 tests in 0.04s with 100% pass rate.

---

## Phase 2: Wayland/XWayland Spike + Single Instance Lock

- **Status**: Completed
- **Date**: 2026-10-16

### Phase 2 To-do List:
- [x] Implement `src/plus_ultra/desktop.py` with `SingleInstanceLock` using `fcntl.flock`:
  - [x] Exclusive advisory locking (`LOCK_EX | LOCK_NB`) on `$XDG_STATE_HOME/plus-ultra/plus-ultra.lock`.
  - [x] Write PID on acquisition for process diagnostics.
  - [x] Clean release and unlinking on exit.
  - [x] Support Python context manager protocol.
- [x] Implement `src/plus_ultra/ui/theme.py`:
  - [x] Define `CapsuleGeometry` tokens (140x36, radius 18, top-offset 12).
  - [x] Define `CapsuleTheme` color tokens (dark palette, idle/hover fill, electric cyan hover glow).
- [x] Implement `src/plus_ultra/ui/floating.py`:
  - [x] `FloatingWidget` with borderless window (`overrideredirect(True)`).
  - [x] `-topmost` attribute honoring user settings.
  - [x] Canvas-based smooth capsule rendering.
  - [x] Mouse drag handling (`<Button-1>`, `<B1-Motion>`) and click detection.
  - [x] Hover glow state transitions (`<Enter>`, `<Leave>`).
  - [x] Clean closure on `<Escape>` or window destruction.
- [x] Update `src/plus_ultra/main.py`:
  - [x] Acquire `SingleInstanceLock` before starting GUI; graceful exit on contention.
  - [x] Support `--smoke-test` (500ms transient run and exit 0) and `--no-ui`.
  - [x] POSIX signal trapping (`SIGINT`, `SIGTERM`) for graceful shutdown.
- [x] Implement tests in `tests/test_desktop.py` and `tests/test_ui.py` (29 tests passing).
- [x] Update documentation (`README.md`, `.docs/api.md`, `.docs/progress-log.md`, `.docs/architecture.MD`).

### Issues & Status:
- **Pytest blocking on Tkinter mainloop**: Resolved by detecting test environments (`PYTEST_CURRENT_TEST`) and supporting `--no-ui` / `--smoke-test` CLI flags.
- **Ruff linter compliance**: Removed unused imports, simplified `.encode()` call, formatted to strict 80-char line limit.

### Important Points:
- Mutual exclusion verified: second instance attempting to run reports contention and exits cleanly without crashing or corrupting state.
- Floating capsule opens centered at top of display and allows smooth dragging across screen.
- Total test suite now runs 29 tests in 0.39s with 100% pass rate.

---

## Phase 3: Database Layer & SQLite Persistence

- **Status**: Completed
- **Date**: 2026-10-16

### Phase 3 To-do List:
- [x] Implement `src/plus_ultra/db.py`:
  - [x] Connection factory `get_connection()` enabling `PRAGMA foreign_keys = ON;`, `PRAGMA journal_mode = WAL;`, `busy_timeout = 5000;`, and `row_factory = sqlite3.Row`.
  - [x] ACID transaction context manager `transaction(conn)` with automatic commit and rollback.
  - [x] Schema migration runner `init_db()` using `PRAGMA user_version` (Version 1).
  - [x] Core schema: `categories`, `tasks`, `reminders`, `reminder_fires`, `app_state`.
  - [x] Unique active partial index on `categories(name) WHERE is_deleted = 0`.
  - [x] Due reminders partial index on `reminders(remind_at) WHERE is_deleted = 0`.
- [x] Implement `src/plus_ultra/models.py`:
  - [x] Strongly typed dataclasses: `Category`, `Task`, `Reminder`, `AppState`.
  - [x] Extended `Task` attributes: `task_label`, `critical_level`, `pace_level`, `is_google_task`.
- [x] Implement `src/plus_ultra/repository.py`:
  - [x] `CategoryRepository`: CRUD, active partial index check, soft-delete cascading nullification (`tasks.category_id = NULL`).
  - [x] `TaskRepository`: CRUD, check constraints, soft-delete cascading to reminders (`reminders.is_deleted = 1`).
  - [x] `ReminderRepository`: CRUD, `list_due()` excluding soft-deleted tasks and fired reminders, `mark_fired()`.
  - [x] `AppStateRepository`: Runtime machine state isolation (`widget_x`, `widget_y`).
- [x] Wire widget position persistence:
  - [x] `FloatingWidget` accepts `initial_x`, `initial_y`, and `on_position_change` callback without DB coupling.
  - [x] `src/plus_ultra/main.py` restores saved coordinates and updates `app_state` on drag release.
- [x] Create comprehensive test suites:
  - [x] `tests/test_db.py`: Migrations, WAL pragma, rollback, CHECK constraints, FK enforcement, partial unique index, query plan index usage (12 tests).
  - [x] `tests/test_repository.py`: CRUD, cascading soft deletes, due filtering, app state persistence, corrupt coordinates handling, Unicode & large strings (10 tests).
  - [x] Update `tests/test_ui.py`: Verify position callback firing (total 52 project tests passing).
- [x] Update documentation (`README.md`, `.docs/api.md`, `.docs/architecture.MD`, `.docs/commands.md`, `.docs/progress-log.md`).

### Issues & Status:
- **Ruff SIM117 on nested context managers**: In tests, combined `with pytest.raises(...), transaction(conn) as cur:` to cleanly test rollbacks and constraint violations.
- **Ruff F841 unused variables**: Resolved by asserting exclusion of future reminder IDs from query results.
- **Strict 80-char line length**: Wrapped all multiline SQL queries, dataclass definitions, and comments to fit strictly within 80 characters.

### Important Notes:
- **Clean Architecture Integrity**: `FloatingWidget` has ZERO database imports. Position persistence is wired purely via high-level callback in `main.py`.
- **Machine State vs Preferences Separation**: User settings (`user-settings.json`, mode `0o600`) hold human choices; machine runtime coordinates (`widget_x`, `widget_y`) live in SQLite `app_state`.
- **Active Name Reusability**: Using SQLite partial unique indexes (`WHERE is_deleted = 0`) allows users to soft-delete a category and create a new category with the same name.
- **Query Planner Verification**: `EXPLAIN QUERY PLAN` confirms `idx_reminders_due` is actively leveraged for due reminder scans.
- Total test suite now runs 61 tests in 0.56s with 100% pass rate.

---

## Phase 4: Services Layer & Main Dashboard Panel

- **Status**: Completed
- **Date**: 2026-10-16

### Phase 4 To-do List:
- [x] Implement pure business logic in `src/plus_ultra/services.py`:
  - [x] `TaskService`: task creation with validation (empty title, invalid status, critical levels, pace levels), status toggle (`Pending` <-> `Completed`), soft delete cascade, multi-criteria filtering (category, status, priority), and case-insensitive search.
  - [x] `CategoryService`: validation, active list, creation, update, and soft delete with cascading task nullification.
  - [x] Fully decoupled from Tkinter for headless testing.
- [x] Implement 3-column workspace window in `src/plus_ultra/ui/panel.py`:
  - [x] **Column 1 (Left Sidebar)**: 6 navigation tabs (`Tasks`, `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`) + pinned Settings button.
  - [x] **Column 2 (Center Panel)**:
    - [x] Option A styled `ttk.Treeview` task list.
    - [x] Live search entry filtering by title and description.
    - [x] Status filter buttons (`All`, `Pending`, `Completed`).
    - [x] Priority filter combobox (`All Priority`, `High`, `Medium`, `Low`).
    - [x] Double-click task row to open edit dialog.
    - [x] Right-click context menu (Toggle status, Edit task, Delete task).
    - [x] `TaskDialog` modal for creating and editing tasks with input validation.
    - [x] `CategoryDialog` modal for adding categories.
    - [x] Placeholder views for non-task tabs displaying mapped feature information.
  - [x] **Column 3 (Right Sidebar)**:
    - [x] Notification panel listing active/past alerts.
    - [x] "Mark All Read" button: marks all queued alerts read and notifies the capsule to remove the orange bell indicator.
    - [x] "Clear" button: empties notification list and removes the bell indicator.
- [x] Wire integration in `src/plus_ultra/main.py`:
  - [x] Instantiate `TaskRepository`, `CategoryRepository`, `TaskService`, `CategoryService`.
  - [x] Construct `DashboardPanel` with parent `widget.root`.
  - [x] Bind capsule click callback to `dashboard.toggle`.
  - [x] Connect `on_notifications_cleared` to `widget._update_bell_state`.
  - [x] Verify clean shutdown and smoke-test toggle support.
- [x] Implement comprehensive unit tests:
  - [x] `tests/test_services.py`: 4 tests validating input constraints, status cycling, category soft-delete cascading nullification, and search query filters.
  - [x] `tests/test_panel.py`: 5 tests validating 3-column layout, tab switching, Treeview rendering, filter/search updates, right-click actions, TaskDialog saving, and notification panel actions.
- [x] Verification:
  - [x] All 70 tests passing via `uv run pytest -v`.
  - [x] Clean formatting and zero lint errors via `uv run ruff check .` and `uv run ruff format --check .`.
  - [x] Smoke test passes cleanly via `uv run plus-ultra --smoke-test`.
- [x] Update documentation (`README.md`, `.docs/api.md`, `.docs/architecture.MD`, `.docs/commands.md`, `.docs/progress-log.md`).

### Issues & Status:
- **Tkinter Frame padding tuple error**: Passing `pady=(0, 10)` directly into `tk.Frame(...)` triggered `_tkinter.TclError: expected screen distance but got "0 10"`. Resolved by passing padding tuples to `.pack(pady=(0, 10))` where tuples are valid, keeping `tk.Frame` construction clean.
- **Tkinter withdrawn window test assertions**: `winfo_ismapped()` returns 0 on widgets inside a withdrawn toplevel. Resolved by checking `winfo_manager() == "pack"` to reliably test tab switching in unit tests.
- **Ruff 80-char line limit**: Formatted all method signatures, multiline conditionals, and dialog constructors to conform strictly to `<= 80` characters.

### Important Notes:
- **Architecture Integrity**: `ui/panel.py` imports only from `services.py`, `models.py`, `notifications.py`, and `ui/theme.py`. There are zero direct SQL or database imports in the UI layer.
- **Two-way Capsule Sync**: Clearing or marking notifications read in the right sidebar immediately clears the persistent orange bell on the floating capsule and re-centers the capsule text.
- **Option A Treeview**: Clean, tabular view of tasks with clear status markers (`✓ Completed` / `○ Pending`), category, priority, pace, and due dates.
- Total test suite now runs 70 tests in 1.31s with 100% pass rate.

---

## Phase 5: Reminders, Desktop Notifications & Background Scheduler

- **Status**: Completed
- **Date**: 2026-10-16

### Decision D1 (System Tray vs Floating Capsule & Native Notifications):
- Executed tray spike with `pystray._xorg` on Ubuntu GNOME on Wayland.
- Ubuntu GNOME top bar uses the `ubuntu-appindicators` extension (`StatusNotifierItem` DBus interface), while the legacy X11 XEmbed tray has been removed from GNOME.
- User evaluated Decision D1 and approved the recommended option: **Drop the system tray** (`pystray`/`Pillow`) to maintain a 100% pure Python standard library stack with zero external C-binding dependencies, relying on the **Floating Capsule** and **Native Desktop Notifications** (`notify-send`).

### Phase 5 To-do List:
- [x] Implement native desktop notifications in `src/plus_ultra/desktop.py`:
  - [x] `send_desktop_notification(title, message, urgency, timeout_ms, app_name)` invoking `notify-send` via `subprocess.run` with argument list and `shell=False`.
  - [x] Check executable presence via `shutil.which`.
  - [x] Graceful error handling (`SubprocessError`, `OSError`) without crashing.
  - [x] Alias `notify = send_desktop_notification`.
- [x] Implement `ReminderService` in `src/plus_ultra/services.py`:
  - [x] `create_reminder`: validation of task existence and non-empty timestamp.
  - [x] `get_due_reminders`: query due reminders joined with active tasks, excluding fired or deleted reminders.
  - [x] `mark_fired`: atomically record in `reminder_fires`.
  - [x] `is_fired`: check firing state.
  - [x] `soft_delete_reminder`: soft delete reminder.
- [x] Implement `ReminderScheduler` in `src/plus_ultra/scheduler.py`:
  - [x] Dedicated daemon worker thread polling every 10 seconds (`REMINDER_POLL_MS = 10_000`).
  - [x] Thread-isolated SQLite WAL connection to prevent concurrency errors.
  - [x] Producer-consumer pattern: queries SQLite, dispatches `notify-send` desktop alerts, and thread-safely enqueues in-app alerts to the floating capsule and dashboard panel.
  - [x] Controlled cancellation using `threading.Event`.
  - [x] Respects `reminders_enabled` user setting flag.
- [x] Wire integration in `src/plus_ultra/main.py`:
  - [x] Instantiate `ReminderRepository`, `ReminderService`, `ReminderScheduler`.
  - [x] Safe in-app callback enqueuing via `widget.root.after_idle`.
  - [x] Clean shutdown in `_signal_handler` and `finally:` calling `scheduler.stop()`.
  - [x] Support smoke test execution (`scheduler.tick()`).
- [x] Automated test suites:
  - [x] `tests/test_desktop.py`: 3 new unit tests for `send_desktop_notification` (success, missing executable, subprocess error).
  - [x] `tests/test_scheduler.py`: 4 new unit tests (due evaluation, future exclusion, soft-deleted task exclusion, settings disabled, thread lifecycle).
  - [x] `tests/test_services.py`: `test_reminder_service_lifecycle_and_validation` validating constraints and atomic firing.
  - [x] All 78 tests passing via `uv run pytest -v`.
- [x] Verification:
  - [x] Clean linting and formatting via `uv run ruff check .` and `uv run ruff format --check .`.
  - [x] Smoke test passes cleanly via `uv run plus-ultra --smoke-test`.
- [x] Update documentation (`README.md`, `.docs/api.md`, `.docs/architecture.MD`, `.docs/commands.md`, `.docs/progress-log.md`).

### Issues & Status:
- **SQLite check_same_thread concurrency error**: Sharing the main thread's SQLite connection with the background scheduler thread caused `ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. Resolved by opening a dedicated thread-isolated SQLite connection in WAL mode within `ReminderScheduler._run_loop()`, cleanly closing it upon thread exit.
- **Decision D1 C-binding complexity**: `pystray`'s AppIndicator backend required `PyGObject` binary wheels which failed to build without system `pkg-config`/`cairo` dev packages. Settled by dropping `pystray`/`Pillow` in favor of standard-library `subprocess` `notify-send` and the floating capsule.
- **Font Rendering on XWayland**: Tkinter fell back to jagged pixelated bitmap font `fixed` when requesting `DejaVu Sans` because the system's X11 server font database lacked that exact name. Resolved by updating `font_family` to `helvetica`, which maps directly to vector TrueType `nimbus sans l`.
- **Button Outlines and Severe Truncation**: Default Tkinter buttons rendered with 1px raised border and 1px highlight ring, causing harsh white/gray double-borders. Left sidebar (180px) and notification panel (220px) were too narrow. Resolved by setting `bd=0, highlightthickness=0, relief="flat"`, widening the sidebar to 230px, the notification panel to 240px, and default window geometry to 1180x700.
- **All 6 Workspace Tabs Fully Interactive**: Non-task tabs previously had placeholder text. Implemented Schema Migration 2 with tables `code_items`, `courses`, `ideas_doubts`, `opportunities`, and `quick_links`. Replaced placeholders with full working sub-views (code copy feedback, DSA solver toggles, course progress increments, idea status cycling, opportunity tracker, and desktop quick launcher with click counter).

### Important Notes:
- **100% Python Standard Library**: Application requires zero external pip packages in production runtime.
- **Thread Safety**: UI calls from the background thread are safely deferred to the Tkinter main thread using `widget.root.after_idle`.
- **Exactly-Once Alert Semantics**: Dispatched reminders are committed to `reminder_fires` table immediately, preventing duplicate alerts across restarts or polling cycles.
- **Interactive Feature Verification**: All 6 tabs (`Tasks`, `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`) plus `Settings` are 100% interactive and testable with seeded demo data.
- Total test suite now runs 81 tests in 3.98s with 100% pass rate.

---

## Next: Phase 6: Robustness, Startup, and Autostart

- **Status**: Ready for Planning
- **Target**:
  - Implement Decision D2 (autostart path resolution).
  - Implement CLI flags: `--install-autostart` and `--uninstall-autostart` writing or removing `~/.config/autostart/plus-ultra.desktop`.
  - Implement `ui/splash.py`: startup progress logger (`[1/4] Paths`, `[2/4] Database`, `[3/4] Scheduler`, `[4/4] Ready`).
  - Graceful process termination and single-instance validation across user session logout/login.




