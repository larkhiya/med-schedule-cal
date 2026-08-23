import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate import _weekday_from_source_ref, _parse_time, _parse_date  # noqa: E402


def test_weekday_from_source_ref():
    assert _weekday_from_source_ref("AUGUST 3-8 / MONDAY") == 0
    assert _weekday_from_source_ref("SEPTEMBER 28-OCTOBER 3 / THURSDAY") == 3
    assert _weekday_from_source_ref("no weekday here") is None


def test_parse_time():
    assert _parse_time("07:30").hour == 7
    assert _parse_time("13:45").minute == 45


def test_year_typo_is_detectable():
    # The PDF printed 2025; Sep 28 2025 is a Sunday, but the column says MONDAY.
    d_wrong = _parse_date("2025-09-28")
    assert d_wrong.weekday() != _weekday_from_source_ref("SEP 28 / MONDAY")
    # Corrected to 2026, Sep 28 is a Monday and matches.
    d_right = _parse_date("2026-09-28")
    assert d_right.weekday() == _weekday_from_source_ref("SEP 28 / MONDAY")
