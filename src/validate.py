"""Validation for schedule.json.

Two tiers:
  * errors   -> fatal; the build must stop and nothing is published.
  * warnings -> non-fatal; surfaced for human review but the build proceeds.

The single most valuable check is `weekday_matches_source_ref`: it re-derives the
weekday from each event's date and compares it against the weekday named in
`source_ref`. A mismatch is the fingerprint of a wrong year (the source PDF prints
2025 on some pages), so it is reported loudly.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

KNOWN_SUBJECTS = {
    "PATHOLOGY", "PHARMACOLOGY", "MICRO", "PD", "PREVMED",
    "PSYCHIATRY", "RESEARCH", "LEGALMED", "OTHER",
}

WEEKDAYS = {
    "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
    "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6,
}

PLAUSIBLE_START = dt.time(6, 0)
PLAUSIBLE_END = dt.time(20, 0)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def _parse_time(s: str) -> dt.time:
    h, m = s.split(":")
    return dt.time(int(h), int(m))


def _weekday_from_source_ref(source_ref: str) -> int | None:
    """Pull a weekday name out of a source_ref like 'AUGUST 3-8 / MONDAY'."""
    for name, idx in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", source_ref.upper()):
            return idx
    return None


def validate_schema(doc: dict, schema: dict, report: Report) -> None:
    if jsonschema is None:  # pragma: no cover
        report.errors.append("jsonschema is not installed; cannot validate structure.")
        return
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        report.errors.append(f"Schema: {loc}: {err.message}")


def validate_events(doc: dict, report: Report) -> None:
    events = doc.get("events", [])
    term_start = term_end = None
    # term window is supplied via stats by the caller (build.py) if available
    tw = report.stats.get("term_window")
    if tw:
        term_start, term_end = tw

    seen_uids: dict[str, str] = {}
    by_day_section: dict[tuple[str, str], list] = {}

    for i, e in enumerate(events):
        ref = f"event #{i} ({e.get('subject','?')} {e.get('date','?')} '{e.get('title','?')[:40]}')"

        # date parse
        try:
            d = _parse_date(e["date"])
        except (ValueError, KeyError):
            report.errors.append(f"{ref}: invalid or missing date.")
            continue

        # weekday vs source_ref  (the year-typo detector)
        expected = _weekday_from_source_ref(e.get("source_ref", ""))
        if expected is not None and d.weekday() != expected:
            names = {v: k.title() for k, v in WEEKDAYS.items()}
            report.warnings.append(
                f"{ref}: date is a {names[d.weekday()]} but source_ref says "
                f"{names[expected]} - likely a wrong year/date."
            )

        # term window guardrail
        if term_start and term_end and not (term_start <= d <= term_end):
            report.warnings.append(
                f"{ref}: date {d.isoformat()} is outside the term window "
                f"{term_start.isoformat()}..{term_end.isoformat()}."
            )

        # timed vs all-day integrity
        all_day = bool(e.get("all_day"))
        start_s, end_s = e.get("start"), e.get("end")
        if all_day:
            if start_s or end_s:
                report.warnings.append(f"{ref}: all_day event also has start/end times; times ignored.")
        else:
            if not start_s or not end_s:
                report.errors.append(f"{ref}: timed event is missing start and/or end.")
                continue
            start_t, end_t = _parse_time(start_s), _parse_time(end_s)
            if end_t <= start_t:
                report.errors.append(f"{ref}: end {end_s} is not after start {start_s}.")
                continue
            if start_t < PLAUSIBLE_START or end_t > PLAUSIBLE_END:
                report.warnings.append(
                    f"{ref}: {start_s}-{end_s} falls outside the plausible 06:00-20:00 window."
                )
            # overlap bookkeeping within same day + section
            key = (e["date"], e.get("section", "ALL"))
            by_day_section.setdefault(key, []).append((start_t, end_t, ref))

        # unknown subject
        if e.get("subject") not in KNOWN_SUBJECTS:
            report.warnings.append(f"{ref}: unknown subject '{e.get('subject')}'.")

        # confidence surfacing
        conf = e.get("confidence")
        if conf in ("low", "medium"):
            report.warnings.append(f"{ref}: confidence={conf} - please verify against the PDF.")

    # overlap detection (same day + same section, treating ALL as shared)
    for (day, section), items in by_day_section.items():
        items.sort()
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                s1, e1, r1 = items[a]
                s2, e2, r2 = items[b]
                if s2 < e1:  # overlap
                    report.warnings.append(
                        f"Overlap on {day} (section {section}): {r1} overlaps {r2}."
                    )

    report.stats["event_count"] = len(events)


def run_validation(doc: dict, schema: dict, term_window=None) -> Report:
    report = Report()
    if term_window:
        report.stats["term_window"] = term_window
    validate_schema(doc, schema, report)
    # Only run semantic checks if the structure is sane enough to iterate.
    if isinstance(doc.get("events"), list):
        validate_events(doc, report)
    return report
