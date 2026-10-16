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
- `FloatingWidget(root: tk.Tk | None, geometry: CapsuleGeometry, theme: CapsuleTheme, on_click_callback: Callable | None)`:
  - Initializes a borderless (`overrideredirect(True)`), `-topmost` floating window placed at the top-center of the primary display.
  - Draws a smooth capsule polygon with hover glow animation.
  - Implements mouse drag tracking (`<Button-1>`, `<B1-Motion>`) and click detection on mouse release.
  - `close() -> None`: Closes window and exits main event loop cleanly.
  - `run() -> None`: Starts Tkinter `mainloop()`.

### CLI Flags (`plus-ultra`)
- `--smoke-test`: Automatically initializes the application and closes the floating widget after 500ms, returning exit code 0.
- `--no-ui`: Initializes configuration, state directories, and logging without starting the GUI event loop.


