"""Generate the two published pages.

* ``index.html`` - the subscribe page: pick your section, tap to subscribe in
  Apple / Google / any app, and read any review flags. It links to the calendar.
* ``calendar.html`` - a month/list calendar view of the whole term, rendered by
  the vendored Event Calendar library (site/vendor/), section-aware and fast
  (all events are inlined at build time; no runtime fetching).
"""
from __future__ import annotations

import datetime as dt
import html
import json

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

# calendar icon (top-right of the subscribe page)
_CAL_SVG = (
    '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<rect x="3" y="4.5" width="18" height="16" rx="2.5"/>'
    '<path d="M3 9.5h18"/><path d="M8 2.5v4M16 2.5v4"/></svg>'
)


def _esc(s: str) -> str:
    return html.escape(s or "")


def _webcal(url: str) -> str:
    """webcal:// form of an https feed URL. Apple Calendar (and iOS) treat a
    webcal link as 'add a subscribed calendar'."""
    if url.startswith("https://"):
        return "webcal://" + url[len("https://"):]
    if url.startswith("http://"):
        return "webcal://" + url[len("http://"):]
    return url


def _gcal(url: str) -> str:
    """Google Calendar 'add calendar from URL' deep link. Google subscribes via
    the webcal form of the feed and requires it be served over HTTPS. Falls back
    to the plain URL for a relative/local build where no absolute URL exists."""
    wc = _webcal(url)
    if not wc.startswith("webcal://"):
        return url
    return "https://calendar.google.com/calendar/render?cid=" + wc


def _default_section(config: dict) -> str:
    """Section the page loads with before the visitor chooses (and the content of
    the legacy schedule.ics). Falls back to A when config isn't A/B."""
    s = config.get("section", "ALL")
    return s if s in ("A", "B") else "A"


# --------------------------------------------------------------------------- #
#  Subscribe page (index.html)
# --------------------------------------------------------------------------- #

def render(doc: dict, config: dict, report, ics_url: str, kept_count: int,
           build_time: dt.datetime, subject_feeds: list | None = None,
           section_data: dict | None = None, base_url: str = "") -> str:
    subject_feeds = subject_feeds or []
    meta = doc.get("meta", {})
    cal_name = _esc(config.get("calendar_name", "Schedule"))
    term = _esc(meta.get("term", ""))
    review_notes = meta.get("review_notes", [])
    warnings = report.warnings

    chooser = section_data is not None
    default_sec = _default_section(config)

    # ---- header event count (swaps with the section when the chooser is on)
    if chooser:
        ca, cb = section_data["A"]["count"], section_data["B"]["count"]
        init_count = ca if default_sec == "A" else cb
        count_html = f'<span data-count-a="{ca}" data-count-b="{cb}">{init_count}</span>'
    else:
        count_html = str(kept_count)

    # ---- subscribe links (per section when the chooser is on)
    if chooser:
        a_url, b_url = section_data["A"]["url"], section_data["B"]["url"]
        apple_a, apple_b = _webcal(a_url), _webcal(b_url)
        goog_a, goog_b = _gcal(a_url), _gcal(b_url)
        init_apple = apple_a if default_sec == "A" else apple_b
        init_goog = goog_a if default_sec == "A" else goog_b
        init_paste = a_url if default_sec == "A" else b_url
        apple_attrs = f' data-a="{_esc(apple_a)}" data-b="{_esc(apple_b)}"'
        goog_attrs = f' data-a="{_esc(goog_a)}" data-b="{_esc(goog_b)}"'
        paste_attrs = f' data-a="{_esc(a_url)}" data-b="{_esc(b_url)}"'
        cal_href = f"calendar.html?section={default_sec}"
    else:
        init_apple, init_goog, init_paste = _webcal(ics_url), _gcal(ics_url), ics_url
        apple_attrs = goog_attrs = paste_attrs = ""
        cal_href = "calendar.html"

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
    --chip: #f0ece3;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--paper); color: var(--ink);
    font: 15px/1.5 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-text-size-adjust: 100%;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 20px 16px 64px; }}
  header {{ display: flex; align-items: flex-start; gap: 14px;
    border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 8px; }}
  .hd-main {{ flex: 1; min-width: 0; }}
  .eyebrow {{ font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }}
  h1 {{ font-size: 24px; margin: 4px 0 2px; font-weight: 650; letter-spacing: -.01em; }}
  .sub {{ color: var(--muted); font-size: 13px; }}
  .calicon {{
    flex: 0 0 auto; display: inline-flex; align-items: center; justify-content: center;
    width: 46px; height: 46px; border: 1px solid var(--line); border-radius: 12px;
    color: var(--ink); background: var(--card); text-decoration: none;
  }}
  .calicon:hover {{ background: #f3eee4; }}
  .calicon .lbl {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }}
  .seg {{ margin: 16px 0 2px; }}
  .seg .seglabel {{ display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }}
  .segwrap {{ display: inline-flex; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }}
  .segbtn {{
    appearance: none; border: 0; background: var(--card); color: var(--ink);
    font: inherit; font-weight: 600; padding: 9px 18px; cursor: pointer;
  }}
  .segbtn + .segbtn {{ border-left: 1px solid var(--line); }}
  .segbtn.on {{ background: var(--ink); color: #fff; }}
  .cta-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 14px 0 4px; }}
  .cta {{
    display: inline-block; padding: 12px 18px; border-radius: 10px;
    background: var(--ink); color: #fff; text-decoration: none; font-weight: 600;
  }}
  .cta:active {{ opacity: .85; }}
  .urlrow {{ font-size: 12px; color: var(--muted); margin-top: 8px; word-break: break-all; }}
  .urlrow code {{ background: var(--chip); padding: 2px 6px; border-radius: 6px; }}
  .feeds {{ margin: 18px 0 4px; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }}
  .feeds > .hd {{ padding: 12px 16px; background: #f5f1e9; border-bottom: 1px solid var(--line); }}
  .feeds > .hd .t {{ font-weight: 650; }}
  .feeds > .hd .d {{ font-size: 12.5px; color: var(--muted); margin-top: 2px; }}
  .feed {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; padding: 10px 16px; border-top: 1px solid var(--line); }}
  .feed:first-of-type {{ border-top: 0; }}
  .sw {{ width: 14px; height: 14px; border-radius: 4px; flex: 0 0 auto; }}
  .feed .nm {{ flex: 1; font-weight: 600; }}
  .feed .ct {{ font-size: 12px; color: var(--muted); }}
  .feed .links {{ display: flex; gap: 6px; flex: 0 0 auto; margin-left: auto; }}
  .feed a {{ font-size: 13px; font-weight: 600; color: #fff; background: var(--ink);
    padding: 7px 12px; border-radius: 8px; text-decoration: none; white-space: nowrap; }}
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
  footer {{ margin-top: 40px; color: var(--muted); font-size: 12px; }}
  footer a {{ color: var(--ink); }}
  @media (prefers-reduced-motion: no-preference) {{ .cta, .segbtn, .calicon {{ transition: background .15s, opacity .15s; }} }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="hd-main">
    <div class="eyebrow">Subscribable calendar</div>
    <h1>{cal_name}</h1>
    <div class="sub">{term} &middot; {count_html} events &middot; built {build_time:%Y-%m-%d %H:%M} UTC</div>
  </div>
  <a class="calicon" href="{_esc(cal_href)}" aria-label="Open calendar view" title="Open calendar view">{_CAL_SVG}<span class="lbl">Calendar</span></a>
</header>
""")

    # ---- section chooser
    if chooser:
        parts.append(
            '<div class="seg" role="group" aria-label="Which section are you in?">'
            '<span class="seglabel">Which section are you in?</span>'
            '<div class="segwrap">'
            '<button class="segbtn" type="button" data-sec="A" aria-pressed="false">Section A</button>'
            '<button class="segbtn" type="button" data-sec="B" aria-pressed="false">Section B</button>'
            '</div></div>'
        )

    # ---- subscribe buttons + paste URL
    parts.append(f"""<div class="cta-row">
  <a class="cta"{apple_attrs} href="{_esc(init_apple)}">Subscribe in Apple Calendar</a>
  <a class="cta"{goog_attrs} href="{_esc(init_goog)}">Subscribe in Google Calendar</a>
</div>
<div class="urlrow">Any other app (Outlook, Fantastical, Thunderbird&hellip;): add a calendar
  &ldquo;from URL&rdquo; and paste<br>
  <code{paste_attrs}>{_esc(init_paste)}</code></div>
""")

    # ---- per-subject color feeds
    _render_subject_feeds(parts, subject_feeds, section_data, default_sec)

    # ---- flags panel
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

    parts.append(f"""<footer>
  Read-only subscription. Regenerated automatically when data/schedule.json changes.
  <a href="{_esc(cal_href)}">Open the calendar view</a>.<br>
  Note: GitHub Pages is publicly readable even on a private repo.
</footer>
</div>""")

    if chooser:
        parts.append(_TOGGLE_SCRIPT.replace("__DEFAULT__", default_sec))

    parts.append("</body></html>")
    return "".join(parts)


def _render_subject_feeds(parts: list, subject_feeds: list,
                          section_data: dict | None, default_sec: str) -> None:
    """Append the 'color per subject' block. When the section chooser is on, each
    row carries both sections' links (data-a/data-b) so the toggle swaps them."""
    if section_data is not None:
        a_by = {s["subject"]: s for s in section_data["A"]["subjects"]}
        b_by = {s["subject"]: s for s in section_data["B"]["subjects"]}
        order = list(a_by) + [s for s in b_by if s not in a_by]
        if not order:
            return
    elif subject_feeds:
        order = None
    else:
        return

    parts.append(
        '<div class="feeds"><div class="hd">'
        '<div class="t">Want a color per subject?</div>'
        '<div class="d">Subscribe to these instead of the combined feed, then set '
        'each calendar\'s color in your app (Apple Calendar and Google Calendar both '
        'let you recolor a subscribed calendar). Suggested swatch shown at left. '
        'Pick either the combined feed above or this set - not both.</div></div>'
    )

    if section_data is not None:
        for subject in order:
            hue = SUBJECT_HUES.get(subject, "#666")
            fa, fb = a_by.get(subject), b_by.get(subject)
            apple_a = _webcal(fa["url"]) if fa else (_webcal(fb["url"]) if fb else "#")
            apple_b = _webcal(fb["url"]) if fb else apple_a
            goog_a = _gcal(fa["url"]) if fa else (_gcal(fb["url"]) if fb else "#")
            goog_b = _gcal(fb["url"]) if fb else goog_a
            ca = fa["count"] if fa else 0
            cb = fb["count"] if fb else 0
            init_apple = apple_a if default_sec == "A" else apple_b
            init_goog = goog_a if default_sec == "A" else goog_b
            init_ct = ca if default_sec == "A" else cb
            parts.append(
                f'<div class="feed"><span class="sw" style="background:{hue}"></span>'
                f'<span class="nm">{_esc(subject)}</span>'
                f'<span class="ct" data-count-a="{ca}" data-count-b="{cb}">{init_ct} events</span>'
                f'<span class="links">'
                f'<a data-a="{_esc(apple_a)}" data-b="{_esc(apple_b)}" href="{_esc(init_apple)}">Apple</a>'
                f'<a data-a="{_esc(goog_a)}" data-b="{_esc(goog_b)}" href="{_esc(init_goog)}">Google</a>'
                f'</span></div>'
            )
    else:
        for f in subject_feeds:
            hue = SUBJECT_HUES.get(f["subject"], "#666")
            parts.append(
                f'<div class="feed"><span class="sw" style="background:{hue}"></span>'
                f'<span class="nm">{_esc(f["subject"])}</span>'
                f'<span class="ct">{f["count"]} events</span>'
                f'<span class="links">'
                f'<a href="{_esc(_webcal(f["url"]))}">Apple</a>'
                f'<a href="{_esc(_gcal(f["url"]))}">Google</a>'
                f'</span></div>'
            )
    parts.append("</div>")


# Runs on the subscribe page only when the section chooser is on. Swaps every
# section-dependent href/text, updates counts and the calendar link, remembers
# the choice. Kept out of the f-string so JS braces stay literal.
_TOGGLE_SCRIPT = """<script>
(function () {
  var DEFAULT = "__DEFAULT__", KEY = "med-sched-section";
  function apply(sec) {
    document.querySelectorAll("[data-a]").forEach(function (el) {
      var v = sec === "A" ? el.getAttribute("data-a") : el.getAttribute("data-b");
      if (v == null) return;
      if (el.tagName === "A") el.setAttribute("href", v); else el.textContent = v;
    });
    document.querySelectorAll("[data-count-a]").forEach(function (el) {
      var n = sec === "A" ? el.getAttribute("data-count-a") : el.getAttribute("data-count-b");
      el.textContent = el.classList.contains("ct") ? n + " events" : n;
    });
    document.querySelectorAll(".calicon").forEach(function (a) {
      a.setAttribute("href", "calendar.html?section=" + sec);
    });
    document.querySelectorAll(".segbtn").forEach(function (b) {
      var on = b.getAttribute("data-sec") === sec;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    try { localStorage.setItem(KEY, sec); } catch (e) {}
  }
  document.querySelectorAll(".segbtn").forEach(function (b) {
    b.addEventListener("click", function () { apply(b.getAttribute("data-sec")); });
  });
  var saved = null; try { saved = localStorage.getItem(KEY); } catch (e) {}
  apply(saved === "A" || saved === "B" ? saved : DEFAULT);
})();
</script>"""


# --------------------------------------------------------------------------- #
#  Calendar page (calendar.html)
# --------------------------------------------------------------------------- #

def _event_when(e: dict) -> str:
    d = dt.date.fromisoformat(e["date"])
    day = f"{d:%a, %b %-d, %Y}"
    if e.get("all_day") or not e.get("start"):
        return f"{day} · All day"
    return f"{day} · {e['start']}–{e['end']}"


def _calendar_events(doc: dict, config: dict) -> list[dict]:
    """Every event (both sections) as Event Calendar objects, tagged with section
    so the page can filter client-side. Times are naive Manila wall-clock; the
    schedule is shown in its own timezone regardless of the viewer's."""
    from ics import keep_event  # local import to avoid a load-time cycle

    include_untimed = config.get("include_untimed", True)
    out: list[dict] = []
    for i, e in enumerate(doc.get("events", [])):
        if not keep_event(e, "ALL", include_untimed):
            continue
        hue = SUBJECT_HUES.get(e["subject"], "#666")
        all_day = bool(e.get("all_day") or not e.get("start"))
        date = e["date"]
        obj = {
            "id": str(i),
            "title": e.get("title", ""),
            "start": date if all_day else f"{date} {e['start']}:00",
            "allDay": all_day,
            "backgroundColor": hue,
            "textColor": "#ffffff",
            "extendedProps": {
                "sec": e.get("section", "ALL"),
                "subject": e["subject"],
                "activity": e.get("activity", ""),
                "when": _event_when(e),
                "lecturer": e.get("lecturer", ""),
                "sectionLabel": (f"Section {e['section']}"
                                 if e.get("section") and e["section"] != "ALL" else ""),
                "notes": e.get("notes", ""),
                "source": e.get("source_ref", ""),
                "color": hue,
            },
        }
        if not all_day:
            obj["end"] = f"{date} {e['end']}:00"
        out.append(obj)
    return out


def render_calendar(doc: dict, config: dict, section_data: dict | None,
                    build_time: dt.datetime, base_url: str = "") -> str:
    cal_name = config.get("calendar_name", "Schedule")
    default_sec = _default_section(config)
    events = _calendar_events(doc, config)

    # subject legend, in first-seen order across the whole term
    seen: list[str] = []
    for ev in events:
        s = ev["extendedProps"]["subject"]
        if s not in seen:
            seen.append(s)
    legend = "".join(
        f'<span class="lg"><i style="background:{SUBJECT_HUES.get(s, "#666")}"></i>{_esc(s)}</span>'
        for s in seen
    )

    term_start = config.get("term_start", "")
    try:
        term_end_excl = (dt.date.fromisoformat(config["term_end"]) + dt.timedelta(days=1)).isoformat()
    except (KeyError, ValueError):
        term_end_excl = ""

    switch = ""
    if section_data is not None:
        switch = (
            '<div class="seg" role="group" aria-label="Which section are you in?">'
            '<button class="segbtn" type="button" data-sec="A" aria-pressed="false">Section A</button>'
            '<button class="segbtn" type="button" data-sec="B" aria-pressed="false">Section B</button>'
            '</div>'
        )

    page = _CAL_TEMPLATE
    page = page.replace("__TITLE__", _esc(f"{cal_name} · Calendar"))
    page = page.replace("__CALNAME__", _esc(cal_name))
    page = page.replace("__LEGEND__", legend)
    page = page.replace("__SWITCH__", switch)
    page = page.replace("__BUILD__", f"{build_time:%Y-%m-%d %H:%M} UTC")
    # JS-injected values (kept as JSON so quoting/escaping is safe)
    page = page.replace("__EVENTS__", json.dumps(events, separators=(",", ":")))
    page = page.replace("__DEFAULT__", json.dumps(default_sec))
    page = page.replace("__TERM_START__", json.dumps(term_start))
    page = page.replace("__TERM_END_EXCL__", json.dumps(term_end_excl))
    return page


_CAL_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="vendor/event-calendar.min.css">
<style>
  :root {
    --ink: #1c1b19; --muted: #6b6862; --line: #e3ded4; --paper: #faf8f3;
    --card: #ffffff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--paper); color: var(--ink);
    font: 15px/1.5 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-text-size-adjust: 100%;
  }
  .wrap { max-width: 1040px; margin: 0 auto; padding: 16px 16px 64px; }
  .top { display: flex; align-items: center; flex-wrap: wrap; gap: 10px 14px;
    border-bottom: 2px solid var(--ink); padding-bottom: 12px; margin-bottom: 14px; }
  .back { color: var(--ink); text-decoration: none; font-weight: 600; font-size: 14px;
    border: 1px solid var(--line); border-radius: 9px; padding: 7px 12px; background: var(--card); }
  .back:hover { background: #f3eee4; }
  .top h1 { flex: 1; min-width: 0; font-size: 18px; margin: 0; font-weight: 650; letter-spacing: -.01em; }
  .seg { display: inline-flex; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  .segbtn { appearance: none; border: 0; background: var(--card); color: var(--ink);
    font: inherit; font-weight: 600; padding: 8px 15px; cursor: pointer; }
  .segbtn + .segbtn { border-left: 1px solid var(--line); }
  .segbtn.on { background: var(--ink); color: #fff; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 0 0 14px; font-size: 12.5px; color: var(--muted); }
  .legend .lg { display: inline-flex; align-items: center; gap: 6px; }
  .legend i { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }

  /* Event Calendar theming (warm palette) */
  .ec {
    --ec-font-family: inherit;
    --ec-bg-color: var(--card);
    --ec-border-color: var(--line);
    --ec-text-color: var(--ink);
    --ec-day-bg-color: var(--card);
    --ec-today-bg-color: #fbf3e6;
    --ec-highlight-color: #f1ead9;
    --ec-popup-bg-color: var(--card);
    --ec-button-bg-color: var(--card);
    --ec-button-border-color: var(--line);
    --ec-button-text-color: var(--ink);
    --ec-button-active-bg-color: var(--ink);
    --ec-button-active-border-color: var(--ink);
    --ec-button-active-text-color: #fff;
  }
  .ec { border-radius: 12px; }
  .ec-day-head, .ec-toolbar { font-weight: 600; }
  .ec-event { border: 0; }

  #cal[hidden] + .noscript, .noscript { display: none; }
  .noscript.show { display: block; background: #fbeee9; border: 1px solid #e6b8ab;
    border-radius: 10px; padding: 14px 16px; color: #8a3f2f; }

  /* detail overlay */
  .ov { position: fixed; inset: 0; background: rgba(28,27,25,.42);
    display: flex; align-items: center; justify-content: center; padding: 18px; z-index: 50; }
  .ov[hidden] { display: none; }
  .ovcard { background: var(--card); border-radius: 14px; max-width: 440px; width: 100%;
    padding: 20px 20px 22px; box-shadow: 0 18px 50px rgba(0,0,0,.25); position: relative; }
  .d-close { position: absolute; top: 10px; right: 12px; border: 0; background: none;
    font-size: 26px; line-height: 1; color: var(--muted); cursor: pointer; }
  .d-chip { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .04em;
    color: #fff; padding: 2px 9px; border-radius: 999px; }
  .d-title { font-size: 19px; margin: 8px 0 4px; font-weight: 650; letter-spacing: -.01em; }
  .d-when { color: var(--muted); font-size: 13.5px; margin-bottom: 10px; }
  .d-row { display: grid; grid-template-columns: 84px 1fr; gap: 10px; font-size: 14px;
    padding: 6px 0; border-top: 1px solid var(--line); }
  .d-row span { color: var(--muted); }
  @media (max-width: 560px) { .top h1 { flex-basis: 100%; order: -1; } }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a class="back" href="index.html">&larr; Subscribe</a>
    <h1>__CALNAME__</h1>
    __SWITCH__
  </div>
  <div class="legend">__LEGEND__</div>
  <div id="cal"></div>
  <div class="noscript">This calendar needs JavaScript. You can still subscribe or read
    the schedule from the <a href="index.html">subscribe page</a>.</div>
  <div id="ov" class="ov" hidden><div id="ovcard" class="ovcard"></div></div>
</div>
<noscript><style>.noscript{display:block !important;background:#fbeee9;border:1px solid #e6b8ab;border-radius:10px;padding:14px 16px;color:#8a3f2f}</style></noscript>
<script src="vendor/event-calendar.min.js"></script>
<script>
(function () {
  var EVENTS = __EVENTS__, DEFAULT = __DEFAULT__, KEY = "med-sched-section";
  var TERM_START = __TERM_START__, TERM_END_EXCL = __TERM_END_EXCL__;
  if (typeof EventCalendar === "undefined") { document.querySelector(".noscript").classList.add("show"); return; }

  function pickSection() {
    var p = new URLSearchParams(location.search).get("section");
    if (p === "A" || p === "B") return p;
    try { var s = localStorage.getItem(KEY); if (s === "A" || s === "B") return s; } catch (e) {}
    return DEFAULT;
  }
  var section = pickSection();
  function feed() {
    return EVENTS.filter(function (ev) {
      var s = ev.extendedProps.sec; return s === "ALL" || s === section;
    });
  }

  var opts = {
    view: window.matchMedia("(max-width: 640px)").matches ? "listMonth" : "dayGridMonth",
    firstDay: 1,
    height: "auto",
    dayMaxEvents: true,
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    headerToolbar: { start: "title", center: "", end: "dayGridMonth,listMonth today prev,next" },
    buttonText: { today: "Today", dayGridMonth: "Month", listMonth: "List" },
    noEventsContent: "No sessions this month",
    events: feed(),
    eventClick: function (info) { showDetail(info.event); }
  };
  if (TERM_START) { opts.date = TERM_START; }
  if (TERM_START && TERM_END_EXCL) { opts.validRange = { start: TERM_START, end: TERM_END_EXCL }; }

  var ec = EventCalendar.create(document.getElementById("cal"), opts);

  function markButtons() {
    document.querySelectorAll(".segbtn").forEach(function (b) {
      var on = b.getAttribute("data-sec") === section;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }
  function setSection(s) {
    section = s;
    ec.setOption("events", feed());
    markButtons();
    try { localStorage.setItem(KEY, s); } catch (e) {}
    var u = new URL(location); u.searchParams.set("section", s); history.replaceState(null, "", u);
  }
  document.querySelectorAll(".segbtn").forEach(function (b) {
    b.addEventListener("click", function () { setSection(b.getAttribute("data-sec")); });
  });
  markButtons();

  // ---- detail overlay
  var ov = document.getElementById("ov"), card = document.getElementById("ovcard");
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  function row(label, val) {
    return val ? '<div class="d-row"><span>' + label + '</span><div>' + esc(val) + '</div></div>' : "";
  }
  function showDetail(ev) {
    var x = ev.extendedProps;
    var heading = x.activity ? x.activity + ": " + ev.title : ev.title;
    card.innerHTML =
      '<button class="d-close" type="button" aria-label="Close">&times;</button>' +
      '<div class="d-chip" style="background:' + esc(x.color) + '">' + esc(x.subject) + '</div>' +
      '<div class="d-title">' + esc(heading) + '</div>' +
      '<div class="d-when">' + esc(x.when) + '</div>' +
      row("Lecturer", x.lecturer) + row("Section", x.sectionLabel) +
      row("Notes", x.notes) + row("Source", x.source);
    ov.hidden = false;
    card.querySelector(".d-close").addEventListener("click", hide);
  }
  function hide() { ov.hidden = true; }
  ov.addEventListener("click", function (e) { if (e.target === ov) hide(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") hide(); });
})();
</script>
</body>
</html>"""


def write_preview(html_str: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_str)
