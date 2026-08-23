"""Generate site/index.html: a review-and-subscribe page.

The page's two jobs are (1) let a human eyeball the whole extracted schedule and
spot anything wrong, and (2) subscribe in one tap. Flags and low-confidence rows
are pulled to the top and highlighted; everything else stays quiet.
"""
from __future__ import annotations

import datetime as dt
import html

SUBJECT_HUES = {
    "PATHOLOGY": "#8a3f3f",
    "PHARMACOLOGY": "#3f6f8a",
    "MICRO": "#3f8a5c",
    "PD": "#7a5f2f",
    "PREVMED": "#5c5c8a",
    "PSYCHIATRY": "#8a3f77",
    "RESEARCH": "#4a4a4a",
    "OTHER": "#6a6a6a",
}


def _esc(s: str) -> str:
    return html.escape(s or "")


def _webcal(url: str) -> str:
    if url.startswith("https://"):
        return "webcal://" + url[len("https://"):]
    if url.startswith("http://"):
        return "webcal://" + url[len("http://"):]
    return url


def render(doc: dict, config: dict, report, ics_url: str, kept_count: int,
           build_time: dt.datetime, subject_feeds: list | None = None) -> str:
    subject_feeds = subject_feeds or []
    meta = doc.get("meta", {})
    cal_name = _esc(config.get("calendar_name", "Schedule"))
    term = _esc(meta.get("term", ""))
    review_notes = meta.get("review_notes", [])
    warnings = report.warnings

    # group kept events by week block, then by date
    blocks = meta.get("week_blocks", [])

    def block_for(date_str: str):
        for b in blocks:
            if b["start"] <= date_str <= b["end"]:
                return b["label"]
        return "Other"

    section = config.get("section", "ALL")
    include_untimed = config.get("include_untimed", True)

    from ics import keep_event  # local import to avoid cycle at module load
    kept = [e for e in doc.get("events", []) if keep_event(e, section, include_untimed)]

    grouped: dict[str, dict[str, list]] = {}
    for e in kept:
        grouped.setdefault(block_for(e["date"]), {}).setdefault(e["date"], []).append(e)

    def sort_key(e):
        return (e["date"], e.get("start") or "00:00")

    # ---- build HTML
    subscribe = _webcal(ics_url)
    parts: list[str] = []
    parts.append(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{cal_name}</title>
<style>
  :root {{
    --ink: #1c1b19; --muted: #6b6862; --line: #e3ded4; --paper: #faf8f3;
    --card: #ffffff; --flag: #b5462f; --flagbg: #fbeee9; --ok: #3f7a4a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--paper); color: var(--ink);
    font: 15px/1.5 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-text-size-adjust: 100%;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 20px 16px 64px; }}
  header {{ border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 8px; }}
  .eyebrow {{ font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }}
  h1 {{ font-size: 24px; margin: 4px 0 2px; font-weight: 650; letter-spacing: -.01em; }}
  .sub {{ color: var(--muted); font-size: 13px; }}
  .cta {{
    display: inline-block; margin: 16px 0 4px; padding: 12px 18px; border-radius: 10px;
    background: var(--ink); color: #fff; text-decoration: none; font-weight: 600;
  }}
  .cta:active {{ opacity: .85; }}
  .urlrow {{ font-size: 12px; color: var(--muted); margin-top: 8px; word-break: break-all; }}
  .urlrow code {{ background: #f0ece3; padding: 2px 6px; border-radius: 6px; }}
  .feeds {{ margin: 18px 0 4px; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }}
  .feeds > .hd {{ padding: 12px 16px; background: #f5f1e9; border-bottom: 1px solid var(--line); }}
  .feeds > .hd .t {{ font-weight: 650; }}
  .feeds > .hd .d {{ font-size: 12.5px; color: var(--muted); margin-top: 2px; }}
  .feed {{ display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-top: 1px solid var(--line); }}
  .feed:first-of-type {{ border-top: 0; }}
  .sw {{ width: 14px; height: 14px; border-radius: 4px; flex: 0 0 auto; }}
  .feed .nm {{ flex: 1; font-weight: 600; }}
  .feed .ct {{ font-size: 12px; color: var(--muted); }}
  .feed a {{ font-size: 13px; font-weight: 600; color: #fff; background: var(--ink);
    padding: 7px 12px; border-radius: 8px; text-decoration: none; }}
  .panel {{
    border: 1px solid var(--line); border-left: 4px solid var(--flag);
    background: var(--flagbg); border-radius: 10px; padding: 14px 16px; margin: 20px 0;
  }}
  .panel h2 {{ font-size: 13px; text-transform: uppercase; letter-spacing: .1em; margin: 0 0 8px; color: var(--flag); }}
  .panel ul {{ margin: 0; padding-left: 18px; }}
  .panel li {{ margin: 3px 0; font-size: 13px; }}
  .panel.clean {{ border-left-color: var(--ok); background: #eef5ef; }}
  .panel.clean h2 {{ color: var(--ok); }}
  details.warns > summary {{ cursor: pointer; font-size: 13px; color: var(--muted); margin-top: 6px; }}
  .weekblk {{ margin-top: 26px; }}
  .weekblk > h2 {{
    font-size: 13px; letter-spacing: .08em; text-transform: uppercase;
    color: var(--muted); border-bottom: 1px solid var(--line); padding-bottom: 6px; margin: 0 0 10px;
  }}
  .day {{ margin: 0 0 12px; }}
  .day > h3 {{ font-size: 13px; margin: 10px 0 6px; color: var(--ink); }}
  .row {{
    display: grid; grid-template-columns: 92px 1fr; gap: 10px;
    padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px;
    background: var(--card); margin-bottom: 6px;
  }}
  .row.flagged {{ border-color: #e6b8ab; background: #fdf6f3; }}
  .time {{ font-variant-numeric: tabular-nums; font-size: 13px; color: var(--muted); }}
  .time .allday {{ display: inline-block; font-size: 11px; letter-spacing: .06em;
    text-transform: uppercase; color: var(--muted); }}
  .chip {{
    display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .04em;
    color: #fff; padding: 1px 7px; border-radius: 999px; vertical-align: 1px;
  }}
  .ttl {{ font-weight: 600; }}
  .meta {{ color: var(--muted); font-size: 12.5px; margin-top: 2px; }}
  .badge {{ font-size: 11px; color: var(--flag); font-weight: 700; }}
  footer {{ margin-top: 40px; color: var(--muted); font-size: 12px; }}
  @media (prefers-reduced-motion: no-preference) {{ .cta {{ transition: opacity .15s; }} }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="eyebrow">Subscribable calendar</div>
  <h1>{cal_name}</h1>
  <div class="sub">{term} &middot; {kept_count} events &middot; built {build_time:%Y-%m-%d %H:%M} UTC</div>
</header>

<a class="cta" href="{_esc(subscribe)}">Subscribe in Apple Calendar</a>
<div class="urlrow">Or paste this URL (Settings &rarr; Calendar &rarr; Add Subscribed Calendar):<br>
  <code>{_esc(ics_url)}</code></div>
""")

    # per-subject feeds (color per subject)
    if subject_feeds:
        parts.append(
            '<div class="feeds"><div class="hd">'
            '<div class="t">Want a color per subject?</div>'
            '<div class="d">Subscribe to these instead of the combined feed, then set '
            'each calendar\'s color in Apple Calendar. Suggested swatch shown at left. '
            'Pick either the combined feed above or this set - not both.</div></div>'
        )
        for f in subject_feeds:
            hue = SUBJECT_HUES.get(f["subject"], "#666")
            sub = _webcal(f["url"])
            parts.append(
                f'<div class="feed"><span class="sw" style="background:{hue}"></span>'
                f'<span class="nm">{_esc(f["subject"])}</span>'
                f'<span class="ct">{f["count"]} events</span>'
                f'<a href="{_esc(sub)}">Subscribe</a></div>'
            )
        parts.append("</div>")

    # flags panel
    if review_notes or warnings:
        parts.append('<div class="panel"><h2>Review before you trust this</h2><ul>')
        for n in review_notes:
            parts.append(f"<li>{_esc(n)}</li>")
        parts.append("</ul>")
        if warnings:
            parts.append(f'<details class="warns"><summary>{len(warnings)} automatic validation warning(s)</summary><ul>')
            for w in warnings:
                parts.append(f"<li>{_esc(w)}</li>")
            parts.append("</ul></details>")
        parts.append("</div>")
    else:
        parts.append('<div class="panel clean"><h2>No flags</h2><ul><li>All checks passed with high confidence.</li></ul></div>')

    # events
    flagged_dates = set()  # not strictly needed; per-row flag below
    for b in blocks:
        label = b["label"]
        if label not in grouped:
            continue
        parts.append(f'<section class="weekblk"><h2>{_esc(label)}</h2>')
        for date_str in sorted(grouped[label]):
            d = dt.date.fromisoformat(date_str)
            parts.append(f'<div class="day"><h3>{d:%A} &middot; {d:%b %-d}</h3>')
            for e in sorted(grouped[label][date_str], key=sort_key):
                hue = SUBJECT_HUES.get(e["subject"], "#666")
                flagged = e.get("confidence") in ("low", "medium")
                if e.get("all_day") or not e.get("start"):
                    timecell = '<span class="allday">All&nbsp;day</span>'
                else:
                    timecell = f'{_esc(e["start"])}<br>{_esc(e["end"])}'
                meta_bits = []
                if e.get("lecturer"):
                    meta_bits.append(_esc(e["lecturer"]))
                if e.get("section") and e["section"] != "ALL":
                    meta_bits.append(f'Section {_esc(e["section"])}')
                if e.get("notes"):
                    meta_bits.append(_esc(e["notes"]))
                metaline = " &middot; ".join(meta_bits)
                badge = f' <span class="badge">verify ({_esc(e["confidence"])})</span>' if flagged else ""
                parts.append(f"""  <div class="row{' flagged' if flagged else ''}">
    <div class="time">{timecell}</div>
    <div>
      <span class="chip" style="background:{hue}">{_esc(e['subject'])}</span>
      <span class="ttl"> {_esc(e['activity'])}: {_esc(e['title'])}</span>{badge}
      {f'<div class="meta">{metaline}</div>' if metaline else ''}
    </div>
  </div>""")
            parts.append("</div>")
        parts.append("</section>")

    parts.append("""<footer>
  Read-only subscription. Regenerated automatically when data/schedule.json changes.
  Note: GitHub Pages is publicly readable even on a private repo.
</footer>
</div></body></html>""")
    return "".join(parts)


def write_preview(html_str: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_str)
