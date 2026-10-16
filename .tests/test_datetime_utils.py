"""Tests for parse_flexible_datetime utility."""

from __future__ import annotations

import datetime

import pytest

from plus_ultra.datetime_utils import parse_flexible_datetime


def test_parse_iso_with_z() -> None:
    dt = parse_flexible_datetime("2026-10-17T09:30:00Z")
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 17
    assert dt.hour == 9
    assert dt.minute == 30


def test_parse_iso_with_offset() -> None:
    dt = parse_flexible_datetime("2026-10-17T09:30:00+05:30")
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.hour == 9
    assert dt.minute == 30


def test_parse_space_separated_local() -> None:
    dt = parse_flexible_datetime("2026-10-17 14:45")
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 17
    assert dt.hour == 14
    assert dt.minute == 45


def test_parse_date_only() -> None:
    dt = parse_flexible_datetime("2026-10-17")
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 17
    assert dt.hour == 0
    assert dt.minute == 0


def test_parse_datetime_object() -> None:
    now = datetime.datetime.now()
    dt = parse_flexible_datetime(now)
    assert dt.tzinfo is not None
    assert dt.year == now.year


def test_parse_empty_raises_error() -> None:
    with pytest.raises(ValueError):
        parse_flexible_datetime("")
