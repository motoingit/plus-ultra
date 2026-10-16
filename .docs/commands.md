# uv

## checking
uv run ruff check .
uv run pytest -v

##
uv run ruff format --check .

## running
uv run python main.py
uv run plus-ultra

## logs

### recent
tail -n 10 ~/.local/state/plus-ultra/launcher.log
### continous
tail -f ~/.local/state/plus-ultra/launcher.log

# Testing Commands

## Automated Test Suites
```bash
# Run all project unit and integration tests
uv run pytest -v

# Run targeted test suites
uv run pytest tests/test_scheduler.py -v
uv run pytest tests/test_services.py -v
uv run pytest tests/test_panel.py -v
uv run pytest tests/test_db.py -v
uv run pytest tests/test_repository.py -v
uv run pytest tests/test_desktop.py -v
uv run pytest tests/test_ui.py -v
uv run pytest tests/test_config.py -v
uv run pytest tests/test_settings.py -v
```

## CLI Test Flags & Headless Validation
```bash
# Smoke test: Launches floating widget, waits 500ms, and closes cleanly (exit 0)
uv run plus-ultra --smoke-test

# Headless check: Initializes paths, logging, and settings without launching GUI
uv run plus-ultra --no-ui

# Headless smoke test in virtual display (CI / remote environments without display)
xvfb-run -a uv run plus-ultra --smoke-test

# Display CLI manual and dynamic metadata
uv run plus-ultra --help
```

## Manual Interactive Desktop Checklist
Run the application interactively in your terminal:
```bash
uv run plus-ultra
```

Verify the following behaviors:
1. **Window Placement**: The capsule appears as a true mathematical pill with zero rectangular dark corners (clipped via XShape).
2. **Animated Border Beam**: A luminous neon cyan beam with a bright tip orbits smoothly around the contour of the pill exclusively on hover (~40 FPS). It stops when unhovered.
3. **Draggability & Position Memory**: Left-click and drag anywhere on the capsule. The widget remembers its coordinate in SQLite `app_state`.
4. **Dashboard Toggle**: Single left-click without dragging toggles the 3-column Dashboard workspace window open and closed.
5. **3-Column Workspace Window (All 6 Tabs + Settings Fully Interactive)**:
   - **Column 1 (Left Sidebar)**: 6 tabs (`Tasks`, `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`) + pinned Settings. Modern flat buttons with zero ugly borders or text truncation.
   - **Column 2 (Center Panel)**:
     - **`Tasks`**: Option A styled `ttk.Treeview` task list. `+ New Task`, live search, status pills (`Pending`, `Completed`), and priority filter.
     - **`Code`**: Sub-category filters (`Snippets`, `CLI Commands`, `Syntax Reference`, `DSA Problem Tracker`). Click `📋 Copy` for instant clipboard copy with `✓ Copied!` feedback for 1.5s. Click `○ Todo` / `✓ Solved` to toggle DSA problem status or `🔗 Open Problem` to launch URL.
     - **`Courses`**: Visual progress bars showing completion percentage. Click `+1 Module` to increment module count and auto-update progress in SQLite. Click `🔗 Open` to launch lecture.
     - **`Ideas-Doubt`**: Filter between `💡 Project Ideas` and `❓ Concept Doubts`. Click status buttons (`[Idea]`, `[Planned]`, `[In Progress]`, `[Completed]`, `[Resolved]`) to advance lifecycle.
     - **`Opportunities`**: Role cards with organization, deadlines, and `[Saved]` -> `[Applied]` lifecycle progression. Click `🔗 Apply` to launch URL.
     - **`Quick Links`**: Fast launcher for Web URLs and local folders/files. Click `🚀 Open` to launch default browser or Linux file manager (`xdg-open`), incrementing click count.
     - **`Settings`**: Live toggles for Always-On-Top, local SQLite database diagnostics, and `Reseed Demo Data` button.
   - **Column 3 (Right Sidebar)**: Notification panel showing active alerts. Click `Mark All Read` or `Clear` to clear unread status and remove the orange bell on the floating capsule.

6. **Notification Flow**:
   - Right-click on the capsule to trigger a test notification alert.
   - Main capsule stays compact and displays an orange bell icon (`🔔`).
   - A separate temporary popup pill appears directly below the main capsule for 3 seconds, then cleanly auto-dismisses.
   - Open the dashboard panel, click `Mark All Read` or `Clear`: the orange bell on the capsule disappears and text re-centers.
7. **Background Reminder Evaluation**:
   - Background worker thread periodically polls SQLite every 10 seconds.
   - When a reminder becomes due, it dispatches a native Linux `notify-send` desktop alert and thread-safely enqueues the alert to the floating capsule and dashboard panel without blocking the UI main thread.
8. **Window Stacking**: The capsule stays on top of open windows (`-topmost`).
9. **Single-Instance Enforcement**: Run `uv run plus-ultra` in another terminal; prints `PLUS-ULTRA is already running.` and exits with code 0.
10. **Clean Termination**: `Ctrl+C` in the terminal destroys both windows, stops the scheduler thread, and cleans up the lock file.