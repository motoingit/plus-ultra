# Build  for `PLUS-ULTRA`

A floating desktop assistant for Ubuntu (GNOME, Wayland): an always-on-top widget, a task and reminder panel, a tray icon, and desktop notifications. This is a PBL project, so the code must also make OS and DBMS concepts visible.

This file is the source of truth for **what to build and in what order**. `AGENTS.md` and `.agents/rules/` say **how to behave**. If they conflict, stop and ask.

# Agent Protocol (read before every phase)

The user (Moto) is vibecoding under supervision. Work in **phases**. Each phase ends at a **gate** where you stop.

## **Before writing code for any phase**
1. Read `AGENTS.md` which is mapping to gemini.md and `.agents/rules/` .
2. Reply with: the files you will create or modify, any new dependency (none unless the phase lists it), your assumptions, and any questions. **Wait for "go".**

## **After writing code for any phase**
1. Update the `.docs/progress-log.md` for Changes as it is saving progress with (Phase-no, phase todolist, phase issues and its status, and Important points)
2. Suggest git add and commit command to run in response

## **While implementing:**
- Do only the current phase. Do not build ahead.
- For `config.py`, `db.py`, `repository.py` and `services.py`: write the pytest tests also to test.
- Never add a dependency, change the stack, or edit `pyproject.toml` dependency lists without approval (see `init-and-techstack.md`).
- Do not edit `.agents/workflows/initial-plan.md`, `.agents/` or `.my/` without asking when sugestion.

# Architecture Rules (non-negotiable)

Think of a restaurant: the UI is the waiter (talks to the customer), `services` is the kitchen (the logic), `repository` is the pantry clerk (the only one who touches storage). The waiter never walks into the pantry.

| Layer | May import | Must not |
|---|---|---|
| `ui/*` | `services`, `models`, `ui.theme` | import `sqlite3`, `db`, or `repository` |
| `services` | `repository`, `models` | import `tkinter` |
| `repository` | `db`, `models` | contain UI or business rules; it is the only place with SQL |
| `db` | `sqlite3`, `config` | contain queries for features |
| `desktop` | `subprocess`, `fcntl`, `pathlib` | be called from `repository` |

Concurrency rules (Tk is a single-threaded event loop, like a game loop; touching widgets from another thread is a data race):
1. **Tk widgets are touched only on the main thread.**
2. Other threads (the tray) send commands through a `queue.Queue`. The Tk loop drains it with `root.after(100, ...)`.
3. Reminders use `root.after()` ticks, not a polling thread.
4. `subprocess` is called only from `desktop.py`, always with an argument list.
5. Timestamps are stored in UTC as ISO-8601 text and converted to local time only at display.

# GUI limitations (Wayland / XWayland)

Tkinter is an X11 toolkit. On Wayland it runs through XWayland. Treat these as facts to test, not assumptions:

- **Always-on-top (`-topmost`)** usually works against other XWayland windows. It may not stay above native Wayland windows (Files, GNOME Terminal). Must be tested in Phase 2.
- **Window position:** `geometry("+x+y")` may be ignored or approximate. Save the last position and verify it restores.
- **Transparency:** `-alpha` needs a compositor. True per-pixel shaped windows are unreliable. Fake a "glow" by drawing on a `Canvas` inside a borderless window and animating colors with `after()`.
- **Borderless (`overrideredirect(True)`)** windows can lose keyboard focus on some setups. The floating widget should be click and drag only. Text input happens in the panel, which has normal window decorations.
- **HiDPI:** fractional scaling can make Tk look blurry. Check `tk scaling` if it does.
- **Tray:** GNOME has no legacy tray. Ubuntu ships the AppIndicator extension enabled by default, and pystray must use its AppIndicator backend.
- **Fallbacks if a limit blocks the app:** present options under `ask-before-assuming.md`. Do not switch toolkits or add X11 hacks on your own.

# Target Layout (modules are created in the phase noted)

```
src/plus_ultra/
├── __init__.py
├── main.py          # P1: main(): args, logging, lock, db, UI. Console script target.
├── config.py        # P1: XDG paths (data, state, runtime; config in P1b), constants
├── settings.py      # P1b: user settings overrides, atomic write, defaults overlay
├── resources/
│   ├── metadata.json         # P1b: static app metadata
│   └── default-settings.json # P1b: default settings
├── db.py            # P3: connect, PRAGMAs, migrations, transaction() helper
├── models.py        # P3: dataclasses Task, Category, Reminder
├── repository.py    # P3: all SQL (sets updated_at, soft deletes)
├── services.py      # P4: TaskService, ReminderService
├── scheduler.py     # P5: reminder tick
├── tray.py          # P5: pystray in a worker thread
├── desktop.py       # P5-6: notify-send, single-instance lock, autostart
├── sync.py          # P7: Supabase differential sync worker (off Tk thread)
└── ui/
    ├── __init__.py
    ├── theme.py     # P2: colors, fonts, glow palette
    ├── floating.py  # P2: the floating widget
    ├── panel.py     # P4: task list and add/edit dialogs
    └── splash.py    # P6: startup log window
tests/               # test_config.py, test_settings.py, test_db.py, test_repository.py, test_services.py, ...
```

Never name a module after a standard-library module (`platform`, `queue`, `code`, `logging`, `signal`).

CLI flags (via `argparse` in `main.py`), added when needed: `--smoke-test` (P4), `--install-autostart` and `--uninstall-autostart` (P6), `--import-json PATH` (P8).

# Future Requirements & Architectural Constraints (Design for now, build later)

1. **Mobile App Compatibility**: A mobile app may be built later on the same backend (Supabase/Postgres). Keep column types portable and enforce rules with CHECK and FOREIGN KEY constraints, not only in Python.
2. **Offline-First & Thread Separation**: The app works fully offline and online. The UI and the task/reminder services never use the network. All writes go to local SQLite first. Only a dedicated sync module (Phase 7) touches the network, and it runs off the Tk main thread.
3. **Cloud Sync Strategy**: Cloud sync like Google Tasks (last-write-wins by `updated_at`) comes in Phase 7. Real-time co-editing is out of scope.
4. **Phase 3 Schema Rules**:
   - UUID text primary and foreign keys.
   - `created_at`, `updated_at`, `synced_at`, `is_deleted` on synced tables only (`tasks`, `categories`, `reminders`).
   - Soft deletes only:
     - Normal queries filter `is_deleted = 0`.
     - Soft-deleting a task soft-deletes its reminders in the same transaction.
     - Soft-deleting a category sets `tasks.category_id` to NULL in the same transaction.
     - Replaced table UNIQUE on `categories.name` with partial unique index `idx_categories_name_active ON categories(name) WHERE is_deleted = 0`.
     - Scheduler query requires both reminder `is_deleted = 0` AND parent task `is_deleted = 0`.
   - Only the repository layer sets `updated_at`.
5. **Local Reminder Fired State**: Reminder fired state is local-only (each device notifies for itself). Store it in a separate local-only table `reminder_fires(reminder_id TEXT PRIMARY KEY REFERENCES reminders(id) ON DELETE CASCADE, fired_at TEXT NOT NULL)`, not as a column on `reminders`. Update the Phase 5 scheduler query and the Phase 3 index to match.
6. **Zero Early Network Dependencies**: No sync code, network libraries, or new dependencies before Phase 7, and only with user approval.

# Data Model (SQLite)

Created in Phase 3. Versioned with `PRAGMA user_version` and an ordered list of migrations in `db.py`.

```sql
CREATE TABLE categories (
    id         TEXT PRIMARY KEY,  -- UUID text
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL,     -- UTC ISO-8601
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1))
);

-- Active category name uniqueness (allows reusing name of soft-deleted category)
CREATE UNIQUE INDEX idx_categories_name_active ON categories(name) WHERE is_deleted = 0;

CREATE TABLE tasks (
    id          TEXT PRIMARY KEY, -- UUID text
    title       TEXT NOT NULL CHECK (length(title) > 0),
    notes       TEXT NOT NULL DEFAULT '',
    category_id TEXT REFERENCES categories(id) ON DELETE SET NULL,
    status      TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done')),
    created_at  TEXT NOT NULL,    -- UTC ISO-8601
    updated_at  TEXT NOT NULL,
    synced_at   TEXT,
    is_deleted  INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1))
);

CREATE TABLE reminders (
    id         TEXT PRIMARY KEY,  -- UUID text
    task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at  TEXT NOT NULL,     -- UTC ISO-8601
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at  TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1))
);

-- Local-only table: reminder fired state is device-specific
CREATE TABLE reminder_fires (
    reminder_id TEXT PRIMARY KEY REFERENCES reminders(id) ON DELETE CASCADE,
    fired_at    TEXT NOT NULL     -- UTC ISO-8601
);

-- Partial index: the scheduler queries active reminders
CREATE INDEX idx_reminders_due ON reminders(remind_at) WHERE is_deleted = 0;

-- machine-written state only (widget_x, widget_y, last_synced_at); user preferences live only in user-settings.json
CREATE TABLE app_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Connection setup: `PRAGMA foreign_keys = ON;` and `PRAGMA journal_mode = WAL;` on every connection. All queries are parameterized.

# Phases

### Phase 0: Repo hygiene (Moto does this, no agent) - COMPLETED
- [x] Replace the four rule files and `pyproject.toml` with the corrected versions.
- [x] Protect user private space by adding `.my/` to `.gitignore`.
- [x] Verify package build and run with `uv run plus-ultra`.
- [x] Stage baseline project files and create initial Git commit on `main`.

### Phase 1: Foundation
**Build:** `config.py` (data dir `$XDG_DATA_HOME/plus-ultra`, state dir `$XDG_STATE_HOME/plus-ultra`, falling back to `~/.local/share` and `~/.local/state`; create dirs with mode `0o700`), logging to `launcher.log` in the state dir, `main.py` with `main()` that logs startup and exits. `uv add --dev ruff pytest`.
**Tests:** path resolution with and without the env vars (use `monkeypatch`), directory permissions `0o700`.
**Gate:** `uv run plus-ultra` writes startup lines to `launcher.log` and exits 0. ruff and pytest pass.
**Concepts:** XDG base directories, file permissions.

### Phase 1b: Secrets, metadata, settings
**Secrets Rules:**
- Moto creates `.env` in project root. Agent NEVER reads, prints, creates, or edits `.env`.
- When a variable is needed, add its NAME with a placeholder to `.env.sample` and ask Moto to set the real value.
- `.gitignore` must contain `.env` and `.env.*`, plus `!.env.sample`.
- Only Supabase URL and anon (publishable) key may ever go in `.env`. Never service_role key.
- Nothing reads `.env` before Phase 7. No `python-dotenv` yet.

**Metadata:**
- Add `src/plus_ultra/resources/metadata.json` with static fields only: `app_name`, `display_name`, `company`, `description`. The version is NOT stored in it.
- `config.py` reads version with `importlib.metadata.version("plus-ultra")`.
- Load the JSON using `importlib.resources`.

**Settings:**
- Propose the keys for `default-settings.json` and wait for Moto's approval before creating it.
- Add `src/plus_ultra/resources/default-settings.json` (ships with app, read-only).
- Add `src/plus_ultra/settings.py` (no tkinter, no network, stdlib only) for user overrides:
  - Add config dir `$XDG_CONFIG_HOME/plus-ultra/user-settings.json` (default `~/.config/plus-ultra/`) to `config.py`.
  - Created on the first change and stores only overridden keys (like VS Code `settings.json`).
  - Effective settings are defaults overlaid with user file, with nested keys merged.
  - Unknown keys or wrong types: ignore that key and log a warning.
  - Invalid JSON: rename file to `user-settings.json.bad-<timestamp>`, fallback to defaults, log error, never crash.
  - Atomic writes: write a temp file in the same folder, then `os.replace`. File mode `0o600`, folder mode `0o700`.
  - Reset: remove one key's override, or delete file to restore factory defaults.
  - Load at startup, plus explicit `reload()` function. No file watching yet.
  - Split: user preferences live ONLY in this JSON. Machine-written state (`widget_x`, `widget_y`, `last_synced_at`) lives ONLY in SQLite `app_state` table (local-only). A value lives in exactly one of them.

**Tests:** happy path, edge cases (corrupt JSON, wrong types, missing overrides, atomic write interrupt simulation).
**Gate:** all tests pass, settings merge and write atomically.
**Concepts:** atomic file replacement (`os.replace`), configuration layering, defensive parsing.

### Phase 2: Wayland spike (go / no-go)
**Build:** `ui/theme.py` and `ui/floating.py`: a borderless, ~90px circular-looking widget (dark rounded canvas), `-topmost`, drag to move, a slow color pulse via `after()`, click toggles a placeholder state. Runs from `main.py`. Position is kept in memory only (persistence arrives in Phase 3).
**Moto tests manually and records results in the log:** stays above a browser? above Files or GNOME Terminal? drag works? survives switching workspaces? pulse smooth? Does it look blurry?
**Gate:** Report what works and what doesn't, record observations in `.docs/progress-log.md`, and proceed (don't block on native Wayland window layering).
**Concepts:** event loop vs threads, window stacking, compositor.

### Phase 3: Database layer
**Build:** `db.py`, `models.py`, `repository.py` per Data Model section. Migration runner using `user_version`. A `transaction()` context manager that commits on success and rolls back on error. CRUD for tasks, categories, reminders, app_state.
- Implement UUID text PK/FKs.
- Synced tables include `created_at`, `updated_at`, `synced_at`, `is_deleted`.
- Implement soft deletes:
  - Soft-deleting a task soft-deletes its reminders in the same transaction.
  - Soft-deleting a category sets `tasks.category_id` to NULL in the same transaction.
  - Normal queries filter `is_deleted = 0`.
  - Unique active category name index `idx_categories_name_active` allows reusing name of soft-deleted category.
  - Only repository layer sets `updated_at`.
- Implement `reminder_fires` table for local fired state.
- Wire widget position save and restore through a small service call or a direct app_state read in `main.py` (not from `ui/`).
**Tests (first):** constraints (empty title rejected, bad status rejected), `ON DELETE CASCADE` and `SET NULL`, rollback leaves no partial rows, migrations are idempotent, `EXPLAIN QUERY PLAN` shows `idx_reminders_due` is used; test soft-deleting task cascades soft-delete to its reminders in transaction; test unique active category name allows reusing soft-deleted category name; test soft-deleting category sets tasks.category_id to NULL in transaction; test scheduler query excludes reminders of soft-deleted tasks.
**Gate:** all tests pass; the widget reopens at its last position.
**Concepts:** ACID, primary and foreign keys, normalization (3NF), indexes, migrations, soft deletes.

### Phase 4: Services and panel UI
**Build:** `services.py` (`TaskService`: add, edit, set status, soft delete, list by category or status). `ui/panel.py`: a normal `Toplevel` with a task list (`ttk.Treeview`), add and edit dialogs, category filter, status toggle. Clicking the widget opens or closes the panel. Add the `--smoke-test` flag: build the UI, `after(1500, root.destroy)`, exit 0.
**Tests:** `test_services.py` against a temp database.
**Gate:** Moto adds three tasks, restarts, and they persist. `xvfb-run -a uv run plus-ultra --smoke-test` exits 0.
**Concepts:** layering (MVC-style), separation of concerns.

### Phase 5: Reminders, notifications, tray
**Decision D1 (needs Moto's approval before coding):** pystray's AppIndicator backend needs system bindings that a uv-managed Python venv may not see. The agent first runs a **tray spike** (just an icon and a Quit item) and reports whether it appears in the GNOME top bar. If not, present these options:
1. Install the AppIndicator typelib and PyGObject through apt, and create the venv from the system Python 3.12 with system site packages. Likely works; touches the environment.
2. Build PyGObject inside the venv with the apt build dependencies. Heavier setup.
3. Drop the tray. The floating widget and notifications are enough. Requires approving a stack change.

Not verified which works on Moto's machine. Do not pick one without asking. Moto decides after the tray spike.

**Build:** `scheduler.py` (a tick every `REMINDER_POLL_MS = 10_000` that asks the service for due, unfired reminders by joining `reminders` where `is_deleted = 0` with `tasks` where `tasks.is_deleted = 0`, excluding reminders in `reminder_fires`, notifies, and records firing in `reminder_fires` inside one transaction). `desktop.notify()` using `notify-send` with an argument list and a timeout. `tray.py` with `run_detached()` and a command queue drained on the Tk thread (menu: Show, Add task, Quit). Add `pystray` and `Pillow` with `uv add` once D1 is settled.
**Tests:** scheduler logic with a fake clock and fake notifier; test scheduler query excludes reminders of soft-deleted tasks; no real `notify-send` in tests.
**Gate:** a reminder set 1 minute ahead fires with the panel closed, exactly once; the tray menu works; Quit exits cleanly.
**Concepts:** threads vs event loop, producer-consumer queue, subprocess, atomic mark-as-fired.

### Phase 6: Robustness and startup
**Decision D2 (needs approval):** `~/My-Drive` may not be mounted at login. If autostart fails for that reason, options are: copy the project to a local path, or `uv tool install .` so the launcher lives in `~/.local/bin`. The second changes the launch command, so it needs approval.
**Build:**
- Single instance: `fcntl.flock` on `$XDG_RUNTIME_DIR/plus-ultra.lock` (fallback to the state dir). A second launch exits with a clear message.
- Graceful shutdown on `SIGINT` and `SIGTERM`: stop the tray, close the database.
- `--install-autostart` and `--uninstall-autostart`: write or remove `~/.config/autostart/plus-ultra.desktop` with resolved absolute paths.
- `ui/splash.py`: a small log window showing startup steps (`[1/4] Paths`, `[2/4] Database`, `[3/4] Tray`, `[4/4] Ready`), auto-closing after about 3 seconds. Steps are also written to `launcher.log`.
**Gate:** a second launch is refused; `kill` shuts the app down cleanly with no stack trace; after logout and login the app starts by itself.
**Concepts:** file locking, signals, process lifecycle, XDG autostart.

### Phase 7: Supabase sync
**Prerequisites:**
- Supabase Auth login configured.
- Row Level Security (RLS) policies enforced per user on Supabase.
- Remote schema created by SQL that Moto runs personally.
- Supabase client dependency added only after Moto's approval.

**Build:**
- `sync.py`: Supabase online differential sync worker (runs off the Tk main thread). Compares local changes (`updated_at > last_synced_at`) with remote Supabase, pushes local mutations, pulls remote mutations (last-write-wins by `updated_at`), updates `last_synced_at` in local SQLite `app_state` table.
**Tests:** differential sync logic with mock Supabase responses, last-write-wins resolution, offline queue, failure handling.
**Gate:** sync tests pass, local mutations push and remote mutations pull without blocking the Tk main loop.
**Concepts:** differential synchronization, conflict resolution (LWW), thread isolation, network resilience.

### Phase 8: Polish and report
**Build:** finish `ui/theme.py` (the glow), README (setup with `uv sync`, how to run, how to autostart), and `--import-json PATH` for old app data (Moto supplies sample JSON). Optional backlog from the old app: clipboard and quick-links categories, color-coded task states.
**Report:** `.docs/concepts.md` mapping each OS and DBMS concept to the file and function where it appears (XDG paths in `config.py`, atomic settings in `settings.py`, locking in `desktop.py`, ACID in `db.transaction`, indexes in the migration, sync in `sync.py`, and so on).
**Gate:** a fresh clone, `uv sync` and `uv run plus-ultra` work end to end.

# Moto's Supervision Checklist (every gate)

1. Read the diff. If you cannot explain a function, ask the agent to explain it before accepting.
2. Run the app yourself. Agent-reported success is not verification, especially for Wayland, tray and notifications.
3. Run `uv run ruff check . && uv run pytest`.
4. `git commit -m "phase-N: <what>"`.
5. Paste the agent's draft into `.docs/progress-log.md`.
6. Start the next phase in a **fresh chat** so context stays small. The log file carries the memory.

# Definition of Done

- All phase gates passed and committed.
- `uv sync && uv run plus-ultra` works on a fresh clone.
- Floating widget, panel, tray, reminders and notifications work on Wayland, or the limits are documented with the decisions taken.
- `ruff` and `pytest` are clean.
- `.docs/concepts.md` maps every OS and DBMS concept to code.
- No secrets or personal data committed (run the `finish-project-security` skill).