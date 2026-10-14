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


