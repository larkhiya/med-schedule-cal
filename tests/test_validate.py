import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate import run_validation  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "schedule.schema.json").read_text())

BASE_META = {
    "term": "Test",
    "source_title": "Test",
    "week_blocks": [{"label": "AUG 3-8, 2026", "start": "2026-08-03", "end": "2026-08-08"}],
}


def _doc(events):
    return {"meta": BASE_META, "events": events}


def _event(**kw):
    e = {
        "subject": "MICRO", "activity": "Lecture", "title": "T",
        "date": "2026-08-07", "start": "07:30", "end": "09:30",
        "all_day": False, "section": "ALL", "confidence": "high",
        "source_ref": "AUG 3-8 / FRIDAY",
    }
    e.update(kw)
    return e


def test_clean_event_has_no_errors():
    r = run_validation(_doc([_event()]), SCHEMA)
    assert r.ok
    assert not r.warnings


def test_end_before_start_is_error():
    r = run_validation(_doc([_event(start="10:00", end="09:00")]), SCHEMA)
    assert not r.ok


def test_missing_time_on_timed_event_is_error():
    r = run_validation(_doc([_event(start=None, end=None, all_day=False)]), SCHEMA)
    assert not r.ok


def test_weekday_mismatch_is_warning_not_error():
    # 2026-08-07 is a Friday; claim it's Monday in source_ref.
    r = run_validation(_doc([_event(source_ref="AUG 3-8 / MONDAY")]), SCHEMA)
    assert r.ok  # non-fatal
    assert any("wrong year" in w or "MONDAY" in w for w in r.warnings)


def test_out_of_window_is_warning():
    tw = (dt.date(2026, 8, 3), dt.date(2026, 10, 10))
    r = run_validation(_doc([_event(date="2027-01-01", source_ref="X")]), SCHEMA, term_window=tw)
    assert any("outside the term window" in w for w in r.warnings)


def test_overlap_is_warning():
    a = _event(title="A", start="09:00", end="11:00")
    b = _event(title="B", start="10:00", end="12:00")
    r = run_validation(_doc([a, b]), SCHEMA)
    assert any("Overlap" in w for w in r.warnings)


def test_low_confidence_surfaces():
    r = run_validation(_doc([_event(confidence="low")]), SCHEMA)
    assert any("confidence=low" in w for w in r.warnings)


def test_bad_enum_is_schema_error():
    r = run_validation(_doc([_event(subject="ASTROLOGY")]), SCHEMA)
    assert not r.ok
