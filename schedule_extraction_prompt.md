# Schedule → JSON Extraction Prompt (reusable)

Paste this whole prompt into Claude, then attach the schedule PDF (the scanned
weekly grid). Claude returns a single `schedule.json` you drop into
`data/schedule.json` in your GitHub repo. Do not edit the rules below unless the
source format changes.

---

You are a careful data-extraction engine. I will attach a scanned/photographed
**weekly class schedule** (a medical-school "Calendar of Activities"). Your job
is to convert **every** activity in it into a single JSON object that exactly
matches the schema and rules below. Accuracy and honest uncertainty flags matter
more than filling every field.

## Output format

Return **exactly two things, in this order**:

1. One fenced ```json code block containing the full object (this is the file I
   will commit — nothing else may be inside the block).
2. After the block, a short plain-text list titled **REVIEW FLAGS** summarizing
   every event you marked `"confidence": "low"` or `"medium"`, and any year/date
   corrections you made, so I can eyeball them.

Do not include any prose inside the JSON block. Do not wrap it in Markdown other
than the single fence.

## Schema

```json
{
  "meta": {
    "term": "SY 2026-2027 First Bimonthly",
    "source_title": "<the header title text>",
    "week_blocks": [
      { "label": "AUGUST 3-8, 2026", "start": "2026-08-03", "end": "2026-08-08" }
    ],
    "review_notes": ["<human-readable flags, e.g. 'Corrected year 2025->2026 on Sept 28 week'>"]
  },
  "events": [
    {
      "subject": "PATHOLOGY",
      "activity": "Lecture",
      "title": "Adaptation, Cell Injury and Death",
      "date": "2026-08-07",
      "start": "07:30",
      "end": "09:30",
      "all_day": false,
      "lecturer": "Dr. Alec Maquiling",
      "section": "ALL",
      "notes": "",
      "confidence": "high",
      "source_ref": "AUG 3-8 / 7 FRIDAY"
    }
  ]
}
```

## Field rules

- **subject**: use the label as printed — one of `PATHOLOGY`, `PHARMACOLOGY`,
  `MICRO`, `PD`, `PREVMED`, `PSYCHIATRY`, `RESEARCH`; use `OTHER` if none fit.
- **activity**: one of `Lecture`, `Laboratory`, `Exam`, `CBL`,
  `Independent Study`, `Orientation`, `PD`, `Holiday`, `Other`.
  ("CBL" = Case Based Learning. "PD" cells describe skills/history-taking
  sessions — use activity `PD`.)
- **title**: the topic / chapter / exercise text, cleaned up (e.g.
  "Ch 1-3: Intro, Cell Structure, Classification of Bacteria").
- **date**: ISO `YYYY-MM-DD`. Derive it from the **week-block header** plus the
  **day column label**. See "Dates & the year check" below — this is critical.
- **start / end**: 24-hour `HH:MM`. `null` when `all_day` is true.
- **all_day**: `true` for holidays and for untimed activities (see below).
- **lecturer**: capture any "Dr. ___" named; else empty string.
- **section**: `A`, `B`, or `ALL`. "SECTION A & B" → `ALL`. If unstated → `ALL`.
- **notes**: anything extra (e.g. "Bring medical bag", "Post-test: Projection Exam").
- **confidence**: `high` = explicit time + clear text; `medium` = time or text
  inferred; `low` = guesswork, faint/struck text, or ambiguous.
- **source_ref**: short human pointer back to the cell, e.g. "AUG 10-15 / 12 WEDNESDAY".

## Time normalization

Convert all times to 24-hour `HH:MM`:
- `NN` / `nn` / `noon` = `12:00`.
- Morning-block times are AM; afternoon-block (after the lunch gap) are PM.
- One-sided labels: `"9:30 AM to 12NN"` → `09:30`–`12:00`; `"1:30-3:30pm"` →
  `13:30`–`15:30`; `"8:00am-9:00 am"` → `08:00`–`09:00`; `"10-12 NN"` →
  `10:00`–`12:00`.
- If a cell has an activity but **no clock time** (e.g. "Independent study",
  "Reading assignment: Chapters 1-7", "Orientation" with no hours): set
  `all_day: true`, `start`/`end` = `null`, `confidence: "medium"`, and note it.

## Splitting & holidays

- A single day cell often stacks **multiple activities** (e.g. a morning lecture,
  a morning lab, an afternoon lecture, an afternoon lab). Emit **one event per
  activity** — never merge them.
- Holidays ("HOLIDAY", "HOLIDAY (NINOY AQUINO DAY)", "DON SERGIO OSMEÑA DAY",
  "NATIONAL HEROES DAY", etc.): `activity: "Holiday"`, `all_day: true`,
  `title` = the holiday name, `section: "ALL"`.
- Struck-through / crossed-out text: still capture it, set `confidence: "low"`,
  and note it may be cancelled or moved.

## Dates & the year check (do this carefully)

1. Read the week-block header (e.g. "AUGUST 10-15, 2026") to get the week's Monday.
2. For each event, compute its date from its day column ("13 THURSDAY" → the
   Thursday of that week).
3. **Validate the weekday:** the computed date's weekday MUST equal the column's
   named weekday. If it doesn't, the printed **year is likely wrong** — adjust
   the year (only the year) so the weekday matches, and add a `review_notes`
   entry like "Corrected 2025→2026 for week of Sept 28 (weekday check)."
4. The term year comes from the document title (SY 2026-2027 ⇒ Aug–Oct events are
   **2026**). Any header disagreeing with that is a typo to flag and fix.

## Final checks before returning

- Every event has a valid date within its week block.
- No timed event has `end` ≤ `start`.
- Every stacked activity in every cell became its own event.
- `REVIEW FLAGS` lists all low/medium items and every date/year correction.
