"""Entrypoint: validate schedule.json, then build the .ics feed and preview page.

Exit code 1 on any fatal validation error (fails the GitHub Actions run and
prevents a broken calendar from publishing). Warnings never fail the build; they
are printed and written to the run's job summary and the preview page.

Run:  python src/build.py
Env:
  PAGES_BASE_URL   base URL of the published site (e.g.
                   https://user.github.io/med-schedule-cal). The .ics URL is
                   PAGES_BASE_URL/schedule.ics. Falls back to a relative link.
  GITHUB_STEP_SUMMARY  if set, a Markdown report is appended for the Actions UI.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ics as ics_mod          # noqa: E402
import preview as preview_mod  # noqa: E402
from validate import run_validation  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "schedule.json"
SCHEMA = ROOT / "schema" / "schedule.schema.json"
CONFIG = ROOT / "config.yaml"
SITE = ROOT / "site"


def load_json(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def term_window(config: dict):
    try:
        return (
            dt.date.fromisoformat(config["term_start"]),
            dt.date.fromisoformat(config["term_end"]),
        )
    except (KeyError, ValueError):
        return None


def emit_summary(report, kept_count: int, ics_url: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    lines = [
        "## Schedule build",
        f"- Events published: **{kept_count}**",
        f"- Errors: **{len(report.errors)}**",
        f"- Warnings: **{len(report.warnings)}**",
        f"- Feed URL: `{ics_url}`",
    ]
    if report.errors:
        lines.append("\n### Errors (build failed)")
        lines += [f"- {e}" for e in report.errors]
    if report.warnings:
        lines.append("\n<details><summary>Warnings</summary>\n")
        lines += [f"- {w}" for w in report.warnings]
        lines.append("\n</details>")
    text = "\n".join(lines) + "\n"
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)


def main() -> int:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    doc = load_json(DATA)
    schema = load_json(SCHEMA)

    report = run_validation(doc, schema, term_window=term_window(config))

    base = os.environ.get("PAGES_BASE_URL", "").rstrip("/")
    ics_url = f"{base}/schedule.ics" if base else "schedule.ics"

    print(f"Validation: {len(report.errors)} error(s), {len(report.warnings)} warning(s).")
    for e in report.errors:
        print(f"  ERROR  {e}")
    for w in report.warnings:
        print(f"  warn   {w}")

    if not report.ok:
        emit_summary(report, 0, ics_url)
        print("\nFatal errors present - not building the calendar.")
        return 1

    build_time = dt.datetime.now(tz=dt.timezone.utc)
    SITE.mkdir(exist_ok=True)

    # combined feed
    cal, kept = ics_mod.build_calendar(doc, config, build_time=build_time)
    ics_mod.write_ics(cal, str(SITE / "schedule.ics"))

    # per-subject feeds (for a color per subject in Apple Calendar)
    subject_feeds = []
    if config.get("emit_per_subject_feeds"):
        section = config.get("section", "ALL")
        include_untimed = config.get("include_untimed", True)
        present = []
        for e in doc.get("events", []):
            if ics_mod.keep_event(e, section, include_untimed):
                if e["subject"] not in present:
                    present.append(e["subject"])
        for subject in present:
            scal, scount = ics_mod.build_calendar(
                doc, config, build_time=build_time,
                subjects={subject}, name_suffix=subject,
            )
            slug = ics_mod.subject_slug(subject)
            fname = f"schedule-{slug}.ics"
            ics_mod.write_ics(scal, str(SITE / fname))
            url = f"{base}/{fname}" if base else fname
            subject_feeds.append({"subject": subject, "url": url, "count": scount})
        print(f"Emitted {len(subject_feeds)} per-subject feeds.")

    html_str = preview_mod.render(doc, config, report, ics_url, kept, build_time,
                                  subject_feeds=subject_feeds)
    preview_mod.write_preview(html_str, str(SITE / "index.html"))

    emit_summary(report, kept, ics_url)
    print(f"\nBuilt {kept} events -> site/schedule.ics and site/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
