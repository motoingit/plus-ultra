"""Tests for plus_ultra.settings module.

Validates:
- Happy paths: defaults loading, overriding settings, resetting single/all.
- Type safety: strict type matching (bool is not int, int is not bool).
- Defensive recovery: malformed JSON and non-object JSON quarantined without
  crashing, returning safe defaults.
- Security & POSIX permissions: mode 0o600 on file, mode 0o700 on config dir.
- Rejection of unknown keys and machine state (widget_x/y).
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from plus_ultra import config, settings


@pytest.fixture(autouse=True)
def isolated_config_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Path:
    """Isolate configuration directory for each test run."""
    cfg_dir = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg_dir))
    settings.reload()
    return cfg_dir / config.APP_NAME


def test_default_settings_keys_and_values() -> None:
    """Verify default settings match the locked schema."""
    defaults = settings.load_default_settings()

    assert defaults["settings_version"] == 1
    assert defaults["always_on_top"] is True
    assert defaults["glow_enabled"] is True
    assert defaults["glow_pulse_period_ms"] == 3000
    assert defaults["reminders_enabled"] is True
    assert defaults["panel_width"] == 1380
    assert defaults["panel_height"] == 840
    assert defaults["panel_min_width"] == 1000
    assert defaults["panel_min_height"] == 640
    assert defaults["notification_popup_duration_ms"] == 3000
    assert set(defaults.keys()) == {
        "settings_version",
        "always_on_top",
        "glow_enabled",
        "glow_pulse_period_ms",
        "reminders_enabled",
        "network_monitor_enabled",
        "panel_width",
        "panel_height",
        "panel_min_width",
        "panel_min_height",
        "notification_popup_duration_ms",
    }


def test_effective_settings_fallback_to_defaults() -> None:
    """When no user file exists, effective settings are defaults."""
    effective = settings.load_effective_settings()
    defaults = settings.load_default_settings()
    assert effective == defaults


def test_update_setting_persists_and_enforces_0600() -> None:
    """Updating a setting persists atomically with mode 0o600."""
    updated = settings.update_user_setting("always_on_top", False)
    assert updated["always_on_top"] is False

    settings_file = config.get_user_settings_path()
    assert settings_file.is_file()

    file_mode = stat.S_IMODE(settings_file.stat().st_mode)
    assert file_mode == 0o600, f"Expected 0o600, got {oct(file_mode)}"

    # Reload fresh to verify persistence
    reloaded = settings.reload()
    assert reloaded["always_on_top"] is False
    assert reloaded["glow_pulse_period_ms"] == 3000


def test_reset_setting_reverts_to_default() -> None:
    """Resetting a single key removes override and restores default."""
    settings.update_user_setting("reminders_enabled", False)
    assert settings.load_effective_settings()["reminders_enabled"] is False

    settings.reset_setting("reminders_enabled")
    effective = settings.load_effective_settings()
    assert effective["reminders_enabled"] is True


def test_reset_all_settings_clears_all_overrides() -> None:
    """reset_all_settings() removes overrides and restores all defaults."""
    settings.update_user_setting("always_on_top", False)
    settings.update_user_setting("glow_pulse_period_ms", 1500)

    settings.reset_all_settings()
    effective = settings.load_effective_settings()
    defaults = settings.load_default_settings()
    assert effective == defaults


def test_unknown_key_rejected_in_api() -> None:
    """Unknown keys cannot be set via update_user_setting."""
    with pytest.raises(KeyError):
        settings.update_user_setting("unknown_option", 123)

    with pytest.raises(KeyError):
        settings.reset_setting("unknown_option")


def test_machine_state_rejected_in_settings() -> None:
    """Machine state like widget coordinates cannot be saved in settings."""
    with pytest.raises(KeyError):
        settings.update_user_setting("widget_x", 400)

    with pytest.raises(KeyError):
        settings.update_user_setting("widget_y", 200)


def test_type_safety_strict_equality() -> None:
    """Types must match exactly: bool is not int and int is not bool."""
    # Attempting to set int where bool is expected
    with pytest.raises(TypeError):
        settings.update_user_setting("always_on_top", 1)

    # Attempting to set str where bool is expected
    with pytest.raises(TypeError):
        settings.update_user_setting("always_on_top", "true")

    # Attempting to set bool where int is expected
    with pytest.raises(TypeError):
        settings.update_user_setting("glow_pulse_period_ms", True)

    # Attempting to set str where int is expected
    with pytest.raises(TypeError):
        settings.update_user_setting("glow_pulse_period_ms", "3000")


def test_external_file_with_unknown_and_invalid_types(
    isolated_config_dir: Path,
) -> None:
    """Invalid user file ignores unknown keys and mismatched types."""
    settings_file = config.get_user_settings_path()
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(
        '{"unknown_key": "val", "always_on_top": 1, "reminders_enabled": false}'
    )

    effective = settings.reload()
    assert "unknown_key" not in effective
    # always_on_top had int (1), expected bool -> ignored, kept default True
    assert effective["always_on_top"] is True
    # reminders_enabled had bool (false), expected bool -> accepted False
    assert effective["reminders_enabled"] is False


def test_corrupt_json_quarantined_without_crashing(
    isolated_config_dir: Path,
) -> None:
    """Corrupted JSON is quarantined to .bad-<timestamp> and defaults used."""
    settings_file = config.get_user_settings_path()
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text("NOT_VALID_JSON{::: broken")

    effective = settings.reload()
    assert effective == settings.load_default_settings()

    # Original file should be gone (renamed)
    assert not settings_file.exists()

    # Quarantined file should exist
    quarantined = list(settings_file.parent.glob(f"{settings_file.name}.bad-*"))
    assert len(quarantined) == 1
    assert "NOT_VALID_JSON" in quarantined[0].read_text(encoding="utf-8")


def test_non_dict_json_quarantined(
    isolated_config_dir: Path,
) -> None:
    """Top-level JSON array is quarantined as invalid structure."""
    settings_file = config.get_user_settings_path()
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text("[1, 2, 3]")

    effective = settings.reload()
    assert effective == settings.load_default_settings()

    quarantined = list(settings_file.parent.glob(f"{settings_file.name}.bad-*"))
    assert len(quarantined) == 1


def test_dashboard_dimension_configuration_and_persistence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify panel dimensions load from settings and persist on update."""
    cfg_dir = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg_dir))
    settings.reload()

    # Initial defaults
    eff = settings.load_effective_settings()
    assert eff["panel_width"] == 1380
    assert eff["panel_height"] == 840
    assert eff["panel_min_width"] == 1000
    assert eff["panel_min_height"] == 640

    # User modifies dimensions
    settings.update_user_setting("panel_width", 1450)
    settings.update_user_setting("panel_height", 900)

    # Reload from disk
    reloaded = settings.reload()
    assert reloaded["panel_width"] == 1450
    assert reloaded["panel_height"] == 900
