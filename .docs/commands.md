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
1. **Window Placement**: The capsule appears at the top-center of your screen.
2. **Hover Glow**: Moving mouse cursor over the capsule highlights its border with electric cyan (`#00e5ff`) and brightens text.
3. **Draggability**: Left-click and hold anywhere on the capsule to drag it smoothly across displays.
4. **Window Stacking**: The capsule stays on top of open browser or terminal windows (`-topmost`).
5. **Single-Instance Enforcement**: Open a second terminal and execute `uv run plus-ultra`. It should immediately print `PLUS-ULTRA is already running.` and exit with code 0 without launching a second widget.
6. **Clean Termination**: Pressing `Escape` while focused or `Ctrl+C` in the terminal destroys the widget and cleans up the lock file at `~/.local/state/plus-ultra/plus-ultra.lock`.