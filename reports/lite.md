# Lite retention report — visual rules and shape

This file defines the LITE retention report. The orchestrator passes it to you alongside the playbook (`d1-retention-analysis.md`) and one or more retention-block specs (each carries its layout, its cohort day, and its retention metric).

- The **playbook** defines methodology — windowing, the three-stage framework, the diagnostic checklist, thresholds, and general output language.
- Each **block spec** defines which retention horizon (D1 / D7 / D30) is being analysed in that block, what cohort day to read, and the layout YAML for the four sections.
- This **template** defines how to emit the blocks and how to write each metric line.

The playbook's general output rules still apply (no internal framework terms, no column names in prose, plain-English directions).

## Important — what "lite" means

Lite refers to the **shape of the written output**, not to the depth of analysis. You must run the full diagnostic flow from the playbook for **every** retention block:

- The forcing rule (`compare_to_baseline(date=cohort_day, metric=<the block's retention_metric>, baseline_kind="stable")`) is mandatory for each block — it sets that block's severity marker.
- The three-stage diagnostic checklist (acquisition mix shift, D0 signals, hook) runs the same way for each cohort day.
- The cross-platform comparator (iOS) is checked per block — even though it is not written into the lite output, the verdict on "is this Android-specific" feeds the impact prose under that block's Retention section.
- Context documents (events, holidays, incidents, release log) load on demand the same way.
- Use `compute_signals_for_day(date=<cohort_day>, retention_metric=<block_retention_metric>, ...)` to get the diagnostic signals for each block in one call.

The only difference between this variant and the deep variant is that the diagnostic conclusions are compressed into per-metric impact sentences and color dots, rather than written as a separate Diagnosis paragraph plus an Evidence section. The work is the same; the write-up is shorter.

If at any point the diagnostic flow says "data not available" or surfaces a thin baseline or a signal-error for a metric, that fact lives in the relevant metric's impact prose — do not drop it just because there is no separate Diagnosis section to put it in.

## Three retention blocks per report

The orchestrator passes **three retention blocks** for a combined run — one each for D1, D7, and D30. Emit them back to back in the order given (D1 first, then D7, then D30).

**No cross-references between blocks.** Each block analyses its own cohort day independently. Do not reference the May 17 cohort's D1 number inside the D7 block; do not say "the same cohort had a worse D1" anywhere; do not compare across blocks. Each block stands alone — that is how the reader is meant to consume them.

If the orchestrator marks a block as **data missing** (the cohort's data was not in the sheet at run time), emit only this stub for that block instead of the four-section layout:

```
# DN — <cohort day> install cohort

> Data missing — the retention column for this cohort was not present in the sheet at run time. The other retention blocks in this email still ran normally; this one will populate on the next scheduled run once the upstream pipeline catches up.
```

Then proceed to the next block.

## Top of every report

**No preamble.** The very first non-empty line of your output MUST be the first block's severity marker (an HTML comment, see below). Do not write any narration, thinking aloud, or process commentary above it — no "I have enough evidence", no "pulling it together", no "let me write the report". Begin at the marker. Stop at the footer. If you need to reason out loud, do it in your private thinking before you start producing the final report; nothing of that should appear in the output.

**Subject line** is set by the orchestrator from `config.yaml`. Do not emit it in the report body. The subject already carries the severity badge (D1's, by default) — do not repeat it in any block's heading.

## Shape of each retention block

Emit each block in this exact order:

1. **Hidden severity marker** as an HTML comment. The orchestrator reads this to set per-block expectations and to pick the subject-line badge. Use the per-retention key — `severity_d1`, `severity_d7`, or `severity_d30` — matching that block's retention horizon:

   ```
   <!-- severity_d1: 🟢 NORMAL -->
   ```

   Use one of: `🔴 ALERT`, `🟡 FLAG`, `🟢 NORMAL`, `🟡 RISE FLAG`, `🟢 RISE ALERT`. Severity selection follows the playbook's "Severity badge rules" (stable-baseline delta on **that block's retention metric**, not always D1).

2. **Block heading** — a level-1 heading that names the retention horizon and the cohort day. No emoji, no badge word.

   ```
   # D1 — May 17 install cohort
   ```

   Format: `# <horizon> — <cohort day in plain English> install cohort`. For D7 the cohort day will be earlier (today − 8). For D30 earlier still (today − 31). The orchestrator tells you the exact cohort day for each block.

3. **One blank line, then `---` (horizontal rule), then the four sections.**

4. **Four sections** in the order given by the block's layout YAML — Engagement, Frequency, Grow Net Installs, Retention. Each section has its own `## <Section Name>` heading and the metrics listed in the layout, sorted by Primary first then Bullet metrics by ascending `bullet_sort`. The Retention section's primary metric is the block's retention horizon (D1 / D7 / D30); the rest of the metrics are the same across blocks.

5. **`---` (horizontal rule)** after the last section of the block to separate it from the next block.

After the final block, emit the footer (color key, see below).

## Metric line shape — applies inside every section of every block

```
<color-dot> **<display_name>: <value>** (<arrow> <delta or "flat"> vs typical <weekday>)

<2–5 sentences of plain-English impact prose. Bold the key numbers and the
key direction phrases within the prose. Explain what the metric did, whether
it has any mechanical effect on the cohort's retention calculation, and the
direction of that effect.>
```

Specifics:

- **Bold the headline** (`**<display_name>: <value>**`) so the eye can scan.
- **Bold key numbers and key direction phrases inside the prose** (e.g. "**9% smaller than typical**", "**no mechanical effect on the cohort's retention**"). Do not bold connective text.
- The parenthetical `(<arrow> <delta> vs typical <weekday>)` follows immediately after the bolded headline, in normal weight.
- **The `<delta>` must be a compact phrase.** Acceptable: `9%`, `6.3 points`, `0.6pp`, `2.2 points`, `4.5 points`, `flat`. **Not** acceptable: `9% below typical Saturday`, `6.3 points below typical Saturday`. The phrase "vs typical <weekday>" is appended once by the template; the delta itself must never repeat any comparator wording.
- **Format time-in-seconds as `Xm Ys`** for any metric measured in seconds (e.g. `avg_engagement_time_per_user`). Display `432 seconds` as `7m 12s`. Display sub-minute values as plain seconds — `45s`. Do not emit raw seconds for values above one minute.
- For metrics with **no baseline** (e.g. `d1_users` / `d7_users` / `d30_users`, raw counts that scale with install volume), omit the parenthetical and write the prose to reflect that this is shown for transparency, not for comparison.
- For **categorical** metrics (e.g. `acquisition_source`), the value is the share breakdown across categories — `organic 58%, paid 32%, WTA 7%, other 3%` — and the delta is the share change of the most-moved category.

### Prose length should match the dot color

Match the depth of the impact prose to the dot. A green metric is not the story — keep its line short. A red metric named as a driver gets the full reasoning. This keeps the visual hierarchy clean: green metrics are quick scans, yellow get a sentence of context, red metrics get attention.

| Dot | Prose length | Tone |
|---|---|---|
| 🟢 | **One short sentence.** Confirm the metric is at typical or moving positively, and stop. | Confirmation. |
| 🟡 | **One to two sentences.** Name the move, name the concern briefly, do not over-explain. | Flag. |
| 🔴 | **Two to four sentences.** Full reasoning — what moved, why it matters mechanically for the cohort's retention, how it ties to the headline diagnosis. | Diagnosis. |

Do not pad green metrics to match the length of yellow or red ones — that flattens the signal you are trying to give.

### Color indicator rules

The dot before the bolded headline tracks the **magnitude of the metric's move**. It does not depend on whether the metric is a mechanical retention input — that nuance belongs in the prose, not the colour.

| Dot | Rule |
|---|---|
| 🟢 | Metric is within ±2% (counts) or ±1pp (rates and shares), OR moving in a positive direction, OR has no baseline to compare against. |
| 🟡 | Metric softened by 2–5% (counts) or 1–2pp (rates and shares). Moderate softness. |
| 🔴 | Metric softened by more than 5% (counts) or more than 2pp (rates and shares). Clear softness — concern regardless of whether the metric is a mechanical retention input. |

Examples:
- Average session time within 0.2% of typical → 🟢.
- DAU down 9% → 🔴.
- Installs down 7% → 🔴.
- D0 notification opt-in down 4.4pp → 🔴.
- DN Retention down 4.5pp → 🔴 (whichever DN this block analyses).
- DN users (raw count, no baseline) → 🟢.

### Direction arrows

| Arrow | Use |
|---|---|
| ↑ | The metric rose vs the baseline. |
| ↓ | The metric fell vs the baseline. |
| → flat | The metric is within ±0.2pp (for rates) / ±1% (for counts) of baseline. |

## Footer — emit once after the last block

```
---

*Color key: 🟢 at typical / positive  ·  🟡 softening  ·  🔴 clear drag*
```

## Baseline rule

Every "vs typical <weekday>" delta uses the **stable weekday baseline** via `compare_to_baseline(metric=<block_retention_metric or supporting_metric>, baseline_kind="stable")`. The weekday in the delta is the cohort day's weekday — so D1, D7, and D30 blocks may each compare against a different weekday baseline depending on which day their cohort falls on.

If a metric does not have a stable-baseline tool wired up, fall back to a 7-day rolling average for that metric and state in the prose for that line that the comparison is a 7-day rolling average rather than the typical-weekday baseline.

## What you do NOT emit in lite mode

- The 6-row status card (that is the deep variant's job).
- The Diagnosis / Evidence / Context & Flags / What to watch next prose sections (deep variant).
- Any prose outside the four sections of each block and the footer.
- Cross-references between blocks ("the same cohort had ...", "as in the D1 block above ..."). Each block is independent.

Note: this list is about the **written output**, not the analysis. You still run the full playbook diagnostic per block. The compressed per-metric impact sentences are the place where your diagnostic conclusions land — they should reflect the same reasoning a deep-variant Diagnosis paragraph would carry, scoped to that block's retention horizon and cohort day.
