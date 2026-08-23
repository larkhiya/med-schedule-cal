# med-schedule-cal

Turns a hand-reviewed `data/schedule.json` into a subscribable Apple Calendar
feed. Claude reads your schedule PDF and produces the JSON; GitHub validates it,
builds `schedule.ics`, and publishes it to GitHub Pages. Your phone subscribes to
that URL once and auto-refreshes forever.

Nothing runs on your device — all compute happens free in GitHub Actions. You
only ever edit one file (`data/schedule.json`) from the GitHub app or website.

```
PDF ──(Claude + extraction prompt)──▶ schedule.json ──(git commit)──▶
      GitHub Actions: validate → build .ics → deploy Pages ──▶ Apple Calendar
```

## What's in here

| Path | Purpose |
|------|---------|
| `data/schedule.json` | The source of truth. The only file you routinely edit. |
| `config.yaml` | Calendar name, section filter, term window, timezone. |
| `schema/schedule.schema.json` | Structural rules for the JSON. |
| `src/` | Validation, ICS generation, preview page, build entrypoint. |
| `tests/` | Unit tests (run automatically in CI). |
| `.github/workflows/build.yml` | Validate → build → publish on every push. |
| `seed_schedule.py` | Dev helper that generated the first `schedule.json`. |

## One-time setup (all doable from an iPhone)

1. **Create a repo** named `med-schedule-cal` and upload these files
   (GitHub app, github.com, or a git client like Working Copy).
2. **Turn on Pages:** repo **Settings → Pages → Build and deployment → Source =
   GitHub Actions**.
3. **Set `config.yaml`** if needed — the calendar name, your `section`
   (`ALL`, `A`, or `B`), and the `term_start`/`term_end` window.
4. **Push to `main`.** The Actions tab shows the build. Green means it published.
5. **Open the site:** `https://<your-username>.github.io/med-schedule-cal/`.
   Review the flags panel and any pink "verify" rows against your PDF.
6. **Subscribe:** tap **Subscribe in Apple Calendar** on that page, or on iPhone
   go to **Settings → Calendar → Accounts → Add Account → Other → Add Subscribed
   Calendar** and paste
   `https://<your-username>.github.io/med-schedule-cal/schedule.ics`.
   *Want a different color per subject?* See **Colors** below — subscribe to the
   per-subject feeds instead of the combined one.
7. **Set refresh:** in that subscribed calendar's settings choose how often iOS
   refetches (e.g. daily). That's it — future updates flow in automatically.

## Every new half-semester

1. Open Claude, paste `schedule_extraction_prompt.md`, attach the new PDF.
2. Claude returns a new `schedule.json` plus a REVIEW FLAGS list. Skim the flags.
3. In the GitHub app/website, open `data/schedule.json`, replace its contents,
   and commit to `main`.
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
or low confidence.

## Colors (one per subject)

Apple Calendar assigns color per *calendar*, not per event — a single subscribed
feed is one color. To get a color per subject, the build also publishes a
separate feed for each subject (`schedule-micro.ics`, `schedule-pathology.ics`,
and so on). To use them:

1. On the published page, use the **"Want a color per subject?"** list and tap
   **Subscribe** on each subject you want (the swatch shows a suggested color).
2. In Apple Calendar, open each subscribed calendar and set its color. On iPhone:
   **Calendar app → Calendars → tap (i) next to the feed → Color**. This only
   changes how *you* see it, so it sticks on your device.

Subscribe to **either** the combined `schedule.ics` **or** the per-subject set —
not both, since they share event IDs and would double up. Turn the per-subject
feeds off by setting `emit_per_subject_feeds: false` in `config.yaml`.

If you'd rather keep one calendar, a lighter option is to prefix event titles
with a colored emoji per subject; that needs a small tweak to `src/ics.py`
(`_summary`) — ask and it's a two-line change.

## Configuration reference

- `section`: `ALL` keeps everything; `A`/`B` keeps that section plus shared
  ("Section A & B") items and drops the other. Currently set to **B**.
- `include_untimed`: set `false` to hide all-day independent-study / reading
  entries and keep only fixed-time classes and exams.
- `emit_per_subject_feeds`: `true` publishes a per-subject feed for color-coding
  (see **Colors**). `false` publishes only the combined `schedule.ics`.
- `timezone`: `Asia/Manila` (fixed UTC+8, no daylight saving). Leave as-is unless
  your schedule is in a different zone.

## Run it locally (optional, needs a computer)

```bash
pip install -r requirements.txt
pytest -q
python src/build.py          # writes site/schedule.ics and site/index.html
open site/index.html         # review
```

## A note on privacy

GitHub Pages is publicly readable **even if the repository is private**. This
calendar contains lecturer names and topics but no personal data. If you'd rather
it not be public at all, don't enable Pages — instead build locally and import
`site/schedule.ics` into Calendar directly (you lose auto-refresh, but nothing is
hosted).
