# med-schedule-cal

Turns a hand-reviewed `data/schedule.json` into a subscribable calendar feed
that works in **Apple Calendar, Google Calendar, Outlook, and any other app that
reads iCalendar (`.ics`)** — the universal calendar standard. Claude reads your
schedule PDF and produces the JSON; GitHub validates it, builds `schedule.ics`,
and publishes it to GitHub Pages. Your phone or account subscribes to that URL
once and auto-refreshes forever.

Nothing runs on your device — all compute happens free in GitHub Actions.
Day-to-day you edit the schedule from a **web editor** (`admin.html`) that commits
the change for you; under the hood it's still one file (`data/schedule.json`),
which you can also edit directly from the GitHub app or website.

```
PDF ──(Claude + extraction prompt)──▶ schedule.json ──(git commit)──▶
      GitHub Actions: validate → build .ics → deploy Pages ──▶ Apple / Google / any calendar
```

> **One feed, every app.** `.ics` is a standard, not an Apple format. The same
> published URL is what Apple Calendar, Google Calendar, and Outlook all
> subscribe to — the published page just gives each a one-tap button. There is
> nothing separate to build or host for Google.

The published site is two pages:

- **Subscribe page** (`index.html`) — each student picks **Section A or B** with
  a toggle, then taps **Apple**, **Google**, or copies the URL for any other app.
  The choice is remembered on the device and points every button at that
  section's feed.
- **Calendar page** (`calendar.html`) — the calendar icon (top-right) opens a
  month/list view of the whole term, colored by subject, respecting the same A/B
  choice. It's rendered by a small vendored library (Event Calendar, in
  `vendor/`) with every event inlined at build time, so it's fully self-contained
  and fast — no external requests.

## What's in here

| Path | Purpose |
|------|---------|
| `data/schedule.json` | The source of truth. The only file you routinely edit. |
| `config.yaml` | Calendar name, default section + A/B chooser, term window, timezone. |
| `schema/schedule.schema.json` | Structural rules for the JSON. |
| `src/` | Validation, ICS generation, subscribe + calendar + editor pages, build entrypoint. |
| `vendor/` | Vendored calendar-view library (Event Calendar, MIT), copied into the site. |
| `tests/` | Unit tests (run automatically in CI). |
| `.github/workflows/build.yml` | Validate → build → publish on every push. |
| `seed_schedule.py` | Dev helper that generated the first `schedule.json`. |

## One-time setup (all doable from an iPhone)

1. **Create a repo** named `med-schedule-cal` and upload these files
   (GitHub app, github.com, or a git client like Working Copy).
2. **Turn on Pages:** repo **Settings → Pages → Build and deployment → Source =
   GitHub Actions**.
3. **Set `config.yaml`** if needed — the calendar name, the default `section`
   and whether the A/B chooser is on (`section_chooser`), and the
   `term_start`/`term_end` window.
4. **Push to `main`.** The Actions tab shows the build. Green means it published.
5. **Open the site:** `https://<your-username>.github.io/med-schedule-cal/`.
   Review the flags panel against your PDF, and tap the calendar icon to eyeball
   the whole term in the calendar view.
6. **Subscribe** — first pick your **section (A/B)** on the page; every button
   then points at that section's feed. Tap a one-tap button, or add the feed by
   hand (the section is baked into the filename — `schedule-a.ics` /
   `schedule-b.ics`):
   `https://<your-username>.github.io/med-schedule-cal/schedule-b.ics`.
   - **Apple Calendar / iPhone:** tap **Subscribe in Apple Calendar**, or go to
     **Settings → Calendar → Accounts → Add Account → Other → Add Subscribed
     Calendar** and paste the URL.
   - **Google Calendar:** tap **Subscribe in Google Calendar**, or on the web go
     to **Other calendars → + → From URL**, paste the URL, and **Add calendar**.
     (The Google mobile app can't add a URL feed; do it once on the web and it
     syncs to your phone.)
   - **Outlook / anything else:** use its "add calendar from URL / subscribe"
     option and paste the URL.

   *Want a different color per subject?* See **Colors** below — subscribe to the
   per-subject feeds instead of the combined one.
7. **Set refresh:** Apple lets you pick how often iOS refetches (e.g. daily) in
   the subscribed calendar's settings. Google refreshes URL feeds on its own
   schedule — usually within a day, sometimes longer, and not on demand. Either
   way, future updates flow in automatically with no re-subscribing.

## Editing from the web (no code)

Ad-hoc changes — a class moved, a room or lecturer change, an added holiday —
don't need the PDF or the codebase. Open the **editor** and change them in a form:

`https://<your-username>.github.io/med-schedule-cal/admin.html`

1. **One-time:** create a **fine-grained token** at GitHub → Settings → Developer
   settings → Fine-grained tokens, scoped to **only this repo** with **Contents:
   Read and write**. Paste it into the editor once; it's stored only in your
   browser (never in the page or the repo) and can be revoked anytime.
2. **Edit:** the **Events** tab is the same month/list calendar the public site
   shows — **tap any class to edit it**, or **tap an empty day to add one**
   (a form with dropdowns and date/time pickers; the A/B/All filter and Grid/List
   toggle match the subscribe view). The **Term & settings** tab edits the week
   blocks, reviewer notes, and calendar settings.
3. **Manage schedules:** the **Schedules** tab keeps a library of schedules, with
   **one live at a time** — the live one is what the public feeds serve, so the
   feed URLs never change. Drop or pick a `schedule.json` (e.g. Claude's output
   for a new bimonthly) to add it to the library; **Set active** then Publish
   makes it the live calendar. Each schedule carries a *source* label, so you can
   multi-select and delete them or delete a whole source group at once. The
   archive lives under `library/` (outside `data/`), so managing it never rebuilds
   or disturbs the live feeds.
4. **Publish:** the editor validates as you go — it won't let you publish an event
   whose end is before its start — then commits `data/schedule.json` to `main` for
   you. Actions rebuilds and republishes in ~2 minutes; subscribers refresh on
   their own, with **no re-subscribing**.

The page is published but not linked from the subscribe page, and is inert
without your token, so you can use it from your phone. Settings you change there
are saved to `data/config.local.json`, which the build merges over `config.yaml`.

> **How fast subscribers see it:** publishing is quick, but calendar apps refetch
> on their own clock — **Apple** on the interval you set (often minutes to
> hourly), **Google** more slowly (several hours up to about a day, and it can't
> be forced). That lag is the calendar app's, not this project's — and no
> alternative hosting changes it.

## Every new half-semester

1. Open Claude, paste `schedule_extraction_prompt.md`, attach the new PDF.
2. Claude returns a new `schedule.json` plus a REVIEW FLAGS list. Skim the flags.
3. In the editor's **Schedules** tab, drop or choose the file to add it to the
   library, tap **Set active**, and Publish — or, in the GitHub app/website, open
   `data/schedule.json`, replace its contents, and commit to `main`.
4. Actions rebuilds and republishes in ~2 minutes. Your subscribed calendar
   updates on its next refresh. No re-subscribing needed.

## When a build fails (red X in Actions)

Open the failed run → **Summary**. It lists exactly which event broke which rule
(e.g. an end time before a start time, or a bad subject). Fix that event in
`schedule.json` — or paste the error back to Claude and ask it to correct the
JSON — then commit again. A red build never publishes, so a broken calendar can
never reach your phone.

## How the data is checked

Fatal (build stops, nothing publishes): schema violations, an end time at or
before a start time, a timed event missing its times, duplicate event IDs.

Warnings (published, but flagged on the page for you): **date's weekday doesn't
match the day it's filed under** (this is how the source PDF's 2025/2026 year
typo gets caught), a date outside the term window, times outside 06:00–20:00,
unknown subjects, same-section time overlaps, and anything Claude marked medium
or low confidence. These stay on the subscribe page's flags panel (and the CI job
summary) for you as the maintainer; the extraction-confidence note is **not**
written into the calendar events subscribers see.

## Colors (one per subject)

Apple Calendar and Google Calendar both assign color per *calendar*, not per
event — a single subscribed feed shows as one color. (The **calendar view** page
already colors events by subject; this section is about coloring in your own
calendar app after subscribing.) To get a color per subject, the build also
publishes a separate feed for each subject, per section (`schedule-b-micro.ics`,
`schedule-b-pathology.ics`, and so on — the toggle swaps A/B for you). To use
them:

1. On the published page, use the **"Want a color per subject?"** list and tap
   the **Apple** or **Google** button for each subject you want (the swatch shows
   a suggested color).
2. Set each subscribed calendar's color in your app. This only changes how *you*
   see it, so it sticks to your account/device.
   - **Apple / iPhone:** **Calendar app → Calendars → tap (i) next to the feed →
     Color**.
   - **Google (web):** hover the calendar under **Other calendars** → **⋮** →
     pick a color.

Subscribe to **either** your section's combined feed **or** its per-subject set —
not both, since they share event IDs and would double up. Turn the per-subject
feeds off by setting `emit_per_subject_feeds: false` in `config.yaml`.

If you'd rather keep one calendar, a lighter option is to prefix event titles
with a colored emoji per subject; that needs a small tweak to `src/ics.py`
(`_summary`) — ask and it's a two-line change.

## Configuration reference

- `section`: the toggle's **default** position, and what the legacy
  `schedule.ics` contains. `ALL` keeps everything; `A`/`B` keeps that section plus
  shared ("Section A & B") items and drops the other. Currently set to **B**.
- `section_chooser`: `true` publishes a per-section feed set (`schedule-a.ics` /
  `schedule-b.ics` + per-section color feeds) and shows the A/B toggle so each
  subscriber picks their own section. `false` publishes a single section (the
  `section` value above) with no toggle.
- `include_untimed`: set `false` to hide all-day independent-study / reading
  entries and keep only fixed-time classes and exams.
- `emit_per_subject_feeds`: `true` publishes a per-subject feed for color-coding
  (see **Colors**). `false` publishes only the combined feed(s).
- `timezone`: `Asia/Manila` (fixed UTC+8, no daylight saving). Leave as-is unless
  your schedule is in a different zone.
- `data/config.local.json` (optional, written by the web editor): overrides the
  matching keys above so the documented `config.yaml` is never rewritten from the
  browser. Delete it to fall back entirely to `config.yaml`. `timezone` and
  `uid_namespace` are intentionally not web-editable — changing `uid_namespace`
  would orphan every existing subscription.

## Run it locally (optional, needs a computer)

```bash
pip install -r requirements.txt
pytest -q
python src/build.py          # writes the feeds, index.html, calendar.html, vendor/
open site/index.html         # review (calendar.html needs an http server, not file://)
```

The calendar page loads its library over `http`, so to preview it locally serve
the folder instead of opening the file directly:

```bash
python -m http.server -d site 8000    # then open http://localhost:8000/calendar.html
```

## A note on privacy

GitHub Pages is publicly readable **even if the repository is private**. This
calendar contains lecturer names and topics but no personal data. If you'd rather
it not be public at all, don't enable Pages — instead build locally and import
`site/schedule.ics` into Calendar directly (you lose auto-refresh, but nothing is
hosted).
