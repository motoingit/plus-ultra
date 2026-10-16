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
2. **Animated Border Beam**: A luminous neon cyan beam with a bright tip continuously orbits smoothly around the contour of the pill (~40 FPS).
3. **Hover Response**: Moving mouse cursor over the capsule increases the orbiting beam speed and brightens the pill.
4. **Draggability**: Left-click and hold anywhere on the capsule to drag it smoothly across displays.
5. **Dynamic Notification Expansion (Center-Outward)**:
   - Right-click anywhere on the capsule (or press **`n`** on your keyboard).
   - The capsule smoothly expands horizontally from the center outward to display an icon, title, and preview message.
   - Press **`n`** again: A second unread notification arrives and an unread badge (`+1`) appears.
   - Click the **`✕`** button on the right end: The top notification is dismissed, and the capsule smoothly shrinks back down toward idle width.
6. **Position Persistence**: Drag the capsule to a new screen coordinate, close the application (`Escape` or `Ctrl+C`), and re-run `uv run plus-ultra`. The widget must reappear at the exact dragged location, restored from SQLite `app_state`.
7. **Window Stacking**: The capsule stays on top of open browser or terminal windows (`-topmost`).
8. **Single-Instance Enforcement**: Open a second terminal and execute `uv run plus-ultra`. It should immediately print `PLUS-ULTRA is already running.` and exit with code 0 without launching a second widget.
9. **Clean Termination**: Pressing `Escape` while focused or `Ctrl+C` in the terminal destroys the widget and cleans up the lock file at `~/.local/state/plus-ultra/plus-ultra.lock`.