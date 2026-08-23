"""Build an iCalendar (.ics) feed from a validated schedule document.

Design notes:
  * Asia/Manila is a permanent UTC+8 (no DST since 1978), so a single-rule
    VTIMEZONE is embedded for maximum client compatibility (Apple Calendar likes
    a self-contained VTIMEZONE).
  * UIDs are stable hashes of subject|date|start|title so that re-publishing an
    updated schedule updates events in place instead of creating duplicates.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event, Timezone, TimezoneStandard

MANILA = ZoneInfo("Asia/Manila")


def _manila_vtimezone() -> Timezone:
    tz = Timezone()
    tz.add("TZID", "Asia/Manila")
    std = TimezoneStandard()
    std.add("DTSTART", dt.datetime(1970, 1, 1, 0, 0, 0))
    std.add("TZOFFSETFROM", dt.timedelta(hours=8))
    std.add("TZOFFSETTO", dt.timedelta(hours=8))
    std.add("TZNAME", "PST")  # Philippine Standard Time
    tz.add_component(std)
    return tz


def _uid(event: dict, namespace: str) -> str:
    basis = f"{event['subject']}|{event['date']}|{event.get('start') or 'allday'}|{event['title']}"
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]
    return f"{digest}@{namespace}"


def _summary(event: dict) -> str:
    subject = event["subject"]
    activity = event["activity"]
    title = event["title"]
    if activity == "Holiday":
        return f"Holiday - {title}"
    return f"{subject} - {activity}: {title}"


def _description(event: dict) -> str:
    lines = []
    if event.get("lecturer"):
        lines.append(f"Lecturer: {event['lecturer']}")
    if event.get("section") and event["section"] != "ALL":
        lines.append(f"Section: {event['section']}")
    if event.get("notes"):
        lines.append(event["notes"])
    if event.get("confidence") and event["confidence"] != "high":
        lines.append(f"[Extraction confidence: {event['confidence']} - verify against source]")
    lines.append(f"Source: {event.get('source_ref', '')}")
    return "\n".join(lines)


def keep_event(event: dict, section: str, include_untimed: bool) -> bool:
    """Apply config filters (section, untimed)."""
    if section != "ALL":
        ev_section = event.get("section", "ALL")
        if ev_section not in (section, "ALL"):
            return False
    if not include_untimed and event.get("all_day") and event.get("activity") in (
        "Independent Study", "Orientation"
    ):
        return False
    return True


def subject_slug(subject: str) -> str:
    """Filename-safe slug for a subject, e.g. 'PATHOLOGY' -> 'pathology'."""
    return "".join(c if c.isalnum() else "-" for c in subject.lower()).strip("-")


def build_calendar(doc: dict, config: dict, build_time: dt.datetime | None = None,
                   subjects: set[str] | None = None,
                   name_suffix: str = "") -> tuple[Calendar, int]:
    """Build a calendar. If `subjects` is given, only those subjects are included
    (used to emit one feed per subject). `name_suffix` is appended to the
    calendar's display name so Apple shows distinct names per feed."""
    build_time = build_time or dt.datetime.now(tz=dt.timezone.utc)
    section = config.get("section", "ALL")
    include_untimed = config.get("include_untimed", True)
    namespace = config.get("uid_namespace", "schedule")

    cal_name = config.get("calendar_name", "Schedule")
    if name_suffix:
        cal_name = f"{cal_name} - {name_suffix}"

    cal = Calendar()
    cal.add("PRODID", "-//med-schedule-cal//EN")
    cal.add("VERSION", "2.0")
    cal.add("CALSCALE", "GREGORIAN")
    cal.add("METHOD", "PUBLISH")
    cal.add("X-WR-CALNAME", cal_name)
    cal.add("X-WR-TIMEZONE", "Asia/Manila")
    cal.add_component(_manila_vtimezone())

    count = 0
    for e in doc.get("events", []):
        if not keep_event(e, section, include_untimed):
            continue
        if subjects is not None and e.get("subject") not in subjects:
            continue
        comp = Event()
        comp.add("UID", _uid(e, namespace))
        comp.add("SUMMARY", _summary(e))
        comp.add("DESCRIPTION", _description(e))
        comp.add("CATEGORIES", [e["subject"], e["activity"]])
        comp.add("DTSTAMP", build_time)
        comp.add("LAST-MODIFIED", build_time)
        comp.add("SEQUENCE", 0)

        d = dt.date.fromisoformat(e["date"])
        if e.get("all_day") or not e.get("start"):
            comp.add("DTSTART", d)
            comp.add("DTEND", d + dt.timedelta(days=1))
            comp.add("X-MICROSOFT-CDO-ALLDAYEVENT", "TRUE")
        else:
            sh, sm = map(int, e["start"].split(":"))
            eh, em = map(int, e["end"].split(":"))
            comp.add("DTSTART", dt.datetime(d.year, d.month, d.day, sh, sm, tzinfo=MANILA))
            comp.add("DTEND", dt.datetime(d.year, d.month, d.day, eh, em, tzinfo=MANILA))
        cal.add_component(comp)
        count += 1

    return cal, count


def write_ics(cal: Calendar, path: str) -> None:
    with open(path, "wb") as f:
        f.write(cal.to_ical())
