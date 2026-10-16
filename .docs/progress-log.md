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
- **Button Outlines and Severe Truncation**: Default Tkinter buttons rendered with 1px raised border and 1px highlight ring, causing harsh white/gray double-borders. Left sidebar (180px) and notification panel (220px) were too narrow. Resolved by setting `bd=0, highlightthickness=0, relief="flat"`, widening the sidebar to 250px, the notification panel to 280px, and default window geometry to 1280x800.
- **Complete CRUD & Guaranteed Visible Confirmation Buttons**: All modal dialogs across all 6 tabs now feature a dedicated, fixed-bottom action bar guaranteeing that `✓ Save [Item]` and `✕ Cancel` buttons are permanently visible regardless of screen size or window manager borders. Full `update` and `delete` operations implemented on repositories, services, and UI.
- **Tasks UI Card Modernization**: Replaced sterile `ttk.Treeview` "SQL table" with a modern card-based layout featuring clickable completion checkboxes, color-coded priority/pace chips, category tags, due date/time badges, and direct `✏️ Edit` and `🗑️ Delete` actions.
- **Task Date & Time Options**: Task creation and editing now includes explicit Due Date and Due Time fields with quick presets (`09:00`, `14:00`, `18:00`, `23:59`) and optional desktop reminder scheduling.
- **Double Capsule Size & Visibility Coordination**: Floating capsule dimensions doubled to `320x72` (radius 36) with scaled-up typography and animated border beam. Capsule automatically hides (`withdraw()`) when the workspace opens and reappears (`deiconify()`) when closed.

### Important Notes:
- **100% Python Standard Library**: Application requires zero external pip packages in production runtime.
- **Thread Safety**: UI calls from the background thread are safely deferred to the Tkinter main thread using `widget.root.after_idle`.
- **Exactly-Once Alert Semantics**: Dispatched reminders are committed to `reminder_fires` table immediately, preventing duplicate alerts across restarts or polling cycles.
- **Interactive Feature Verification**: All 6 tabs (`Tasks`, `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`) plus `Settings` are 100% interactive and testable with full CRUD, seeded demo data, and modern card styling.
- Total test suite runs 81 tests with 100% pass rate.

---

## Architecture Refactoring: Modular Architecture Decomposition

- **Status**: Completed
- **Date**: 2026-10-16

### Objective:
Eliminate oversized "god" modules (`ui/panel.py` at 3,784 lines, `repository.py` at 1,361 lines, `services.py` at 701 lines, `db.py` at 648 lines, and `ui/floating.py` at 514 lines), decompose into single-responsibility modules, enforce a strict `<= 500` lines-per-file ceiling, and ensure zero regressions across tests and runtime.

### Refactoring To-do List:
- [x] Baseline audit: Confirmed 81 passing tests and 0 ruff lint errors.
- [x] Stage 1: Decompose database package (`src/plus_ultra/database/`):
  - [x] `connection.py` (51 lines): SQLite connection factory, WAL pragma, transaction CM.
  - [x] `schema.py` (159 lines): Migration schemas V1 and V2 SQL.
  - [x] `migrations.py` (52 lines): Version lookup and schema runner.
  - [x] `seeds.py` (404 lines): Workspace seed dataset.
  - [x] `__init__.py` (32 lines): Public symbol re-exports.
- [x] Stage 2: Decompose repositories package (`src/plus_ultra/repositories/`):
  - [x] `base.py` (10 lines): Common UTC timestamp utilities.
  - [x] 9 Single-table repositories: `category_repository.py` (118 lines), `task_repository.py` (217 lines), `reminder_repository.py` (117 lines), `app_state_repository.py` (51 lines), `code_repository.py` (194 lines), `course_repository.py` (195 lines), `idea_doubt_repository.py` (181 lines), `opportunity_repository.py` (196 lines), `quick_link_repository.py` (152 lines).
  - [x] `__init__.py` (62 lines): Re-exports all repositories and row converters.
- [x] Stage 3: Decompose services package (`src/plus_ultra/services/`):
  - [x] 8 Pure domain services: `task_service.py` (169 lines), `category_service.py` (48 lines), `reminder_service.py` (59 lines), `code_service.py` (85 lines), `course_service.py` (87 lines), `idea_doubt_service.py` (93 lines), `opportunity_service.py` (103 lines), `quick_link_service.py` (73 lines).
  - [x] `__init__.py` (34 lines): Clean package marker and symbol exports.
- [x] Stage 4: Decompose presentation layer (`src/plus_ultra/ui/`):
  - [x] `geometry.py` (69 lines): Mathematical capsule polygon and perimeter beam generator.
  - [x] `floating.py` (452 lines): Capsule widget trimmed down from 514 lines.
  - [x] `ui/components/`: `scrollable.py` (47 lines), `sidebar.py` (160 lines), `notifications_panel.py` (123 lines), `__init__.py` (13 lines).
  - [x] `ui/dialogs/`: `base.py` (19 lines), `task_dialog.py` (328 lines), `code_dialog.py` (215 lines), `course_dialog.py` (246 lines), `idea_dialog.py` (200 lines), `opportunity_dialog.py` (242 lines), `quick_link_dialog.py` (147 lines), `category_dialog.py` (97 lines), `__init__.py` (23 lines).
  - [x] `ui/views/`: `tasks_view.py` (418 lines), `code_view.py` (364 lines), `courses_view.py` (320 lines), `ideas_view.py` (279 lines), `opportunities_view.py` (303 lines), `quick_links_view.py` (268 lines), `settings_view.py` (152 lines), `__init__.py` (21 lines).
  - [x] `panel.py` (436 lines): Streamlined coordinator window trimmed from 3,784 lines, with `TreeCompatibilityFacade` preserving backward compatibility with existing tests.
- [x] Stage 5: Verification & Quality Gate:
  - [x] All 81 unit tests pass in 2.31s via `uv run pytest`.
  - [x] Smoke test passes cleanly via `uv run plus-ultra --smoke-test`.
  - [x] 0 lint errors via `uv run ruff check .`.
  - [x] Clean format via `uv run ruff format --check .` (87 files).
  - [x] 100% of Python modules in `src/plus_ultra` are strictly `<= 500` lines (max 452 lines).
  - [x] Strict PEP 8 and `<= 80` characters line limit enforced.

### Issues & Status:
- **Pre-release Clean Slate & Elimination of Facades**: Because PLUS-ULTRA is in pre-release development, maintaining backward-compatibility shims (`db.py` and `repository.py`) added unnecessary technical debt. Deleted both facades and converted all application modules (`main.py`, `scheduler.py`) and test suites to import directly from `plus_ultra.database` and `plus_ultra.repositories`.
- **Test attribute delegation**: `tests/test_panel.py` directly exercised attributes of `DashboardPanel` (e.g. `sidebar_col`, `search_entry`, `_filtered_tasks`, `tree.get_children()`). Resolved by implementing property delegates on `DashboardPanel` forwarding to `Sidebar` and `TasksView`, maintaining 100% test compatibility without rewriting tests.

### Important Notes:
- Zero third-party dependencies introduced; purely standard-library Python 3.12+.
- Clean, maintainable architecture ready for Phase 6.

---

## Testing Experience Review & UX Refinements

- **Status**: Completed
- **Date**: 2026-10-16

### Phase To-do List:
- [x] Adjustable window dividers (`tk.PanedWindow`) for left-main and main-right sashes with explicit minsize constraints (`sidebar_col >= 180`, `center_col >= 400`, `notif_col >= 100`).
- [x] Tab customizability via manual cursor drag-and-drop in left sidebar (`Sidebar`).
- [x] Clean, enlarged left sidebar tabs (3x box padding `pady=16, padx=20`, 2x font size `13pt bold`), removed useless bottom-left close button.
- [x] Quick Links first-class tab in left navigation with full CRUD.
- [x] Separated DSA Problem Tracker into dedicated sub-tab in right drawer alongside Notifications, plus dedicated center view `DSAView`.
- [x] Removed "DSA Problem Tracker" from `Code Lab` view to eliminate mismatch with code workspace.
- [x] Eliminated hardcoded emojis across all views, cards, buttons, dialogs, and capsule; introduced `src/plus_ultra/ui/icons.py` with Tkinter `PhotoImage.subsample()` scaling from `fallback.png`.
- [x] Deleted `Coursera`, `NPTEL`, and `Self-Paced` options from Courses view and dialogs.
- [x] Generous dialog sizing across all modal dialogs in `src/plus_ultra/ui/dialogs/` (`680x700`, `680x680`, `640x620`, etc.).
- [x] 2x card sizing (double padding, larger fonts, clean action buttons) across all content views.
- [x] Adapted to user-moved `default-settings.json` and `metadata.json` in `src/plus_ultra/resources/data/`.
- [x] Relocated `seeds.py` out of `src/` to `.scripts/seeds.py` with standalone CLI execution.
- [x] Renamed `tests/` directory to `.tests/` and updated `pyproject.toml`.
- [x] Quality Gate: All 81 unit tests pass (`uv run pytest`), 0 ruff lint errors (`uv run ruff check .`), smoke test passes cleanly (`uv run plus-ultra --smoke-test`).

### Issues & Solutions:
- **TclError: image "pyimage2" does not exist in multi-root pytest runs**: `PhotoImage` objects are tied to a specific Tcl interpreter. When pytest destroyed a root window and created a new one, module-level icon caches held stale references. Resolved by keying the icon cache by `(id(active_root), icon_name, size)` and verifying `active_root.tk.call("image", "type", ...)` before returning cached images.
- **SIM114 & Line Length in DSA Filters**: Long chained `if ... or ...` expressions generated line length and ruff violations. Extracted clean predicate methods `_matches_dsa_filter()` and `_matches_filter()` respecting strict `<= 80` character limits.
- **ScrollableFrame attribute consistency**: Fixed view components accessing `.scrollable_frame` to use the canonical `ScrollableFrame.interior` widget.

---

## Interactive UI & Component Refinements

- **Status**: Completed
- **Date**: 2026-10-17

### Phase To-do List:
- [x] Settings button: Converted to compact icon-only square button on bottom-left with fallback to `fallback.png`.
- [x] Sidebar tab renamings:
  - `"Tasks & Deadlines"` -> `"Tasks"`
  - `"Ideas & Doubts"` -> `"PS/I"`
  - `"Code Lab"` -> `"Code c-p"`
- [x] Right Drawer cleaned: Removed DSA Tracker from right drawer (DSA is a dedicated view `DSAView` on the left sidebar).
- [x] Network Status:
  - Created `src/plus_ultra/network.py` with `is_network_online` and thread-safe `NetworkStatusMonitor` using a pure Python FIFO queue (zero Tcl cross-threading).
  - Added live network status indicators to left sidebar bottom and right drawer bottom with a manual probe button.
- [x] Dynamic Floating Capsule:
  - Implemented `_update_capsule_geometry()` to auto-adjust capsule width dynamically when unread notifications arrive/clear.
  - Implemented 3-second transient popup capsule pill positioned directly below the main capsule emphasizing notification titles.
- [x] Interactive DateTimePicker:
  - Created reusable component `src/plus_ultra/ui/components/datetime_picker.py` with `⚡ Now` button, date presets (`Today`, `Tomorrow`, `+3 Days`, `+1 Wk`), time shortcuts, and day steppers (`-1d`, `+1d`).
  - Refactored `TaskDialog` and `OpportunityDialog` to use this single shared component without code duplication.
- [x] Tasks inline category creation:
  - Removed `+ Category` button from top of Tasks view.
  - Added inline category creation directly inside `TaskDialog` via `"+ Add New Category..."` combobox item and `+` button.
- [x] Code Dialog predefined languages:
  - Added predefined languages combobox (`Python`, `JavaScript`, `TypeScript`, `C`, `C++`, `Java`, `Rust`, `Go`, `Bash`, `SQL`, etc.).
- [x] PS/I Ideas view:
  - Replaced filter buttons with two distinct sub-tabs: `[ Project Ideas ]` and `[ Concept Doubts ]`.
  - Added contextual creation actions (`+ Add Idea` on Ideas subtab, `+ Add Doubt` on Doubts subtab).
- [x] Validation:
  - Full suite of 88 unit tests passing via `uv run pytest -v`.
  - 0 ruff lint errors via `uv run ruff check .`.
  - Clean format via `uv run ruff format --check .`.
  - Smoke test passing via `uv run plus-ultra --smoke-test`.

### Issues & Solutions:
- **Segmentation fault from background thread Tkinter calls**: Calling `after_idle` or `configure` on Tkinter widgets from a secondary background thread during test teardown caused Tcl interpreter memory corruption. Resolved by introducing `NetworkStatusMonitor` with pure Python `queue.Queue`. The background worker thread only communicates via the queue, and the main thread safely polls the queue using `container.after()`.
- **Due entry test compatibility**: Tests in `test_panel.py` directly addressed `dialog.due_entry.insert()`. Resolved by exposing `@property def due_entry` on `TaskDialog` and `OpportunityDialog` delegating directly to `DateTimePicker.entry`.

---

## UI Polish, Reminder Reliability & Diagnostics

- **Status**: Completed
- **Date**: 2026-10-17

### Phase To-do List:
- [x] Fix Reminder Scheduling & Evaluation:
  - Created `src/plus_ultra/datetime_utils.py` with `parse_flexible_datetime()`.
  - Resolved root cause of reminder non-dispatch: replaced fragile SQLite ASCII string comparison (`r.remind_at <= ?`) with timezone-aware datetime comparison handling local naive strings (`"YYYY-MM-DD HH:MM"`), ISO-8601 with `"Z"`, and offset-aware datetimes.
  - Reduced scheduler poll interval from 10.0s to 2.0s for immediate alert responsiveness.
  - Removed silent `contextlib.suppress(Exception)` in `TasksView` and added explicit logging and error visibility.
- [x] Network Status Capsule Dot & Setting Toggle:
  - Deleted network status division from Left Sidebar (`Sidebar`) and Right Drawer (`NotificationsPanel`).
  - Added small, clean network status indicator dot (`net_dot_id`) on the right side of the floating capsule.
  - Added `"network_monitor_enabled": true` to `src/plus_ultra/resources/data/default-settings.json`.
  - Added toggle checkbox in `SettingsView` under "Widget Behavior" to enable/disable network monitoring and capsule dot.
- [x] 5x Settings Icon in Left Sidebar:
  - Enlarged settings icon button in `Sidebar` to 80px (`get_icon("settings", 80) or get_icon("fallback", 80)`), providing an easily accessible, prominent button in the bottom-left corner.
- [x] Cleaned Course Platform Categories:
  - Removed `"Independent"` and `"Book"` tags from `CoursesView` filter buttons (`["All", "University", "YouTube", "Other"]`).
  - Removed `"Independent"` and `"Book"` options from `CourseDialog` platform dropdown.
- [x] Comprehensive Debug Logging:
  - Fixed logging configuration in `src/plus_ultra/main.py`: attached stream and file handlers to the root logger and `plus_ultra` namespace so all module logs appear in console stdout and write to `launcher.log`.
  - Added detailed, structured `logger.info()` logging across task creation, task updates, status toggles, task deletions, reminder scheduling, and scheduler firing across `task_service.py`, `reminder_service.py`, `tasks_view.py`, `course_service.py`, and `code_service.py`.
- [x] Quality Gates & Test Suite:
  - All 95 unit tests passing (`uv run pytest -v`).
  - Zero lint errors with strict ruff checks (`uv run ruff check .`).
  - Code fully formatted (`uv run ruff format --check .`).
  - Strict compliance with line constraints: all files strictly <= 500 lines, all lines <= 80 characters.

### Issues & Solutions:
- **Reminder non-firing on user test**: The background scheduler evaluated `now` using `datetime.now(UTC).isoformat()`. Because user input was stored in local system time (IST +05:30), ASCII string comparison against UTC time from the previous day evaluated to `False`, delaying alerts by 5.5 hours. Furthermore, difference in separators (`' '` vs `'T'`) broke string inequality. Solved by creating `parse_flexible_datetime` to parse both naive local time and UTC formats and evaluate aware datetimes in Python.
- **Unprinted module logs**: `configure_logging()` previously configured only logger named `"plus-ultra"` (hyphenated `APP_NAME`), while all Python submodules used standard `logger = logging.getLogger(__name__)` (underscored package `"plus_ultra"`). Logs were silently dropped. Solved by configuring the root logger and `"plus_ultra"` logger hierarchy.

---

## Beta Release Quality Refactoring

- **Status**: Completed
- **Date**: 2026-10-17

### Phase To-do List:
- [x] Testing & Utility Scripts (`.scripts/`):
  - Created `.scripts/clear_db.py`: Full domain database clearing utility supporting hard `DELETE` or soft delete (`is_deleted = 1`), runtime `app_state` clearing, SQLite `VACUUM`, and `--force` headless confirmation bypassing.
  - Created `.scripts/seed_data.py`: Dual-mode dataset utility supporting `--seed` (populating demo records for tasks, code snippets, courses, doubts, opportunities, and quick links) and `--unseed` (cleanly removing seeded demo records and cascading to reminders without disturbing user data).
  - Maintained `.scripts/seeds.py` as a backward-compatible wrapper delegating to `seed_data.py`.
  - Created `.scripts/notify.py`: Standalone desktop notification testing CLI supporting immediate execution (`uv run python .scripts/notify.py`) or delayed execution after `X` minutes (`uv run python .scripts/notify.py 2`) or seconds (`-s 15`) with a live console countdown.
- [x] Architecture & God-File Deconstruction:
  - Extracted `CapsulePopupPill` into `src/plus_ultra/ui/components/popup_pill.py`: Encapsulates transient 3-second alert banners, XShape masking, canvas layout, positioning, and auto-dismissal. Reduced `floating.py` from 495 to 448 lines.
  - Extracted `TaskCard` into `src/plus_ultra/ui/components/task_card.py`: Standalone card widget handling task status toggle, title, badges (category, priority, pace, due date, Google task), overdue highlighting, and Edit/Delete action handlers. Reduced `tasks_view.py` from 473 to 331 lines.
  - Refactored `DashboardPanel._switch_tab()` in `panel.py` into dictionary-based dispatch, keeping `panel.py` comfortably within bounds.
  - Re-exported new components in `src/plus_ultra/ui/components/__init__.py`.
- [x] Configuration & State Centralization:
  - Extended `src/plus_ultra/resources/data/default-settings.json` with `panel_width` (1380), `panel_height` (840), `panel_min_width` (1000), `panel_min_height` (640), and `notification_popup_duration_ms` (3000).
  - Implemented `<Configure>` resize tracking and automatic dimension persistence in `DashboardPanel`: when the user resizes the dashboard and closes it, the new dimensions persist to `~/.config/plus-ultra/user-settings.json` and restore on next launch.
  - Configured `FloatingWidget` and `CapsulePopupPill` to respect `notification_popup_duration_ms` with graceful fallback handling.
- [x] Test Coverage & Quality Gates:
  - Created `.tests/test_scripts.py` verifying `seed_data.py`, `clear_db.py`, and `notify.py` execution, arguments, and database effects.
  - Added component unit tests for `CapsulePopupPill` and `TaskCard` in `.tests/test_refinements.py`.
  - Added dimension persistence test in `.tests/test_settings.py`.
  - Full suite expanded to **103 unit tests** passing cleanly (`uv run pytest -v`).
  - Zero Ruff linter errors (`uv run ruff check .`) and 100% code formatted (`uv run ruff format --check .`).
- [x] Documentation Uniformity:
  - Synchronized `README.md`, `.docs/architecture.MD`, `.docs/commands.md`, and `.docs/api.md` with new scripts, components, test suites, and configuration options.

### Issues & Solutions:
- **`winfo_exists` integer return type in Tkinter**: `CapsulePopupPill.is_visible` asserted against `True`, but Tkinter's `winfo_exists()` returns an integer `1` or `0`, causing an `AssertionError: assert 1 is True`. Resolved by wrapping the return in `bool(self.window is not None and self.window.winfo_exists())`.
- **Ruff alias import sorting in scripts test**: Importing functions under multiple aliases from `.scripts` files caused import sorting conflicts with first-party package boundaries. Resolved by importing `clear_db`, `notify`, and `seed_data` as module namespaces.
- **`NetworkStatusMonitor` attribute mismatch during smoke-test**: During `uv run plus-ultra --smoke-test`, `floating.py` attempted to access `self._net_monitor.status.is_online`, but `NetworkStatusMonitor` in `network.py` only provided `get_result()`. Resolved by exposing `self.last_status: bool = True` on `NetworkStatusMonitor` and updating `floating.py` to retrieve the cached state.

---

## Next: Phase 6: Robustness, Startup, and Autostart

- **Status**: Ready for Planning
- **Target**:
  - Implement Decision D2 (autostart path resolution).
  - Implement CLI flags: `--install-autostart` and `--uninstall-autostart` writing or removing `~/.config/autostart/plus-ultra.desktop`.
  - Implement `ui/splash.py`: startup progress logger (`[1/4] Paths`, `[2/4] Database`, `[3/4] Scheduler`, `[4/4] Ready`).
  - Graceful process termination and single-instance validation across user session logout/login.


