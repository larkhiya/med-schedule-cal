"""Generate the two published pages.

* ``index.html`` - the subscribe page. An editorial, question-first flow: the
  visitor picks their section, the app they use, and whether they want a color
  per subject; only then does the matching subscribe output appear. A potato
  mascot randomizes per load (tap it for another - easter egg).
* ``calendar.html`` - a month/list calendar view of the whole term, rendered by
  the vendored Event Calendar library (site/vendor/), section-aware and fast
  (all events are inlined at build time; no runtime fetching).

Both pages share one palette + self-hosted type (Apple Garamond display, Inter
UI) and stay fully self-contained: fonts and images are vendored under
site/fonts and site/img, so there are no external requests.
"""
from __future__ import annotations

import datetime as dt
import html
import json

SUBJECT_HUES = {
    "PATHOLOGY": "#A5FD8B",
    "PHARMACOLOGY": "#FFBB8B",
    "MICRO": "#FF6492",
    "PD": "#FFB1BC",
    "PREVMED": "#F0FF82",
    "PSYCHIATRY": "#99F6FF",
    "RESEARCH": "#FBFF85",
    "OTHER": "#FF9B87",
}

# The subject hues above are all light pastels, so events and chips print dark
# text on them (white would be unreadable). One fixed ink works on all 8.
SUBJECT_TEXT = "#1c1b19"

# calendar icon (bottom-left of the subscribe page, back link on calendar)
_CAL_SVG = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<rect x="3" y="4.5" width="18" height="16" rx="2.5"/>'
    '<path d="M3 9.5h18"/><path d="M8 2.5v4M16 2.5v4"/></svg>'
)

# --------------------------------------------------------------------------- #
#  Shared theme: palette tokens + self-hosted @font-face (both pages)
# --------------------------------------------------------------------------- #

_PALETTE = """
    --blue:#CBE1EC; --paper:#FFFFFF; --ink:#47362E; --hi:#FAFF95; --lark:#680202;
    --ink-70:rgba(71,54,46,.72); --ink-55:rgba(71,54,46,.55); --ink-40:rgba(71,54,46,.40);
    --ink-12:rgba(71,54,46,.12); --ink-07:rgba(71,54,46,.07);
    --hi-soft:rgba(250,255,149,.42);
    --serif:"Apple Garamond","AppleGaramond","EB Garamond",Garamond,"Times New Roman",serif;
    --sans:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
"""

# Relative to the site root, where both pages live, so one path works for both.
_FONT_FACE = """
@font-face{font-family:"Apple Garamond";src:url("fonts/AppleGaramond.ttf") format("truetype");font-weight:400;font-style:normal;font-display:swap;}
@font-face{font-family:"Inter";src:url("fonts/inter-latin-400-normal.woff2") format("woff2");font-weight:400;font-style:normal;font-display:swap;}
@font-face{font-family:"Inter";src:url("fonts/inter-latin-500-normal.woff2") format("woff2");font-weight:500;font-style:normal;font-display:swap;}
@font-face{font-family:"Inter";src:url("fonts/inter-latin-600-normal.woff2") format("woff2");font-weight:600;font-style:normal;font-display:swap;}
"""


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

def _feeds_model(section_data, subject_feeds, ics_url, kept_count, default_sec):
    """Everything the client flow needs to build any output, as plain JSON.

    ``{ <SEC>: { combined:{url}, count, subjects:[{subject,hue,count,url}] } }``
    plus the ordered section list. Only the feed ``url`` is carried; the page
    resolves it against the served origin at runtime and derives the Apple
    (webcal://) and Google deep links there, so the buttons open the right app
    instead of downloading the .ics - both on GitHub Pages and a local preview.
    When the section chooser is off, a single-section model is produced so the
    same UI renders with one section button."""
    def subj_entries(subs):
        return [
            {
                "subject": s["subject"],
                "hue": SUBJECT_HUES.get(s["subject"], "#666"),
                "count": s["count"],
                "url": s["url"],
            }
            for s in subs
        ]

    feeds: dict = {}
    if section_data is not None:
        for sec in ("A", "B"):
            d = section_data.get(sec)
            if not d:
                continue
            feeds[sec] = {
                "combined": {"url": d["url"]},
                "count": d["count"],
                "subjects": subj_entries(d["subjects"]),
            }
        sections = [s for s in ("A", "B") if s in feeds]
    else:
        feeds[default_sec] = {
            "combined": {"url": ics_url},
            "count": kept_count,
            "subjects": subj_entries(subject_feeds),
        }
        sections = [default_sec]
    return feeds, sections


def render(doc: dict, config: dict, report, ics_url: str, kept_count: int,
           build_time: dt.datetime, subject_feeds: list | None = None,
           section_data: dict | None = None, base_url: str = "",
           hero_images: list | None = None) -> str:
    subject_feeds = subject_feeds or []
    hero_images = hero_images or [f"img/{i}.png" for i in range(1, 9)]
    meta = doc.get("meta", {})
    cal_name = config.get("calendar_name", "Schedule")
    term = meta.get("term", "")
    default_sec = _default_section(config)
    review_notes = meta.get("review_notes", [])
    warnings = report.warnings

    feeds, sections = _feeds_model(section_data, subject_feeds, ics_url,
                                   kept_count, default_sec)

    sec_choices = "".join(
        f'<button class="hl" type="button" data-q="section" data-val="{s}" '
        f'aria-pressed="false"><span class="lbl">Section {s}</span></button>'
        for s in sections
    )

    eyebrow = _esc(cal_name) + (f" &middot; {_esc(term)}" if term else "")
    heading = "No more building calendars by hand &mdash; just subscribe."

    page = _INDEX_TEMPLATE
    page = page.replace("__TITLE__", _esc(cal_name))
    page = page.replace("__FONT_FACE__", _FONT_FACE)
    page = page.replace("__PALETTE__", _PALETTE)
    page = page.replace("__EYEBROW__", eyebrow)
    page = page.replace("__HEADING__", heading)
    page = page.replace("__SECTION_CHOICES__", sec_choices)
    page = page.replace("__CAL_ICON__", _CAL_SVG)
    # JS-injected values (JSON so quoting/escaping is safe)
    page = page.replace("__CALSVG__", json.dumps(_CAL_SVG))
    page = page.replace("__FEEDS__", json.dumps(feeds, separators=(",", ":")))
    page = page.replace("__SECTIONS__", json.dumps(sections, separators=(",", ":")))
    page = page.replace("__HERO__", json.dumps(hero_images, separators=(",", ":")))
    page = page.replace("__DEFAULT__", json.dumps(default_sec))
    return page


# The braces below are literal CSS/JS, so this is a plain string with __TOKEN__
# placeholders (not an f-string). Data is injected by render() via .replace().
_INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
__FONT_FACE__
:root {__PALETTE__}
* { box-sizing: border-box; }
html, body { margin: 0; }
body {
  background: var(--blue); color: var(--ink);
  font: 15px/1.5 var(--sans); -webkit-text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
}
a { color: inherit; }

.frame { min-height: 100vh; display: flex; justify-content: center;
  padding: 24px 24px 84px; }
.sheet { width: 100%; max-width: 720px; align-self: flex-start; text-align: center;
  background: var(--paper); border-radius: 22px;
  padding: clamp(26px, 4.6vw, 56px);
  box-shadow: 0 16px 48px rgba(71,54,46,.13); }

/* ---- hero: mascot above a centered display heading ---- */
.hero { display: flex; flex-direction: column; align-items: center; gap: 14px;
  margin-bottom: clamp(26px, 4.5vw, 44px); }
.mascot { flex: 0 0 auto; width: clamp(104px, 22vw, 150px); aspect-ratio: 1;
  position: relative; border: 0; background: none; padding: 0; cursor: pointer;
  appearance: none; -webkit-appearance: none; -webkit-tap-highlight-color: transparent; }
.mascot .layer { position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: contain; opacity: 0; transition: opacity .5s ease; will-change: opacity; }
.mascot .layer.show { opacity: 1; }
.hero-copy { min-width: 0; }
.eyebrow { font-size: 12px; font-weight: 600; letter-spacing: .13em;
  text-transform: uppercase; color: var(--ink-55); margin: 0 0 10px; }
.display { font-family: var(--serif); font-weight: 400;
  font-size: clamp(30px, 6vw, 46px); line-height: 1.06; letter-spacing: -.012em;
  margin: 0 auto; max-width: 15ch; text-wrap: balance; }

/* ---- questions (centered) ---- */
.quiz { display: flex; flex-direction: column; align-items: center;
  gap: clamp(17px, 3vw, 24px); }
.q { min-width: 0; width: 100%; }
.qlabel { font-family: var(--serif); font-size: clamp(18px, 2.5vw, 22px);
  line-height: 1.25; margin: 0 0 11px; }
.qlabel .star { color: var(--lark); font-family: var(--sans);
  font-size: .62em; font-weight: 700; margin-right: 10px; vertical-align: .18em; }
.qlabel .hint { font-family: var(--sans); font-size: 12.5px; font-weight: 400;
  color: var(--ink-55); letter-spacing: 0; }
.choices { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }

/* highlighter button: solid marker fill on select (same feel as the calendar) */
.hl { font-family: var(--sans); font-weight: 500; font-size: 15px; color: var(--ink);
  background: var(--paper); border: 1.6px solid var(--ink-40); border-radius: 11px;
  padding: 9px 18px; cursor: pointer; appearance: none; -webkit-appearance: none;
  -webkit-tap-highlight-color: transparent; }
.hl:hover { background: var(--hi-soft); border-color: var(--ink); }
.hl.on { background: var(--hi); border-color: var(--ink); }
.hl:focus-visible { outline: 2.5px solid var(--ink); outline-offset: 2px; }

/* Q3 collapses smoothly when platform = Other (negative margin eats the flex gap) */
#q-separate { overflow: hidden; max-height: 200px; }
#q-separate.collapsed { max-height: 0; opacity: 0; pointer-events: none;
  margin-top: calc(-1 * clamp(17px, 3vw, 24px)); }

/* ---- generated output ---- */
.out { margin-top: clamp(24px, 4vw, 36px); padding-top: clamp(20px, 3vw, 28px);
  border-top: 2px solid var(--ink); }
.out[hidden] { display: none; }
.out { opacity: 0; transform: translateY(12px); }
.out.show { opacity: 1; transform: none; }
.out-head { font-family: var(--serif); font-weight: 400;
  font-size: clamp(21px, 3vw, 28px); margin: 0 0 6px; letter-spacing: -.01em; }
.out-sub { font-size: 13.5px; color: var(--ink-55); margin: 0 auto 18px;
  max-width: 52ch; }
.out-note { font-size: 12.5px; color: var(--ink-55); margin: 14px 0 0; }

.subbtn { text-decoration: none; }
.subbtn.primary { display: inline-flex; align-items: center; gap: 10px;
  font-weight: 600; font-size: 16px; color: var(--ink); background: var(--hi);
  border: 2px solid var(--ink); border-radius: 13px; padding: 13px 22px;
  box-shadow: 3px 3px 0 var(--ink); }
.subbtn.primary svg { width: 20px; height: 20px; }
.subbtn.primary:hover { transform: translate(-1px,-1px); box-shadow: 4px 4px 0 var(--ink); }
.subbtn.primary:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 var(--ink); }

.subject-grid { display: grid; gap: 10px; justify-content: center;
  grid-template-columns: repeat(auto-fit, minmax(180px, 232px)); text-align: left; }
.subbtn.subj { display: flex; align-items: center; gap: 11px; font-size: 14.5px;
  font-weight: 500; color: var(--ink); background: var(--paper);
  border: 1.6px solid var(--ink-40); border-radius: 12px; padding: 11px 14px; }
.subbtn.subj:hover { border-color: var(--ink); transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(71,54,46,.13); }
.subbtn.subj .sw { width: 16px; height: 16px; border-radius: 5px; flex: 0 0 auto;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,.14); }
.subbtn.subj .nm { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; }
.subbtn.subj .ct { font-size: 12px; color: var(--ink-55); flex: 0 0 auto; }

.urlbox { display: flex; align-items: stretch; justify-content: center; gap: 8px; flex-wrap: wrap; }
.urlbox code { flex: 1 1 260px; min-width: 0; font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: 13px; background: var(--ink-07); border: 1.5px solid var(--ink-40);
  border-radius: 10px; padding: 12px 14px; word-break: break-all; }
.copybtn { font-family: var(--sans); font-weight: 600; font-size: 14px; color: var(--ink);
  background: var(--hi); border: 2px solid var(--ink); border-radius: 10px;
  padding: 0 22px; cursor: pointer; white-space: nowrap;
  appearance: none; -webkit-appearance: none; }

/* ---- fixed footer bar on the blue frame ---- */
.footbar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 14px clamp(16px, 3vw, 28px); pointer-events: none; }
.footbar a { pointer-events: auto; text-decoration: none; font-family: var(--sans); }
.prevlink { display: inline-flex; align-items: center; gap: 10px; color: var(--ink);
  font-weight: 600; font-size: 13.5px; }
.prevlink .calbox { display: inline-flex; align-items: center; justify-content: center;
  width: 36px; height: 36px; border: 1.6px solid var(--ink); border-radius: 10px;
  background: var(--paper); color: var(--ink); }
.prevlink .arrow { display: inline-block; }
.prevlink:hover .calbox { background: var(--hi); transform: translateY(-2px); }
.prevlink:hover .arrow { transform: translateX(-3px); }
.lark { color: var(--lark); font-weight: 700; font-size: 13.5px; letter-spacing: .02em; }
.lark:hover { text-decoration: underline; }

/* ---- motion (opt-in; respects reduced-motion) ---- */
@media (prefers-reduced-motion: no-preference) {
  .hl { transition: background .16s ease, border-color .16s ease, color .16s ease; }
  #q-separate { transition: max-height .34s ease, opacity .26s ease, margin-top .3s ease; }
  .out { transition: opacity .34s ease, transform .34s ease; }
  .subbtn.primary, .subbtn.subj, .copybtn, .prevlink .calbox, .prevlink .arrow {
    transition: transform .16s ease, box-shadow .16s ease, background .16s ease, border-color .16s ease; }
  .copybtn:active { transform: scale(.96); }
  .mascot .layer.show { animation: bob 4.6s ease-in-out infinite; }
  .mascot.pop { animation: pop .42s ease; }
  @keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
  @keyframes pop { 0% { transform: scale(1); } 32% { transform: scale(.9); }
    62% { transform: scale(1.07); } 100% { transform: scale(1); } }
}

/* ---- responsive ---- */
@media (max-width: 767px) {
  /* below the card's width there are no blue rails, so the fixed footer would
     sit over the content: make it a solid bar and reserve space beneath. */
  .footbar { background: var(--paper); border-top: 1.5px solid var(--ink-12);
    box-shadow: 0 -8px 20px rgba(71,54,46,.09); }
  .frame { padding-bottom: 88px; }
}
@media (max-width: 560px) {
  .frame { padding-left: 14px; padding-right: 14px; }
  .sheet { border-radius: 18px; }
  .mascot { width: clamp(112px, 34vw, 132px); }
  .display { font-size: clamp(27px, 8.2vw, 38px); }
  .prevlink .ptext, .lark { font-size: 12.5px; }
}
</style>
</head>
<body>
<div class="frame">
  <main class="sheet">
    <section class="hero">
      <button class="mascot" id="mascot" type="button" aria-label="Surprise potato - tap for another">
        <img class="layer" alt="" decoding="async">
        <img class="layer" alt="" decoding="async">
      </button>
      <div class="hero-copy">
        <p class="eyebrow">__EYEBROW__</p>
        <h1 class="display">__HEADING__</h1>
      </div>
    </section>

    <div class="quiz">
      <div class="q" id="q-section" role="group" aria-label="Which section are you in?">
        <p class="qlabel"><span class="star">&#9733;</span>Which section are you in?</p>
        <div class="choices">__SECTION_CHOICES__</div>
      </div>

      <div class="q" id="q-platform" role="group" aria-label="Where are you adding this calendar?">
        <p class="qlabel"><span class="star">&#9733;</span>Where are you adding this calendar?</p>
        <div class="choices">
          <button class="hl" type="button" data-q="platform" data-val="apple" aria-pressed="false"><span class="lbl">Apple Calendar</span></button>
          <button class="hl" type="button" data-q="platform" data-val="google" aria-pressed="false"><span class="lbl">Google Calendar</span></button>
          <button class="hl" type="button" data-q="platform" data-val="other" aria-pressed="false"><span class="lbl">Other</span></button>
        </div>
      </div>

      <div class="q" id="q-separate" role="group" aria-label="Want a separate color per subject?">
        <p class="qlabel"><span class="star">&#9733;</span>Want a separate color per subject?
          <span class="hint">Off = one color for the whole schedule.</span></p>
        <div class="choices">
          <button class="hl" type="button" data-q="separate" data-val="yes" aria-pressed="false"><span class="lbl">Yes</span></button>
          <button class="hl" type="button" data-q="separate" data-val="no" aria-pressed="false"><span class="lbl">No</span></button>
        </div>
      </div>
    </div>

    <section class="out" id="out" hidden aria-live="polite"></section>
  </main>
</div>

<div class="footbar">
  <a class="prevlink" id="prevlink" href="calendar.html">
    <span class="calbox">__CAL_ICON__</span>
    <span class="ptext"><span class="arrow">&larr;</span> preview calendar here!</span>
  </a>
  <a class="lark" href="https://github.com/larkhiya" target="_blank" rel="noopener">&#9733; by lark</a>
</div>

<script>
(function () {
  var FEEDS = __FEEDS__, SECTIONS = __SECTIONS__, HERO = __HERO__;
  var DEFAULT = __DEFAULT__, CAL_SVG = __CALSVG__, KEY = "med-sched-section";
  var state = { section: null, platform: null, separate: null };
  var out = document.getElementById("out");
  var qSep = document.getElementById("q-separate");
  var prev = document.getElementById("prevlink");

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }

  // Resolve a feed path against the page's real origin, then derive the deep
  // links there - so Apple opens webcal:// and Google opens its add-by-URL page
  // instead of the browser downloading the .ics (works locally and on Pages).
  function absUrl(u) { try { return new URL(u, location.href).href; } catch (e) { return u; } }
  function webcalUrl(u) { return absUrl(u).replace(/^https?:/i, "webcal:"); }
  function gcalUrl(u) { return "https://calendar.google.com/calendar/render?cid=" + encodeURIComponent(webcalUrl(u)); }
  function linkFor(p, u) { return p === "apple" ? webcalUrl(u) : p === "google" ? gcalUrl(u) : absUrl(u); }

  // ---------- mascot: random per load, crossfade to a new one on tap ----------
  (function () {
    var btn = document.getElementById("mascot");
    var layers = btn.querySelectorAll(".layer");
    if (!HERO.length) return;
    var order = HERO.map(function (_, i) { return i; });
    for (var i = order.length - 1; i > 0; i--) {          // Fisher-Yates shuffle
      var j = (Math.random() * (i + 1)) | 0, t = order[i]; order[i] = order[j]; order[j] = t;
    }
    var pos = 0, cur = 0;                                  // cur = visible layer index
    layers[0].src = HERO[order[0]];
    layers[0].classList.add("show");
    function swap(src) {
      var next = layers[cur ^ 1], vis = layers[cur], img = new Image();
      img.onload = function () { next.src = src; next.classList.add("show"); vis.classList.remove("show"); cur ^= 1; };
      img.src = src;
    }
    btn.addEventListener("click", function () {
      pos = (pos + 1) % order.length;
      swap(HERO[order[pos]]);
      btn.classList.remove("pop"); void btn.offsetWidth; btn.classList.add("pop");
    });
    btn.addEventListener("animationend", function (e) { if (e.animationName === "pop") btn.classList.remove("pop"); });
  })();

  // ---------- questions ----------
  function ready() {
    if (!state.section || !state.platform) return false;
    if (state.platform === "other") return true;          // separation is skipped for Other
    return !!state.separate;
  }
  function show(on) {
    if (on) { out.hidden = false; requestAnimationFrame(function () { out.classList.add("show"); }); }
    else { out.classList.remove("show"); out.hidden = true; }
  }
  function update() {
    qSep.classList.toggle("collapsed", state.platform === "other");
    if (state.section && prev) prev.setAttribute("href", "calendar.html?section=" + state.section);
    if (ready()) { renderOut(); show(true); } else { show(false); }
  }

  function copy(text, btn) {
    function done() { var t = btn.textContent; btn.textContent = "Copied!"; setTimeout(function () { btn.textContent = t; }, 1500); }
    function fallback() {
      try { var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta); done(); } catch (e) {}
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }

  function renderOut() {
    var f = FEEDS[state.section]; if (!f) { out.innerHTML = ""; return; }
    var h = "";
    if (state.platform === "other") {
      var url = absUrl(f.combined.url);
      h += '<h2 class="out-head">Add it from a link</h2>';
      h += '<p class="out-sub">In your calendar app choose <b>Add calendar &rarr; From URL</b> and paste this. It refreshes on its own.</p>';
      h += '<div class="urlbox"><code id="feedurl">' + esc(url) + '</code><button class="copybtn" id="copybtn" type="button">Copy</button></div>';
    } else if (state.separate === "no") {
      h += '<h2 class="out-head">You\\'re all set</h2>';
      h += '<p class="out-sub">One calendar, one color. Tap to subscribe &mdash; it stays in sync automatically.</p>';
      h += '<a class="subbtn primary" href="' + esc(linkFor(state.platform, f.combined.url)) + '">' + CAL_SVG + 'Subscribe to Calendar</a>';
      if (f.count) h += '<p class="out-note">' + f.count + ' sessions this term.</p>';
    } else {
      h += '<h2 class="out-head">Subscribe to each subject</h2>';
      h += '<p class="out-sub">Add each one, then set its color in your app &mdash; a calendar per subject.</p>';
      h += '<div class="subject-grid">';
      f.subjects.forEach(function (s) {
        h += '<a class="subbtn subj" href="' + esc(linkFor(state.platform, s.url)) + '">'
          + '<span class="sw" style="background:' + esc(s.hue) + '"></span>'
          + '<span class="nm">' + esc(s.subject) + '</span>'
          + '<span class="ct">' + s.count + '</span></a>';
      });
      h += '</div>';
    }
    out.innerHTML = h;
    var cb = document.getElementById("copybtn");
    if (cb) cb.addEventListener("click", function () { copy(absUrl(f.combined.url), cb); });
  }

  document.querySelectorAll(".hl").forEach(function (b) {
    b.addEventListener("click", function () {
      var q = b.getAttribute("data-q"), v = b.getAttribute("data-val");
      b.closest(".choices").querySelectorAll(".hl").forEach(function (x) {
        var on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-pressed", on ? "true" : "false");
      });
      state[q] = v;
      if (q === "section") { try { localStorage.setItem(KEY, v); } catch (e) {} }
      update();
    });
  });

  // ---------- restore the remembered section (both pages share the key) ----------
  (function () {
    var s = null; try { s = localStorage.getItem(KEY); } catch (e) {}
    if (s && FEEDS[s]) {
      var b = document.querySelector('.hl[data-q="section"][data-val="' + s + '"]');
      if (b) { b.classList.add("on"); b.setAttribute("aria-pressed", "true"); state.section = s;
        if (prev) prev.setAttribute("href", "calendar.html?section=" + s); }
    }
  })();
})();
</script>
</body>
</html>"""


# --------------------------------------------------------------------------- #
#  Calendar page (calendar.html)
# --------------------------------------------------------------------------- #

def _event_when(e: dict) -> str:
    d = dt.date.fromisoformat(e["date"])
    try:
        day = f"{d:%a, %b %-d, %Y}"
    except ValueError:
        day = f"{d:%a, %b %#d, %Y}"
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
        # Mirror the ICS exactly: an all-day event is DTSTART=date, DTEND=date+1
        # (exclusive). Event Calendar needs that explicit end, or it spans the
        # event across the whole grid instead of showing a single day.
        next_day = (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat()
        obj = {
            "id": str(i),
            "title": e.get("title", ""),
            "start": date if all_day else f"{date} {e['start']}:00",
            "end": next_day if all_day else f"{date} {e['end']}:00",
            "allDay": all_day,
            "backgroundColor": hue,
            "textColor": SUBJECT_TEXT,
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
    page = page.replace("__FONT_FACE__", _FONT_FACE)
    page = page.replace("__PALETTE__", _PALETTE)
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
__FONT_FACE__
:root {__PALETTE__}
* { box-sizing: border-box; }
html, body { margin: 0; }
body {
  background: var(--blue); color: var(--ink);
  font: 15px/1.5 var(--sans); -webkit-text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }
.frame { min-height: 100vh; display: flex; justify-content: center; padding: 24px; }
.wrap { width: 100%; max-width: 1080px; align-self: flex-start; background: var(--paper);
  border-radius: 22px; padding: clamp(18px, 3vw, 34px);
  box-shadow: 0 16px 48px rgba(71,54,46,.13); }

.top { display: flex; align-items: center; flex-wrap: wrap; gap: 10px 14px;
  border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 16px; }
.back { display: inline-flex; align-items: center; gap: 7px; color: var(--ink);
  text-decoration: none; font-weight: 600; font-size: 14px; border: 1.6px solid var(--ink-40);
  border-radius: 10px; padding: 7px 13px; background: var(--paper); }
.back:hover { background: var(--hi); border-color: var(--ink); }
.top h1 { flex: 1; min-width: 0; font-family: var(--serif); font-weight: 400;
  font-size: clamp(22px, 3vw, 30px); margin: 0; letter-spacing: -.01em; }
.top .seg { margin-left: auto; }   /* keep the Section A/B switch at the far right */
.lark { color: var(--lark); font-weight: 700; font-size: 13.5px; letter-spacing: .02em;
  text-decoration: none; }
.lark:hover { text-decoration: underline; }
.calfoot { margin-top: 20px; text-align: right; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 0 0 16px; font-size: 12.5px; color: var(--ink-55); }
.legend .lg { display: inline-flex; align-items: center; gap: 6px; }
.legend i { width: 11px; height: 11px; border-radius: 3px; display: inline-block; box-shadow: inset 0 0 0 1px rgba(0,0,0,.12); }

/* segmented controls + pills, styled as highlighter chips (selected = yellow) */
.seg { display: inline-flex; border: 1.6px solid var(--ink-40); border-radius: 11px; overflow: hidden; }
.segbtn { appearance: none; border: 0; background: var(--paper); color: var(--ink);
  font: inherit; font-family: var(--sans); font-weight: 600; padding: 8px 15px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px; }
.segbtn + .segbtn { border-left: 1.6px solid var(--ink-40); }
.segbtn:hover { background: var(--hi-soft); }
.segbtn.on { background: var(--hi); color: var(--ink); }

/* custom calendar toolbar (we hide the library's and render our own so the
   list view can page by week inside a month) */
.ec-toolbar { display: none; }
/* three columns so the month stepper stays visually centered regardless of the
   side controls' widths */
.caltoolbar { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;
  gap: 8px 10px; margin: 0 0 14px; }
.caltoolbar .today { justify-self: start; display: inline-flex; align-items: center; gap: 7px;
  appearance: none; border: 1.6px solid var(--ink-40); background: var(--paper);
  color: var(--ink); font: inherit; font-family: var(--sans); font-weight: 600; padding: 8px 14px; border-radius: 10px; cursor: pointer; }
.caltoolbar .today:hover { background: var(--hi); border-color: var(--ink); }
.monthnav { justify-self: center; display: inline-flex; align-items: center; gap: 4px; }
.monthnav .mlabel { min-width: 148px; text-align: center; font-family: var(--serif); font-weight: 400; font-size: 19px; }
.navbtn { appearance: none; border: 1.6px solid var(--ink-40); background: var(--paper); color: var(--ink);
  width: 36px; height: 36px; border-radius: 10px; font-size: 19px; line-height: 1; cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center; }
.navbtn:hover:not(:disabled) { background: var(--hi); border-color: var(--ink); }
.navbtn:disabled { opacity: .35; cursor: default; }
.viewseg { justify-self: end; }
/* Today / Grid / List carry both an icon and a text label; the label shows on
   wide screens, the icon takes over on narrow ones (see the mobile query). */
.today .ic, .segbtn[data-view] .ic { display: none; align-items: center; }
.today .ic svg, .segbtn[data-view] .ic svg { display: block; }
.weekbar { display: flex; align-items: center; flex-wrap: wrap; justify-content: center;
  gap: 8px 12px; margin: 2px 0 14px; }
.weekbar[hidden] { display: none; }
.weekbar .wlab { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-55); }
.wpills { display: flex; flex-wrap: wrap; gap: 6px; }
.wpill { appearance: none; border: 1.6px solid var(--ink-40); background: var(--paper); color: var(--ink);
  min-width: 34px; height: 34px; padding: 0 11px; border-radius: 999px; font: inherit; font-family: var(--sans); font-weight: 600; cursor: pointer; }
.wpill:hover { background: var(--hi-soft); }
.wpill.on { background: var(--hi); color: var(--ink); border-color: var(--ink); }
.wcap { font-size: 13px; color: var(--ink-55); font-weight: 600; }

/* Event Calendar theming (mapped to the palette) */
.ec {
  --ec-font-family: var(--sans);
  --ec-bg-color: var(--paper);
  --ec-border-color: var(--ink-12);
  --ec-text-color: var(--ink);
  --ec-day-bg-color: var(--paper);
  --ec-today-bg-color: var(--hi-soft);
  --ec-highlight-color: rgba(203,225,236,.55);
  --ec-popup-bg-color: var(--paper);
  --ec-button-bg-color: var(--paper);
  --ec-button-border-color: var(--ink-40);
  --ec-button-text-color: var(--ink);
  --ec-button-active-bg-color: var(--hi);
  --ec-button-active-border-color: var(--ink);
  --ec-button-active-text-color: var(--ink);
}
.ec { border-radius: 14px; }
.ec-day-head, .ec-toolbar { font-weight: 600; }
/* light pastel fills need a hairline so they read against white cells */
.ec-event { border: 0; box-shadow: inset 0 0 0 1px rgba(0,0,0,.12); border-radius: 6px; }
.ec-day-grid .ec-event { margin-inline: 3px; padding: 2px 4px; }

#cal[hidden] + .noscript, .noscript { display: none; }
.noscript.show { display: block; background: var(--hi-soft); border: 1.6px solid var(--ink-40);
  border-radius: 10px; padding: 14px 16px; color: var(--ink); }

/* detail overlay */
.ov { position: fixed; inset: 0; background: rgba(28,27,25,.42);
  display: flex; align-items: center; justify-content: center; padding: 18px; z-index: 50; }
.ov[hidden] { display: none; }
.ovcard { background: var(--paper); border-radius: 16px; max-width: 440px; width: 100%;
  padding: 22px 22px 24px; box-shadow: 0 22px 60px rgba(28,27,25,.3); position: relative; }
.d-close { position: absolute; top: 10px; right: 12px; border: 0; background: none;
  font-size: 26px; line-height: 1; color: var(--ink-55); cursor: pointer; }
.d-chip { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .04em;
  color: var(--ink); padding: 2px 9px; border-radius: 999px; box-shadow: inset 0 0 0 1px rgba(0,0,0,.12); }
.d-title { font-family: var(--serif); font-weight: 400; font-size: 22px; margin: 10px 0 4px; letter-spacing: -.01em; }
.d-when { color: var(--ink-55); font-size: 13.5px; margin-bottom: 10px; }
.d-row { display: grid; grid-template-columns: 84px 1fr; gap: 10px; font-size: 14px;
  padding: 7px 0; border-top: 1px solid var(--ink-12); }
.d-row span { color: var(--ink-55); }

@media (prefers-reduced-motion: no-preference) {
  .segbtn, .navbtn, .today, .wpill, .back { transition: background .16s ease, border-color .16s ease, color .16s ease; }
}
@media (max-width: 560px) {
  .frame { padding: 14px; }
  .wrap { border-radius: 18px; padding: 16px 14px 22px; }
  .top { gap: 8px 10px; padding-bottom: 12px; margin-bottom: 14px; }
  .top h1 { flex-basis: 100%; order: -1; font-size: 22px; }
  .back { font-size: 13px; padding: 6px 11px; }
  .legend { font-size: 11.5px; gap: 5px 10px; margin-bottom: 12px; }
  /* compact toolbar: Today and Grid/List collapse to icons */
  .caltoolbar { gap: 8px; }
  .caltoolbar .today { padding: 8px 11px; gap: 0; }
  .today .tlabel, .segbtn[data-view] .tlabel { display: none; }
  .today .ic, .segbtn[data-view] .ic { display: inline-flex; }
  .segbtn { padding: 8px 12px; font-size: 13.5px; }
  .segbtn[data-view] { padding: 8px 11px; }
  .navbtn { width: 34px; height: 34px; font-size: 18px; }
  .monthnav .mlabel { min-width: 112px; font-size: 16px; }
  /* week pager: drop the label, shrink the pills */
  .weekbar .wlab { display: none; }
  .wpill { min-width: 30px; height: 30px; padding: 0 9px; font-size: 13px; }
  .wcap { flex-basis: 100%; text-align: center; }
  .calfoot { text-align: center; }
}
</style>
</head>
<body>
<div class="frame">
<div class="wrap">
  <div class="top">
    <a class="back" href="index.html">&larr; Subscribe</a>
    <h1>__CALNAME__</h1>
    __SWITCH__
  </div>
  <div class="legend">__LEGEND__</div>
  <div class="caltoolbar">
    <button id="btnToday" class="today" type="button" aria-label="Jump to today">
      <span class="ic"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16" rx="2.5"/><path d="M3 9.5h18"/><path d="M8 2.5v4M16 2.5v4"/><circle cx="12" cy="15" r="1.7" fill="currentColor" stroke="none"/></svg></span><span class="tlabel">Today</span></button>
    <div class="monthnav">
      <button id="mPrev" class="navbtn" type="button" aria-label="Previous month">&lsaquo;</button>
      <span id="mLabel" class="mlabel" aria-live="polite"></span>
      <button id="mNext" class="navbtn" type="button" aria-label="Next month">&rsaquo;</button>
    </div>
    <div class="seg viewseg" role="group" aria-label="Calendar view">
      <button class="segbtn" type="button" data-view="grid" aria-pressed="false" aria-label="Grid view"><span class="ic"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/></svg></span><span class="tlabel">Grid</span></button>
      <button class="segbtn" type="button" data-view="list" aria-pressed="false" aria-label="List view"><span class="ic"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r="1.3" fill="currentColor" stroke="none"/><circle cx="4" cy="12" r="1.3" fill="currentColor" stroke="none"/><circle cx="4" cy="18" r="1.3" fill="currentColor" stroke="none"/></svg></span><span class="tlabel">List</span></button>
    </div>
  </div>
  <div id="weekbar" class="weekbar" role="group" aria-label="Week of the month" hidden>
    <span class="wlab">Week</span>
    <div id="wpills" class="wpills"></div>
    <span id="wcap" class="wcap" aria-live="polite"></span>
  </div>
  <div id="cal"></div>
  <div class="noscript">This calendar needs JavaScript. You can still subscribe or read
    the schedule from the <a href="index.html">subscribe page</a>.</div>
  <div id="ov" class="ov" hidden><div id="ovcard" class="ovcard"></div></div>
  <div class="calfoot"><a class="lark" href="https://github.com/larkhiya" target="_blank" rel="noopener">&#9733; by lark</a></div>
</div>
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

  // ---------- date helpers (events are wall-clock; no timezone math) ----------
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function ymd(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function parseYmd(s) { var p = s.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function addDays(d, n) { var x = new Date(d.getFullYear(), d.getMonth(), d.getDate()); x.setDate(x.getDate() + n); return x; }
  function firstOfMonth(d) { return new Date(d.getFullYear(), d.getMonth(), 1); }
  function sameMonth(a, b) { return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth(); }
  function startOfWeekMon(d) {
    var x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    x.setDate(x.getDate() - ((x.getDay() + 6) % 7));   // back up to Monday
    return x;
  }
  var MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var MON_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  function fmtMonth(d) { return MONTHS[d.getMonth()] + " " + d.getFullYear(); }
  function fmtDay(d) { return MON_ABBR[d.getMonth()] + " " + d.getDate(); }

  // ---------- term bounds (validRange end is exclusive) ----------
  var tStart = TERM_START ? parseYmd(TERM_START) : null;
  var tEndExcl = TERM_END_EXCL ? parseYmd(TERM_END_EXCL) : null;
  var monthMin = tStart ? firstOfMonth(tStart) : null;
  var monthMax = tEndExcl ? firstOfMonth(addDays(tEndExcl, -1)) : null;
  function clampMonth(m) {
    if (monthMin && m < monthMin) return new Date(monthMin);
    if (monthMax && m > monthMax) return new Date(monthMax);
    return m;
  }
  function safeDate(d) {   // keep any navigation date inside validRange
    if (tStart && d < tStart) return tStart;
    if (tEndExcl && d >= tEndExcl) return addDays(tEndExcl, -1);
    return d;
  }
  function weekInTerm(mon) {              // week [mon, mon+7) overlaps the term
    if (!tStart || !tEndExcl) return true;
    return mon < tEndExcl && addDays(mon, 7) > tStart;
  }
  // Mondays whose date lands in month m (each week has one home month, so no week
  // is shown under two months), limited to weeks that overlap the term.
  function weeksOfMonth(m) {
    var mon = startOfWeekMon(firstOfMonth(m));
    if (mon < firstOfMonth(m)) mon = addDays(mon, 7);   // drop the week leaking in from the prev month
    var out = [];
    while (sameMonth(mon, m)) { if (weekInTerm(mon)) out.push(mon); mon = addDays(mon, 7); }
    return out.length ? out : [startOfWeekMon(firstOfMonth(m))];
  }
  function gridDate(m) {   // a day inside month m the grid can safely open on
    var d = firstOfMonth(m);
    return (tStart && d < tStart && sameMonth(d, tStart)) ? tStart : d;
  }

  // ---------- nav state: one focused month drives both views ----------
  var now = new Date();
  var inTerm = tStart && tEndExcl && now >= tStart && now < tEndExcl;
  var focus = inTerm ? now : (tStart || now);
  var curMonth = firstOfMonth(focus);
  var weeks = weeksOfMonth(curMonth);
  var weekIdx = 0;
  for (var wi = 0; wi < weeks.length; wi++) {
    if (focus >= weeks[wi] && focus < addDays(weeks[wi], 7)) { weekIdx = wi; break; }
  }
  var view = window.matchMedia("(max-width: 640px)").matches ? "list" : "grid";

  var opts = {
    view: view === "list" ? "listWeek" : "dayGridMonth",
    date: ymd(safeDate(view === "list" ? weeks[weekIdx] : gridDate(curMonth))),
    firstDay: 1,
    height: "auto",
    dayMaxEvents: true,
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    headerToolbar: { start: "", center: "", end: "" },   // hidden; we render our own below
    noEventsContent: view === "list" ? "No sessions this week" : "No sessions this month",
    events: feed(),
    eventClick: function (info) { showDetail(info.event); }
  };
  if (tStart && tEndExcl) { opts.validRange = { start: TERM_START, end: TERM_END_EXCL }; }

  var ec = EventCalendar.create(document.getElementById("cal"), opts);

  // ---------- custom toolbar: month stepper + week pager ----------
  var elToday = document.getElementById("btnToday");
  var elPrev = document.getElementById("mPrev");
  var elNext = document.getElementById("mNext");
  var elLabel = document.getElementById("mLabel");
  var elWeekbar = document.getElementById("weekbar");
  var elPills = document.getElementById("wpills");
  var elCap = document.getElementById("wcap");

  function renderMonth() {
    elLabel.textContent = fmtMonth(curMonth);
    elPrev.disabled = !!monthMin && !(curMonth > monthMin);
    elNext.disabled = !!monthMax && !(curMonth < monthMax);
  }
  function renderWeeks() {
    elPills.innerHTML = "";
    weeks.forEach(function (mon, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "wpill" + (i === weekIdx ? " on" : "");
      b.textContent = String(i + 1);
      b.setAttribute("aria-label", "Week of " + fmtDay(mon));
      b.setAttribute("aria-pressed", i === weekIdx ? "true" : "false");
      b.addEventListener("click", function () { gotoWeek(i); });
      elPills.appendChild(b);
    });
    var mon = weeks[weekIdx];
    elCap.textContent = fmtDay(mon) + " – " + fmtDay(addDays(mon, 6));
  }
  function showAt() {   // point the calendar at the current month/week for the active view
    ec.setOption("date", ymd(safeDate(view === "list" ? weeks[weekIdx] : gridDate(curMonth))));
  }
  function gotoWeek(i) { weekIdx = i; renderWeeks(); showAt(); }
  function gotoMonth(delta) {
    var m = clampMonth(new Date(curMonth.getFullYear(), curMonth.getMonth() + delta, 1));
    if (sameMonth(m, curMonth)) return;
    curMonth = m; weeks = weeksOfMonth(curMonth); weekIdx = 0;
    renderMonth(); renderWeeks(); showAt();
  }
  function goToday() {
    var t = safeDate(now);
    curMonth = firstOfMonth(t); weeks = weeksOfMonth(curMonth); weekIdx = 0;
    for (var i = 0; i < weeks.length; i++) { if (t >= weeks[i] && t < addDays(weeks[i], 7)) { weekIdx = i; break; } }
    renderMonth(); renderWeeks(); showAt();
  }
  function markViewButtons() {
    document.querySelectorAll(".segbtn[data-view]").forEach(function (b) {
      var on = b.getAttribute("data-view") === view;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }
  function applyView() {
    markViewButtons();
    if (view === "list") {
      ec.setOption("noEventsContent", "No sessions this week");
      ec.setOption("view", "listWeek");
      elWeekbar.hidden = false;
    } else {
      ec.setOption("noEventsContent", "No sessions this month");
      ec.setOption("view", "dayGridMonth");
      elWeekbar.hidden = true;
    }
    showAt();
  }

  elPrev.addEventListener("click", function () { gotoMonth(-1); });
  elNext.addEventListener("click", function () { gotoMonth(1); });
  elToday.addEventListener("click", goToday);
  document.querySelectorAll(".segbtn[data-view]").forEach(function (b) {
    b.addEventListener("click", function () {
      var v = b.getAttribute("data-view");
      if (v !== view) { view = v; applyView(); }
    });
  });

  // ---------- section A/B toggle (unchanged: swaps the event feed) ----------
  function markButtons() {
    document.querySelectorAll(".segbtn[data-sec]").forEach(function (b) {
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
  document.querySelectorAll(".segbtn[data-sec]").forEach(function (b) {
    b.addEventListener("click", function () { setSection(b.getAttribute("data-sec")); });
  });

  // ---------- initial paint (opts already set the view/date, so just chrome) ----------
  renderMonth();
  renderWeeks();
  markViewButtons();
  markButtons();
  elWeekbar.hidden = (view !== "list");

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
