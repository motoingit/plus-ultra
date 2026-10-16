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
5. **3-Column Workspace Window**:
   - **Column 1 (Left Sidebar)**: 6 tabs (`Tasks`, `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`) + pinned Settings.
   - **Column 2 (Center Panel)**: Option A styled `ttk.Treeview` task list. Click `+ New Task` to add tasks. Live search instantly filters tasks. Click status pills (`Pending`, `Completed`) or priority dropdown to filter.
   - **Column 3 (Right Sidebar)**: Notification panel showing active alerts. Click `Mark All Read` to clear unread status and remove the orange bell on the floating capsule.
6. **Notification Flow**:
   - Right-click on the capsule to trigger a test notification alert.
   - Main capsule stays compact and displays an orange bell icon (`🔔`).
   - A separate temporary popup pill appears directly below the main capsule for 3 seconds, then cleanly auto-dismisses.
   - Open the dashboard panel, click `Mark All Read` or `Clear`: the orange bell on the capsule disappears and text re-centers.
7. **Window Stacking**: The capsule stays on top of open windows (`-topmost`).
8. **Single-Instance Enforcement**: Run `uv run plus-ultra` in another terminal; prints `PLUS-ULTRA is already running.` and exits with code 0.
9. **Clean Termination**: `Ctrl+C` in the terminal destroys both windows and cleans up the lock file.