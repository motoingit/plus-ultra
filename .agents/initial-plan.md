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
├── config.py        # P1: XDG paths (data, state, runtime), constants
├── db.py            # P3: connect, PRAGMAs, migrations, transaction() helper
├── models.py        # P3: dataclasses Task, Category, Reminder
├── repository.py    # P3: all SQL
├── services.py      # P4: TaskService, ReminderService
├── scheduler.py     # P5: reminder tick
├── tray.py          # P5: pystray in a worker thread
├── desktop.py       # P5-6: notify-send, single-instance lock, autostart
└── ui/
    ├── __init__.py
    ├── theme.py     # P2: colors, fonts, glow palette
    ├── floating.py  # P2: the floating widget
    ├── panel.py     # P4: task list and add/edit dialogs
    └── splash.py    # P6: startup log window
tests/               # test_config.py, test_db.py, test_repository.py, test_services.py, ...
```

Never name a module after a standard-library module (`platform`, `queue`, `code`, `logging`, `signal`).

CLI flags (via `argparse` in `main.py`), added when needed: `--smoke-test` (P4), `--install-autostart` and `--uninstall-autostart` (P6), `--import-json PATH` (P7).

# Data Model (SQLite)

Created in Phase 3. Versioned with `PRAGMA user_version` and an ordered list of migrations in `db.py`.

```sql
CREATE TABLE categories (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL CHECK (length(title) > 0),
    notes       TEXT NOT NULL DEFAULT '',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    status      TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done')),
    created_at  TEXT NOT NULL,   -- UTC ISO-8601
    updated_at  TEXT NOT NULL
);

CREATE TABLE reminders (
    id        INTEGER PRIMARY KEY,
    task_id   INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    remind_at TEXT NOT NULL,     -- UTC ISO-8601
    fired_at  TEXT               -- NULL until the notification is sent
);

-- Partial index: the scheduler only ever asks "what is due and not yet fired?"
CREATE INDEX idx_reminders_due ON reminders(remind_at) WHERE fired_at IS NULL;

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL          -- e.g. widget_x, widget_y
);
```

Connection setup: `PRAGMA foreign_keys = ON;` and `PRAGMA journal_mode = WAL;` on every connection. All queries are parameterized.

# Phases

### Phase 0: Repo hygiene (Moto does this, no agent)
- [ ] Replace the four rule files and `pyproject.toml` with the corrected versions.
- [ ] Rename `genral-project-structure.md` to `general-project-structure.md`.
- [ ] Rename `skills/finish-project-security/skill.md` to `SKILL.md`.
- [ ] Delete the stray `.my/prompt` file (keep `.my/prompts/`).
- [ ] Move `GEMINI.md` to the project root (or reduce it to a one-line pointer to `AGENTS.md`). Add a line to `AGENTS.md`: "Read `.agents/workflows/initial-plan.md` and follow its Agent Protocol."
- [ ] Add `.venv/`, `__pycache__/` to `.gitignore`. Exclude `.venv` from Drive sync if the folder syncs.
- [ ] `uv sync`, `uv run plus-ultra`, `git commit`.

### Phase 1: Foundation
**Build:** `config.py` (data dir `$XDG_DATA_HOME/plus-ultra`, state dir `$XDG_STATE_HOME/plus-ultra`, falling back to `~/.local/share` and `~/.local/state`; create dirs with mode `0o700`), logging to `launcher.log` in the state dir, `main.py` with `main()` that logs startup and exits. `uv add --dev ruff pytest`.
**Tests:** path resolution with and without the env vars (use `monkeypatch`).
**Gate:** `uv run plus-ultra` writes startup lines to `launcher.log` and exits 0. ruff and pytest pass.
**Concepts:** XDG base directories, file permissions.

### Phase 2: Wayland spike (go / no-go)
**Build:** `ui/theme.py` and `ui/floating.py`: a borderless, ~90px circular-looking widget (dark rounded canvas), `-topmost`, drag to move, a slow color pulse via `after()`, click toggles a placeholder state. Runs from `main.py`. Position is kept in memory only (persistence arrives in Phase 3).
**Moto tests manually and records results in the log:** stays above a browser? above Files or GNOME Terminal? drag works? survives switching workspaces? pulse smooth? Does it look blurry?
**Gate:** Moto says "go" or "no-go". On no-go, the agent presents options and trade-offs and waits.
**Concepts:** event loop vs threads, window stacking, compositor.

### Phase 3: Database layer
**Build:** `db.py`, `models.py`, `repository.py` per section 6. Migration runner using `user_version`. A `transaction()` context manager that commits on success and rolls back on error. CRUD for tasks, categories, reminders, settings. Wire widget position save and restore through a small service call or a direct setting read in `main.py` (not from `ui/`).
**Tests (first):** constraints (empty title rejected, bad status rejected), `ON DELETE CASCADE` and `SET NULL`, rollback leaves no partial rows, migrations are idempotent, `EXPLAIN QUERY PLAN` shows `idx_reminders_due` is used.
**Gate:** all tests pass; the widget reopens at its last position.
**Concepts:** ACID, primary and foreign keys, normalization (3NF), indexes, migrations.

### Phase 4: Services and panel UI
**Build:** `services.py` (`TaskService`: add, edit, set status, delete, list by category or status). `ui/panel.py`: a normal `Toplevel` with a task list (`ttk.Treeview`), add and edit dialogs, category filter, status toggle. Clicking the widget opens or closes the panel. Add the `--smoke-test` flag: build the UI, `after(1500, root.destroy)`, exit 0.
**Tests:** `test_services.py` against a temp database.
**Gate:** Moto adds three tasks, restarts, and they persist. `xvfb-run -a uv run plus-ultra --smoke-test` exits 0.
**Concepts:** layering (MVC-style), separation of concerns.

### Phase 5: Reminders, notifications, tray
**Decision D1 (needs Moto's approval before coding):** pystray's AppIndicator backend needs system bindings that a uv-managed Python venv may not see. The agent first runs a **tray spike** (just an icon and a Quit item) and reports whether it appears in the GNOME top bar. If not, present these options:
1. Install the AppIndicator typelib and PyGObject through apt, and create the venv from the system Python 3.12 with system site packages. Likely works; touches the environment.
2. Build PyGObject inside the venv with the apt build dependencies. Heavier setup.
3. Drop the tray. The floating widget and notifications are enough. Requires approving a stack change.

Not verified which works on Moto's machine. Do not pick one without asking.

**Build:** `scheduler.py` (a tick every `REMINDER_POLL_MS = 10_000` that asks the service for due, unfired reminders, notifies, and marks them fired inside one transaction). `desktop.notify()` using `notify-send` with an argument list and a timeout. `tray.py` with `run_detached()` and a command queue drained on the Tk thread (menu: Show, Add task, Quit). Add `pystray` and `Pillow` with `uv add` once D1 is settled.
**Tests:** scheduler logic with a fake clock and fake notifier; no real `notify-send` in tests.
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

### Phase 7: Polish and report
**Build:** finish `ui/theme.py` (the glow), README (setup with `uv sync`, how to run, how to autostart), and `--import-json PATH` for the old app's data. **Moto must supply a sample of the old JSON first; the agent must not guess the schema.** Optional backlog from the old app: clipboard and quick-links categories, color-coded task states.
**Report:** `docs/concepts.md` mapping each OS and DBMS concept to the file and function where it appears (XDG paths in `config.py`, locking in `desktop.py`, ACID in `db.transaction`, indexes in the migration, and so on).
**Gate:** a fresh clone, `uv sync` and `uv run plus-ultra` work end to end.

# Moto's Supervision Checklist (every gate)

1. Read the diff. If you cannot explain a function, ask the agent to explain it before accepting.
2. Run the app yourself. Agent-reported success is not verification, especially for Wayland, tray and notifications.
3. Run `uv run ruff check . && uv run pytest`.
4. `git commit -m "phase-N: <what>"`.
5. Paste the agent's draft into `.my/progress-log.md`.
6. Start the next phase in a **fresh chat** so context stays small. The log file carries the memory.

# Definition of Done

- All phase gates passed and committed.
- `uv sync && uv run plus-ultra` works on a fresh clone.
- Floating widget, panel, tray, reminders and notifications work on Wayland, or the limits are documented with the decisions taken.
- `ruff` and `pytest` are clean.
- `docs/concepts.md` maps every OS and DBMS concept to code.
- No secrets or personal data committed (run the `finish-project-security` skill).