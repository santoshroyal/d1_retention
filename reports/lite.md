# Lite report — visual rules and shape

This file defines the LITE D1 retention report. The orchestrator passes it to you alongside the playbook (`d1-retention-analysis.md`) and the layout spec (`reports/lite_layout.yaml`).

- The **playbook** defines methodology — windowing, the three-stage framework, the diagnostic checklist, thresholds, and general output language.
- The **layout** defines which metrics to include and the order to emit them.
- This **template** defines how to write each metric's line.

The playbook's general output rules still apply (no internal framework terms, no column names in prose, plain-English directions).

## Important — what "lite" means

Lite refers to the **shape of the written output**, not to the depth of analysis. You must run the full diagnostic flow from the playbook before writing this report:

- The forcing rule (`compare_to_baseline(date=cohort_day, metric="d1_corrected", ..., baseline_kind="stable")`) is mandatory — it sets the severity banner at the top.
- The three-stage diagnostic checklist (acquisition mix shift, D0 signals, hook) runs the same way as the deep variant. Without it, you cannot pick the right color dot for each metric, you cannot write a sensible impact sentence, and you cannot say whether a soft D1 is segment-specific or external.
- The cross-platform comparator (iOS) is checked the same way — even though it is not written into the lite output, the verdict on "is this Android-specific" feeds the impact prose under the Retention section.
- Context documents (events, holidays, incidents, release log) load on demand the same way.

The only difference between this variant and the deep variant is that the diagnostic conclusions are compressed into per-metric impact sentences and color dots, rather than written as a separate Diagnosis paragraph plus an Evidence section. The work is the same; the write-up is shorter.

If at any point the diagnostic flow says "data not available" or surfaces a thin baseline or a signal-error, that fact lives in the relevant metric's impact prose — do not drop it just because there is no separate Diagnosis section to put it in.

## Top of the report

**No preamble.** The very first non-empty line of your output MUST be the severity marker (an HTML comment, see below). Do not write any narration, thinking aloud, or process commentary above it — no "I have enough evidence", no "pulling it together", no "let me write the report". Begin at the marker. Stop at the footer. If you need to reason out loud, do it in your private thinking before you start producing the final report; nothing of that should appear in the output.

1. **Subject line** is set by the orchestrator from `config.yaml`. Do not emit it in the report body. The subject already carries the severity badge — do not repeat the badge in the body banner.

2. **First line** is a hidden severity marker as an HTML comment. The orchestrator reads this to set the email subject. It renders as nothing in the body:

   ```
   <!-- severity: 🟢 NORMAL -->
   ```

   Use one of: `🔴 ALERT`, `🟡 FLAG`, `🟢 NORMAL`, `🟡 RISE FLAG`, `🟢 RISE ALERT`. Severity selection follows the playbook's "Severity badge rules" (stable-baseline delta on `d1_corrected`). Picking the badge requires the forcing rule's `compare_to_baseline(date=cohort_day, metric="d1_corrected", ..., baseline_kind="stable")` call.

3. **Second line** is a level-1 heading carrying the visible title. **No emoji, no badge word — just the short title.**

   ```
   # <short title>
   ```

   Examples of acceptable titles (≤ ~70 characters, one fact, no cause, no comparator):
   - `# D1 fell sharply on Saturday May 16`
   - `# D1 missed Saturday by 3 points`
   - `# D1 held at typical Monday level`

   Do NOT pack the cause, the iOS comparator, or any reasoning into the title. Those belong in the per-metric impact prose below. The title is a short headline, not a sentence. If your title would need a comma, semicolon, or em-dash to fit, it is too long — cut it.

So the first three lines of every lite report are:

```
<!-- severity: 🔴 ALERT -->
# D1 fell sharply on Saturday May 16

```

3. Then one blank line, then `---` (horizontal rule), then begin section 1.

## Body — one section per entry in `lite_layout.yaml`

For each `section` in the layout file, in the order given:

1. Emit `## <section.name>` as the section header.
2. List every metric in the section, sorted: **Primary first**, then **Bullet metrics** by ascending `bullet_sort`.
3. Emit every metric — including ones with no movement or no mechanical impact. The reader expects a consistent shape every day.

### Metric line shape

```
<color-dot> **<display_name>: <value>** (<arrow> <delta or "flat"> vs typical <weekday>)

<2–5 sentences of plain-English impact prose. Bold the key numbers and the
key direction phrases within the prose. Explain what the metric did, whether
it has any mechanical effect on the cohort's D1 calculation, and the
direction of that effect.>
```

Specifics:

- **Bold the headline** (`**<display_name>: <value>**`) so the eye can scan.
- **Bold key numbers and key direction phrases inside the prose** (e.g. "**9% smaller than typical**", "**no mechanical effect on today's D1**"). Do not bold connective text.
- The parenthetical `(<arrow> <delta> vs typical <weekday>)` follows immediately after the bolded headline, in normal weight.
- **The `<delta>` must be a compact phrase.** Acceptable: `9%`, `6.3 points`, `0.6pp`, `2.2 points`, `4.5 points`, `flat`. **Not** acceptable: `9% below typical Saturday`, `6.3 points below typical Saturday`, `9% smaller than the typical Saturday level`. The phrase "vs typical &lt;weekday&gt;" is appended once by the template; the delta itself must never repeat any comparator wording. If you find yourself writing "below typical" inside the delta, stop — the suffix already says it.
- **Format time-in-seconds as `Xm Ys`** for any metric measured in seconds (e.g. `avg_engagement_time_per_user`). Display `432 seconds` as `7m 12s`. Display `90 seconds` as `1m 30s`. Display sub-minute values as plain seconds — `45s`. Do not emit raw seconds for values above one minute.
- For metrics with **no baseline** (e.g. `d1_users`, a raw count that scales with install volume), omit the parenthetical and write the prose to reflect that this is shown for transparency, not for comparison.
- For **categorical** metrics (e.g. `acquisition_source`), the value is the share breakdown across categories — `organic 58%, paid 32%, WTA 7%, other 3%` — and the delta is the share change of the most-moved category (e.g. `organic share down 4.4 points`).

### Prose length should match the dot color

Match the depth of the impact prose to the dot. A green metric is not the story — keep its line short. A red metric named as a driver gets the full reasoning. This keeps the visual hierarchy clean: green metrics are quick scans, yellow get a sentence of context, red metrics get attention.

| Dot | Prose length | Tone |
|---|---|---|
| 🟢 | **One short sentence.** Confirm the metric is at typical or moving positively, and stop. No need to spell out the absence of a mechanical effect on D1 at length. | Confirmation. |
| 🟡 | **One to two sentences.** Name the move, name the concern briefly, do not over-explain. | Flag. |
| 🔴 | **Two to four sentences.** Full reasoning — what moved, why it matters mechanically for D1, how it ties to the headline diagnosis. | Diagnosis. |

Do not pad green metrics to match the length of yellow or red ones — that flattens the signal you are trying to give. A wall of even-length paragraphs makes the dots harder to read, not easier.

### Color indicator rules

The dot before the bolded headline tracks the **magnitude of the metric's move**. It does not depend on whether the metric is a mechanical D1 input — that nuance belongs in the prose, not the colour.

| Dot | Rule |
|---|---|
| 🟢 | Metric is within ±2% (counts) or ±1pp (rates and shares), OR moving in a positive direction, OR has no baseline to compare against. |
| 🟡 | Metric softened by 2–5% (counts) or 1–2pp (rates and shares). Moderate softness. |
| 🔴 | Metric softened by more than 5% (counts) or more than 2pp (rates and shares). Clear softness — concern regardless of whether the metric is a mechanical D1 input. |

Examples (using the actual May 16 data):
- Average session time within 0.2% of typical → 🟢 (near typical).
- DAU down 9% → 🔴 (large move, even though DAU is not a direct D1 input).
- Installs down 7% → 🔴 (large move, even though it is a count not a D1 rate).
- Acquisition mix with organic share down 4.4pp → 🔴 (large move for a share).
- Share of DAU via notifications down 6.3pp → 🔴 (large move).
- D0 uninstalls up 8% → 🔴 (large move; the direction is bad even though absolute number is small).
- D0 login rate up 2.2pp → 🟢 (positive direction).
- D0 notification opt-in down 4.4pp → 🔴 (large move).
- D1 Retention down 4.5pp → 🔴 (large move; the headline metric).
- D1 users (raw count, no baseline) → 🟢.

On a clean day most dots will be 🟢. On an alert day most will be 🔴. Yellow is the transitional zone between the two — not a default for "concerning but not technically a D1 input."

### Direction arrows

| Arrow | Use |
|---|---|
| ↑ | The metric rose vs the baseline. |
| ↓ | The metric fell vs the baseline. |
| → flat | The metric is within ±0.2pp (for rates) / ±1% (for counts) of baseline. |

### Between sections

Insert `---` (horizontal rule) between consecutive sections so the report breathes.

## Footer

After the last section, insert one final horizontal rule and the color key on a single italic line:

```
---

*Color key: 🟢 at typical / positive  ·  🟡 softening  ·  🔴 clear drag*
```

## Baseline rule for lite mode

Every "vs typical <weekday>" delta uses the **stable weekday baseline** via `compare_to_baseline(..., baseline_kind="stable")` — same baseline that drives the severity badge in the deep report. Do not mix metrics across baselines.

If a metric does not have a stable-baseline tool wired up, fall back to a 7-day rolling average for that metric and state in the prose for that line that the comparison is a 7-day rolling average rather than the typical-weekday baseline.

## What you do NOT emit in lite mode

- The 6-row status card (that is the deep variant's job).
- The Diagnosis / Evidence / Context & Flags / What to watch next sections (deep variant).
- Any prose outside the four sections and the footer.

Note: this list is about the **written output**, not the analysis. You still run the full playbook diagnostic before writing. The compressed per-metric impact sentences are the place where your diagnostic conclusions land — they should reflect the same reasoning a deep-variant Diagnosis paragraph would carry.
