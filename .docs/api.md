# PLUS-ULTRA API & Interface Documentation

This document records public APIs, module interfaces, and command-line entry points across each development phase.

---

## 1. CLI Entry Points

### `plus-ultra`
- **Module**: `plus_ultra.main:main`
- **Arguments**:
  - `argv: list[str] | None`: Command line arguments (defaults to `sys.argv[1:]`).
- **Return Code**: `0` on successful execution.
- **Behavior**: Initializes dual logging (`sys.stdout` and `$XDG_STATE_HOME/plus-ultra/launcher.log`), logs startup paths, and exits cleanly.

---

## 2. Implemented Module Specifications (Phase 1)

### `plus_ultra.config`
- `get_data_dir() -> Path`: Resolves `$XDG_DATA_HOME/plus-ultra` (fallback: `~/.local/share/plus-ultra`). Creates directory with mode `0o700`.
- `get_state_dir() -> Path`: Resolves `$XDG_STATE_HOME/plus-ultra` (fallback: `~/.local/state/plus-ultra`). Creates directory with mode `0o700`.
- `get_config_dir() -> Path`: Resolves `$XDG_CONFIG_HOME/plus-ultra` (fallback: `~/.config/plus-ultra`). Creates directory with mode `0o700`.
- `get_db_path() -> Path`: Returns `get_data_dir() / "plus-ultra.sqlite3"`.
- `get_log_path() -> Path`: Returns `get_state_dir() / "launcher.log"`.
- `get_user_settings_path() -> Path`: Returns `get_config_dir() / "user-settings.json"`.
- `get_app_version() -> str`: Returns installed package version via `importlib.metadata.version` (fallback `"0.1.0"`).
- `get_metadata() -> dict[str, Any]`: Loads application metadata dictionary (`app_name`, `display_name`, `company`, `description`) from packaged resources.
- **Constants**:
  - `APP_NAME: str = "plus-ultra"`
  - `DB_FILENAME: str = "plus-ultra.sqlite3"`
  - `LOG_FILENAME: str = "launcher.log"`
  - `USER_SETTINGS_FILENAME: str = "user-settings.json"`

### `plus_ultra.main`
- `configure_logging() -> Path`: Sets up dual logging handlers (FileHandler with UTF-8 encoding in state directory, StreamHandler to stdout) with ISO-8601 timestamps. Returns the active log file path.
- `parse_args(args: list[str] | None = None) -> argparse.Namespace`: Parses CLI arguments using packaged metadata.
- `main(argv: list[str] | None = None) -> None`: Main application routine.

---

## 3. Implemented Module Specifications (Phase 1b)

### `plus_ultra.settings`
- `load_default_settings() -> dict[str, Any]`: Loads read-only default settings packaged in `plus_ultra.resources/default-settings.json`.
  - Schema keys: `settings_version` (int: 1), `always_on_top` (bool: true), `glow_enabled` (bool: true), `glow_pulse_period_ms` (int: 3000), `reminders_enabled` (bool: true).
- `load_effective_settings() -> dict[str, Any]`: Returns effective settings merging defaults with user overrides from `$XDG_CONFIG_HOME/plus-ultra/user-settings.json`.
  - Unknown keys in user file are safely ignored.
  - Keys with mismatched types (strictly checked: `type(val) is type(default_val)`) are ignored, retaining default values.
  - Corrupted JSON files or non-dictionary roots are quarantined to `user-settings.json.bad-<timestamp>` without crashing.
- `update_user_setting(key: str, value: Any) -> dict[str, Any]`: Validates that `key` exists and `type(value) is type(default[key])` (raises `KeyError` or `TypeError` on invalid inputs). Persists overrides atomically via temporary file and POSIX rename (`os.replace`) with mode `0o600`. Returns updated effective settings.
- `reset_setting(key: str) -> None`: Removes user override for `key` and restores default value.
- `reset_all_settings() -> None`: Clears all user overrides, removing the settings file and restoring default settings.
- `reload() -> dict[str, Any]`: Forces an immediate reload from disk, bypassing memory cache.

---

## 4. Implemented Module Specifications (Phase 2)

### `plus_ultra.desktop`
- `SingleInstanceLock(lock_path: Path | None = None)`:
  - `acquire() -> bool`: Attempts to acquire an exclusive, non-blocking advisory file lock (`fcntl.flock(LOCK_EX | LOCK_NB)`) on `$XDG_STATE_HOME/plus-ultra/plus-ultra.lock`. Writes current PID to the file. Returns `True` if acquired, `False` on contention.
  - `release() -> None`: Releases lock (`fcntl.LOCK_UN`), closes file descriptor, and unlinks lock file.
  - Supports Python context manager (`with SingleInstanceLock(): ...`).

### `plus_ultra.ui.theme`
- `CapsuleGeometry`: NamedTuple containing `width: int = 140`, `height: int = 36`, `radius: int = 18`, `top_offset: int = 12`.
- `CapsuleTheme`: NamedTuple containing color tokens:
  - `window_bg: "#12151c"`
  - `idle_fill: "#1a1f2c"`, `idle_border: "#2b3448"`, `idle_text: "#cbd5e1"`
  - `hover_fill: "#242c3d"`, `hover_border: "#00e5ff"`, `hover_text: "#ffffff"`
  - `font_family: "DejaVu Sans"`, `font_size: 9`

### `plus_ultra.ui.floating`
- `FloatingWidget(root: tk.Tk | None, geometry: CapsuleGeometry, theme: CapsuleTheme, on_click_callback: Callable | None, initial_x: int | None = None, initial_y: int | None = None, on_position_change: Callable[[int, int], None] | None = None)`:
  - Initializes a borderless (`overrideredirect(True)`), `-topmost` floating window.
  - Places widget at `(initial_x, initial_y)` if provided, else defaults to top-center of the primary display.
  - Draws a smooth capsule polygon with hover glow animation.
  - Implements mouse drag tracking (`<Button-1>`, `<B1-Motion>`), firing `on_position_change(x, y)` when dragging finishes.
  - Triggers `on_click_callback()` on mouse release when no dragging occurred.
  - `close() -> None`: Closes window and exits main event loop cleanly.
  - `run() -> None`: Starts Tkinter `mainloop()`.

### CLI Flags (`plus-ultra`)
- `--smoke-test`: Automatically initializes database and logging, launches floating widget, and closes after 500ms, returning exit code 0.
- `--no-ui`: Initializes configuration, database schema, state directories, and logging without starting GUI event loop.

---

## 5. Implemented Module Specifications (Phase 3)

### `plus_ultra.db`
- `CURRENT_SCHEMA_VERSION: int = 1`: Version marker for PRAGMA user_version migrations.
- `get_connection(db_path: Path | None = None) -> sqlite3.Connection`:
  - Returns a configured SQLite connection to `db_path` or `$XDG_DATA_HOME/plus-ultra/plus-ultra.sqlite3`.
  - Enables `PRAGMA foreign_keys = ON;`.
  - Enables `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for non-blocking concurrent reads).
  - Sets `PRAGMA busy_timeout = 5000;` (5-second lock timeout).
  - Sets `row_factory = sqlite3.Row` for dict-accessible column names.
- `transaction(conn: sqlite3.Connection) -> ContextManager[sqlite3.Cursor]`:
  - Context manager guaranteeing ACID transaction atomicity.
  - Commits automatically if the block executes without error.
  - Rolls back immediately on any unhandled exception.
- `get_schema_version(conn: sqlite3.Connection) -> int`: Returns current `PRAGMA user_version`.
- `set_schema_version(conn: sqlite3.Connection, version: int) -> None`: Sets `PRAGMA user_version`.
- `init_db(db_path: Path | None = None) -> None`:
  - Runs pending database schema migrations incrementally.
  - Migration 1 creates tables: `categories`, `tasks`, `reminders`, `reminder_fires`, `app_state`, plus partial indexes `idx_categories_name_active` and `idx_reminders_due`.

### `plus_ultra.models`
- Strongly typed `@dataclass(slots=True)` models:
  - `Category`: `id: str`, `name: str`, `color: str = "#4a5568"`, `created_at: str`, `updated_at: str`, `synced_at: str | None`, `is_deleted: int = 0`.
  - `Task`: `id: str`, `title: str`, `category_id: str | None`, `description: str`, `due_date: str | None`, `status: str = "Pending"`, `task_label: str = "College"`, `critical_level: str = "Medium"`, `pace_level: str = "Short-term"`, `is_google_task: bool = False`, `created_at: str`, `updated_at: str`, `synced_at: str | None`, `is_deleted: int = 0`.
  - `Reminder`: `id: str`, `task_id: str`, `remind_at: str`, `created_at: str`, `updated_at: str`, `synced_at: str | None`, `is_deleted: int = 0`.
  - `AppState`: `key: str`, `value: str`.

### `plus_ultra.repository`
- `CategoryRepository(conn: sqlite3.Connection)`:
  - `create(name: str, color: str = "#4a5568") -> Category`: Creates new category. Enforces unique name among active categories.
  - `get_by_id(category_id: str) -> Category | None`: Retrieves category by UUID.
  - `list_active() -> list[Category]`: Lists active (non-deleted) categories ordered alphabetically NOCASE.
  - `update(category_id: str, name: str, color: str) -> Category | None`: Updates category name and color.
  - `soft_delete(category_id: str) -> bool`: Soft-deletes category (`is_deleted = 1`) and cascades `tasks.category_id = NULL` in the same transaction.
- `TaskRepository(conn: sqlite3.Connection)`:
  - `create(...) -> Task`: Creates new task. Validates `title` length > 0, `status`, `critical_level`, and `pace_level`.
  - `get_by_id(task_id: str) -> Task | None`: Retrieves task by UUID.
  - `list_active(category_id: str | None = None, status: str | None = None) -> list[Task]`: Lists active tasks with optional category and status filtering.
  - `update(task_id: str, ...) -> Task | None`: Updates task attributes and automatically updates `updated_at`.
  - `soft_delete(task_id: str) -> bool`: Soft-deletes task and cascades soft-delete to all related reminders (`reminders.is_deleted = 1`) in the same transaction.
- `ReminderRepository(conn: sqlite3.Connection)`:
  - `create(task_id: str, remind_at: str) -> Reminder`: Schedules a reminder for an existing task.
  - `get_by_id(reminder_id: str) -> Reminder | None`: Retrieves reminder by UUID.
  - `list_due(before_timestamp: str) -> list[Reminder]`: Queries active reminders due at or before timestamp, excluding reminders where the parent task was soft-deleted or the reminder was already dispatched on this device.
  - `mark_fired(reminder_id: str) -> None`: Records reminder dispatch in `reminder_fires`.
  - `is_fired(reminder_id: str) -> bool`: Checks if reminder was already dispatched on this device.
  - `soft_delete(reminder_id: str) -> bool`: Soft-deletes an individual reminder.
- `AppStateRepository(conn: sqlite3.Connection)`:
  - `get(key: str, default: str | None = None) -> str | None`: Reads runtime machine state value.
  - `set(key: str, value: str) -> None`: Sets or updates machine state value via upsert (`ON CONFLICT(key) DO UPDATE`).
  - `get_widget_position() -> tuple[int, int] | None`: Reads saved `(widget_x, widget_y)`.
### `plus_ultra.notifications`
- `CapsuleNotification`: Dataclass containing `id: str`, `title: str`, `message: str`, `icon: str`, `action_label: str`, `dismissable: bool`, `created_at: str`, `is_read: bool`.
- `CapsuleNotificationQueue(min_width: int = 160, max_width: int = 440, char_width_px: int = 7)`:
  - `push(title: str, message: str = "", icon: str = "🔔", action_label: str = "View", notification_id: str | None = None) -> CapsuleNotification`: Adds or updates a notification.
  - `dismiss(notification_id: str) -> CapsuleNotification | None`: Dismisses notification by ID.
  - `clear() -> None`: Clears all notifications.
  - `mark_read(notification_id: str) -> None`: Marks a specific notification as read.
  - `mark_all_read() -> None`: Marks all queued notifications as read.
  - `list_all() -> list[CapsuleNotification]`: Returns all notifications.
  - `unread_count: int`: Returns number of unread notifications.
  - `has_unread: bool`: Returns `True` if any unread notification exists.
  - `compute_popup_width(item: CapsuleNotification) -> int`: Returns width for 3-second popup pill clamped between 200px and 360px.

---

## 6. Implemented Module Specifications (Phase 4)

### `plus_ultra.services`
- `VALID_STATUSES`: `("Pending", "In Progress", "Completed", "Overdue")`
- `VALID_CRITICAL_LEVELS`: `("High", "Medium", "Low")`
- `VALID_PACE_LEVELS`: `("Long-term", "Short-term")`
- `TaskService(task_repo: TaskRepository, category_repo: CategoryRepository)`:
  - `create_task(title: str, category_id: str | None = None, description: str = "", due_date: str | None = None, status: str = "Pending", task_label: str = "College", critical_level: str = "Medium", pace_level: str = "Short-term", is_google_task: bool = False) -> Task`: Pure business logic validation; rejects whitespace-only titles, invalid statuses, or non-existent categories.
  - `get_task(task_id: str) -> Task | None`: Retrieves active task.
  - `update_task(task_id: str, ...) -> Task | None`: Validates updates and persists.
  - `toggle_status(task_id: str) -> Task | None`: Cycles status between `Pending` and `Completed`.
  - `soft_delete_task(task_id: str) -> bool`: Soft-deletes task and cascades to reminders.
  - `list_tasks(category_id: str | None = None, status: str | None = None, critical_level: str | None = None, search_query: str | None = None) -> list[Task]`: Multi-criteria querying and case-insensitive text search.
- `CategoryService(category_repo: CategoryRepository)`:
  - `create_category(name: str, color: str = "#4a5568") -> Category`: Validates and creates a new category.
  - `get_category(category_id: str) -> Category | None`: Retrieves category by ID.
  - `update_category(category_id: str, name: str, color: str) -> Category | None`: Updates category name and color.
  - `soft_delete_category(category_id: str) -> bool`: Soft deletes category and nullifies `tasks.category_id` in linked tasks.
  - `list_active() -> list[Category]`: Lists active categories alphabetically.

### `plus_ultra.ui.panel`
- `TaskDialog(parent, categories, task=None, on_save=None, theme=THEME)`:
  - Modal dialog for task creation and editing.
  - Fields: Title, Category combobox, Priority combobox, Pace combobox, Due Date entry, Description/Notes text area.
  - Validates title non-empty and invokes `on_save(data)`.
- `DashboardPanel(parent: tk.Tk, task_service: TaskService, category_service: CategoryService, notification_queue: CapsuleNotificationQueue, on_notifications_cleared: Callable[[], None] | None = None, theme: CapsuleTheme = THEME)`:
  - 3-column workspace window:
    - **Column 1 (Left Sidebar)**: 6 navigation tabs (`Tasks`, `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`) + pinned Settings.
    - **Column 2 (Center Panel)**: Option A styled `ttk.Treeview` task list, search bar, status pills (`All`, `Pending`, `Completed`), priority filter combobox, double-click to edit, right-click context menu (toggle status, edit, soft delete), "+ New Task", "+ Category".
    - **Column 3 (Right Sidebar)**: Notification panel with "Mark All Read" and "Clear", wired to `CapsuleNotificationQueue` and capsule bell indicator.
  - `show() -> None`: Displays dashboard window and refreshes data.
  - `hide() -> None`: Hides dashboard window via `withdraw()`.
  - `toggle() -> None`: Toggles visibility between normal and withdrawn.

---

## 7. Implemented Module Specifications (Phase 5)

### `plus_ultra.desktop` (Desktop Notifications)
- `send_desktop_notification(title: str, message: str = "", urgency: str = "normal", timeout_ms: int = 5000, app_name: str = config.APP_NAME) -> bool`:
  - Dispatches native desktop notifications using `notify-send` with an argument list and `shell=False`.
  - Verifies executable availability with `shutil.which`.
  - Catches `SubprocessError` and `OSError` without crashing.
  - Alias: `notify = send_desktop_notification`.

### `plus_ultra.services` (Reminder Management)
- `ReminderService(reminder_repo: ReminderRepository, task_repo: TaskRepository)`:
  - `create_reminder(task_id: str, remind_at: str) -> Reminder`: Validates task existence, active state, and non-empty timestamp.
  - `get_due_reminders(before_timestamp: str) -> list[tuple[Reminder, Task]]`: Queries due reminders, joins with parent active tasks, and filters out already fired or deleted items.
  - `mark_fired(reminder_id: str) -> None`: Records firing in `reminder_fires`.
  - `is_fired(reminder_id: str) -> bool`: Checks if reminder already fired on this device.
  - `soft_delete_reminder(reminder_id: str) -> bool`: Soft-deletes a reminder.

### `plus_ultra.scheduler` (Background Poller)
- `DEFAULT_POLL_INTERVAL_S: float = 10.0`
- `ReminderScheduler(reminder_service, poll_interval_s=10.0, on_reminder_due=None, desktop_notify=True, now_provider=None, db_path=None, conn_factory=None)`:
  - Background daemon thread executing off the Tkinter UI event loop.
  - Thread-isolated SQLite WAL connection to prevent concurrency errors.
  - Producer-consumer dispatch: fires `notify-send` desktop popups and delivers in-app alerts via `on_reminder_due(task, reminder)`.
  - `tick(now_iso: str | None = None, service: ReminderService | None = None) -> list[tuple[Reminder, Task]]`: Evaluates due reminders, invokes notifiers, and marks records fired atomically.
  - `start() -> None`: Starts daemon thread loop.
  - `stop(timeout: float = 2.0) -> None`: Sets `threading.Event` cancellation flag and cleanly joins the thread.
  - `is_running: bool`: Returns `True` if background worker thread is active.

---

## 8. Implemented Module Specifications (Workspace Tabs & Schema v2)

### `plus_ultra.db` (Schema Migration 2)
- `CURRENT_SCHEMA_VERSION: int = 2`
- Tables added:
  - `code_items`: `(id, category, title, content, language, difficulty, is_done, url, notes, created_at, updated_at, synced_at, is_deleted)`
  - `courses`: `(id, title, platform, instructor, total_modules, completed_modules, url, notes, created_at, updated_at, synced_at, is_deleted)`
  - `ideas_doubts`: `(id, kind, title, description, tech_stack_or_ref, status, created_at, updated_at, synced_at, is_deleted)`
  - `opportunities`: `(id, title, organization, kind, url, deadline, status, notes, created_at, updated_at, synced_at, is_deleted)`
  - `quick_links`: `(id, name, target_uri, category, click_count, created_at, updated_at, synced_at, is_deleted)`
- `seed_demo_workspace_data(conn: sqlite3.Connection) -> None`: Populates rich initial sample items across all tabs if tables are empty.

### `plus_ultra.services`
- `CodeService`:
  - `list_items(category=None, search_query=None) -> list[CodeItem]`
  - `create_item(...) -> CodeItem`
  - `update_code_item(item_id: str, ...) -> bool`
  - `toggle_done(item_id: str) -> bool`
  - `soft_delete_item(item_id: str) -> bool`
- `CourseService`:
  - `list_courses(platform=None, search_query=None) -> list[Course]`
  - `create_course(...) -> Course`
  - `update_course(course_id: str, ...) -> bool`
  - `increment_module(course_id: str) -> bool`
  - `soft_delete_course(course_id: str) -> bool`
- `IdeaDoubtService`:
  - `list_items(kind=None, status=None, search_query=None) -> list[IdeaDoubt]`
  - `create_item(...) -> IdeaDoubt`
  - `update_idea_doubt(item_id: str, ...) -> bool`
  - `advance_status(item_id: str) -> bool`: Cycles through standard stages or resolves doubts.
  - `soft_delete_item(item_id: str) -> bool`
- `OpportunityService`:
  - `list_opportunities(kind=None, status=None, search_query=None) -> list[Opportunity]`
  - `create_opportunity(...) -> Opportunity`
  - `update_opportunity(opp_id: str, ...) -> bool`
  - `advance_status(opp_id: str) -> bool`: Advances Saved -> Applied -> In Progress -> Accepted.
  - `soft_delete_opportunity(opp_id: str) -> bool`
- `QuickLinkService`:
  - `list_links(category=None, search_query=None) -> list[QuickLink]`
  - `create_link(name: str, target_uri: str, category: str) -> QuickLink`
  - `update_quick_link(link_id: str, ...) -> bool`
  - `record_click(link_id: str) -> bool`: Increments click count.
  - `soft_delete_link(link_id: str) -> bool`

### `plus_ultra.ui`
- `CapsuleGeometry`: Doubled dimensions `width=320, height=72, radius=36, top_offset=16`.
- `FloatingWidget`: Double size with 56-point beam, orange bell indicator, and dynamic hide/show coordination.
- `DashboardPanel`:
  - Card-based modern UI replacing table views.
  - Explicit Create, Edit, and Delete modal workflows with fixed-bottom confirmation action bars.
  - Task date and time pickers with optional desktop notification scheduling.
  - Visibility coordination (`on_open`, `on_close`) withdrawing floating pill while open and restoring on close.

---

## 9. Modular Architecture Subpackages (Architectural Refactoring)

All core modules adhere strictly to single-responsibility decomposition with `<= 500` lines per file.

### `plus_ultra.database`
Subpackage encapsulating SQLite engine, migrations, and seed data:
- `connection.py`:
  - `get_connection(db_path: Path | None = None) -> sqlite3.Connection`: Configures WAL mode, 5s busy timeout, foreign keys, row factory.
  - `transaction(conn: sqlite3.Connection) -> ContextManager[sqlite3.Cursor]`: ACID transaction manager with commit/rollback.
- `schema.py`:
  - `CURRENT_SCHEMA_VERSION: int = 2`
  - `SCHEMA_V1_STATEMENTS: tuple[str, ...]`
  - `SCHEMA_V2_STATEMENTS: tuple[str, ...]`
- `migrations.py`:
  - `get_schema_version(conn: sqlite3.Connection) -> int`
  - `set_schema_version(conn: sqlite3.Connection, version: int) -> None`
  - `init_db(conn: sqlite3.Connection) -> None`
- `seeds.py`:
  - `seed_demo_workspace_data(conn: sqlite3.Connection) -> None`

### `plus_ultra.repositories`
Subpackage containing isolated single-table data access repositories:
- `base.py`: `_now_utc() -> str`
- `CategoryRepository`: CRUD and soft-deletes for categories.
- `TaskRepository`: CRUD, soft-deletes, and filter queries for tasks.
- `ReminderRepository`: CRUD and due-reminder queries.
- `AppStateRepository`: Runtime key-value state persistence (`get_state`, `set_state`).
- `CodeRepository`: CRUD, language filter, and done-toggle for code items.
- `CourseRepository`: CRUD, platform filter, and module progress increments.
- `IdeaDoubtRepository`: CRUD, kind/status filters, and lifecycle advancement.
- `OpportunityRepository`: CRUD, kind/status filters, and application pipeline advancement.
- `QuickLinkRepository`: CRUD, category filter, and click count recording.

### `plus_ultra.services`
Subpackage providing decoupled business logic:
- `TaskService`: Validates constraints, status transitions, search queries.
- `CategoryService`: Manages categories, cascades soft-delete task nullifications.
- `ReminderService`: Enforces reminder creation constraints and atomic firing records.
- `CodeService`: Code snippet search, category filtering, completion toggling.
- `CourseService`: Course module progress incrementation and tracking.
- `IdeaDoubtService`: Idea stage progression and doubt resolution.
- `OpportunityService`: Application pipeline status progression.
- `QuickLinkService`: Link registry and access count updates.

### `plus_ultra.network`
Lightweight network status detection and non-blocking probe utility:
- `is_network_online(host: str = "1.1.1.1", port: int = 53, timeout: float = 1.0) -> bool`: Probes Cloudflare/Google public DNS via lightweight socket connection with zero external dependencies.
- `NetworkStatusMonitor`: Thread-safe background connectivity probe engine using pure Python FIFO queue (`probe_async()`, `get_result() -> bool | None`).

### `plus_ultra.ui.icons`
Pure Tkinter image caching and downsampling utility:
- `find_icon_path(icon_name: str) -> Path | None`: Discovers asset files across `resources/icons`, `resources/base`, `resources/folders`, and `resources/tabs`.
- `get_icon(icon_name: str = "fallback", size: int = 24, master: tk.Misc | None = None) -> tk.PhotoImage | None`: Returns a cached, subsampled `PhotoImage` tied to the active interpreter root with zero third-party dependencies.
- `clear_icon_cache() -> None`: Clears in-memory image references.

### `plus_ultra.datetime_utils`
Timezone-aware datetime parsing utility:
- `parse_flexible_datetime(val: str | datetime) -> datetime`: Parses naive local datetimes, ISO 8601 with Z or timezone offsets, space-separated dates (`"YYYY-MM-DD HH:MM"`), and date-only strings into timezone-aware datetimes for reliable scheduling comparisons.

### `plus_ultra.ui.components`
Reusable presentation components:
- `DateTimePicker`: Interactive date and time picker featuring `⚡ Now` automatic timestamp insertion, date presets (`Today`, `Tomorrow`, `+3 Days`, `+1 Wk`), time presets (`09:00`, `12:00`, `15:00`, `18:00`, `21:00`, `23:59`), and step adjusters (`-1d`, `+1d`).
- `CapsulePopupPill`: Transient rounded popup pill appearing directly below the floating capsule for temporary alert banners (configurable duration, XShape masked).
- `TaskCard`: Standalone card widget presenting an individual task with status button (`[Done]`/`[Pending]`), category chip, priority badge, pace level, overdue highlighting, and contextual Edit/Delete actions.
- `ScrollableFrame`: Canvas-backed scrollable container with mousewheel bindings.
- `Sidebar`: Draggable navigation sidebar supporting manual cursor drag-and-drop tab reordering, 80px enlarged Settings button on bottom-left, and renamed tabs (`Tasks`, `Code c-p`, `DSA Tracker`, `Courses`, `PS/I`, `Opportunities`, `Quick Links`).
- `NotificationsPanel`: Focused notification alerts stream with Mark All Read, Clear, and clean unread status list.

### `plus_ultra.ui.floating`
Floating capsule presence:
- `FloatingWidget`: Top-center hovering presence with trailing hover beam, dynamic width expansion on unread alerts, integrated `CapsulePopupPill`, and right-side network status indicator dot (`#10b981` online, `#ef4444` offline, toggleable via settings).

### `plus_ultra.ui.dialogs`
Centering modal dialogs with generous dimensions (`680x720`, `680x680`, `640x620`):
- `center_modal(dialog: tk.Toplevel, parent: tk.Misc, width: int, height: int)`
- `TaskDialog`: Supports interactive `DateTimePicker`, priority/pace selectors, and inline category creation directly inside the category dropdown (`+ Add New Category...` and `+` button).
- `OpportunityDialog`: Supports interactive `DateTimePicker` in date-only mode for deadlines.
- `CodeDialog`: Offers predefined language combobox selections (`Python`, `JavaScript`, `TypeScript`, `C`, `C++`, `Java`, `Rust`, `Go`, `Bash`, `SQL`, etc.).
- `CourseDialog`: Course editor with cleaned platform options (`University`, `YouTube`, `Other`).
- `IdeaDialog`, `QuickLinkDialog`, `CategoryDialog`.

### `plus_ultra.ui.views`
Decoupled workspace tab views with 2x card sizing and clean badges:
- `TasksView` (`Tasks`): Streamlined view with category filters, priority filters, search bar, and full CRUD utilizing `TaskCard`.
- `CodeView` (`Code c-p`): Code snippets workspace with language filters and one-click clipboard copy.
- `DSAView` (`DSA Tracker`): Dedicated DSA Problem Tracker view in the main workspace.
- `IdeasView` (`PS/I`): Dual-subtab view featuring dedicated `[ Project Ideas ]` and `[ Concept Doubts ]` tables, each with contextual creation actions (`+ Add Idea` / `+ Add Doubt`).
- `CoursesView` (`Courses`): Platform filter buttons (`All`, `University`, `YouTube`, `Other`).
- `OpportunitiesView`, `QuickLinksView`.
- `SettingsView`: Preferences & diagnostics with Always-on-top toggle, Network status indicator toggle, and demo data reseed.

### `plus_ultra.ui.geometry`
Mathematical capsule coordinate calculations:
- `generate_capsule_points(width, height, radius, steps_per_corner=12) -> list[int]`
- `generate_perimeter_path(width, height, radius, total_points=56) -> list[tuple[float, float]]`

### `.scripts` Standalone Utilities
- `clear_db.py`: `clear_database(conn, tables, hard_delete, clear_app_state, vacuum)` - Clears database tables cleanly with hard DELETE or soft delete (`is_deleted = 1`) and `--force` support.
- `seed_data.py`: `seed_demo_workspace_data(conn, force)`, `unseed_demo_workspace_data(conn, hard_delete)` - Full workspace demo population and selective removal.
- `notify.py`: `dispatch_notification(title, message, delay_seconds, urgency)` - Desktop notification dispatcher supporting instant popup or delayed countdown delivery.

