# Lite retention report — causality flow

This file defines the LITE retention report. The orchestrator passes it to you alongside the playbook (`d1-retention-analysis.md`) and one block spec per retention horizon (each spec carries the retention metric and the cohort day).

- The **playbook** defines methodology — windowing, the three-stage framework, the diagnostic checklist, thresholds, and general output language.
- Each **block spec** says which retention horizon (D1 / D7 / D30) the block analyses and what cohort day to read.
- This **template** defines how to write each block as a tight causality narrative.

The playbook's general output rules still apply (no internal framework terms, no column names in prose, plain-English directions).

## Important — what "lite" means here

Lite refers to the **shape of the written output**, not the depth of analysis. You run the full diagnostic flow from the playbook for **every** retention block, then compress the conclusions into a tight causality narrative per block.

For every block:

- The forcing rule is mandatory: `compare_to_baseline(date=cohort_day, metric=<the block's retention_metric>, baseline_kind="stable")` is your first call. It sets the block's severity marker.
- Use `compute_signals_for_day(date=cohort_day, retention_metric=<the block's retention_metric>, ...)` for the D0 signals + iOS comparator in one call.
- Use `compute_acquisition_mix_shift(date=cohort_day, platform=android, baseline_days=7)` for the Acquisition mix bullets — it already returns absolute installs, baseline mean, and install ratio per channel. Do not recompute the math.
- The three-stage diagnostic checklist (acquisition mix shift, D0 signals, hook) is what produces the Driver line and the per-block prose.

## Block sequence per report

Emit FOUR blocks back to back in this exact order:

1. **D1 retention block** (full causality flow)
2. **D7 retention block** (compressed)
3. **D30 retention block** (compressed)
4. **Uninstall Rate block** (week-on-week pulse — see "Uninstall Rate block" section below)

**No cross-references between blocks.** Each block analyses its own slice independently. Do not say "the same cohort had a worse D1" inside the D7 block; do not compare across blocks. Each block stands alone.

If the orchestrator marks a block as **data missing**, emit only this stub for that block instead of the full content:

```
## DN — <cohort day> install cohort

> Data missing — the retention column for this cohort was not present in the sheet at run time. The other blocks ran normally; this one will populate on the next scheduled run once the upstream pipeline catches up.
```

Then proceed to the next block.

## Top of every report

**No preamble.** The very first non-empty line of your output MUST be the first block's hidden severity marker (an HTML comment, see below). Do not write any narration, thinking aloud, or process commentary above it. Begin at the marker. Stop at the bottom-line synthesis.

**Subject line** is set by the orchestrator from `config.yaml`. Do not emit it in the report body.

After the three retention severity markers (`severity_d1`, `severity_d7`, `severity_d30`), write a single one-line **"The big picture"** TL;DR that summarises the three retention blocks in plain English, optionally with a brief uninstall-side clause when material. The uninstall block's own severity marker (`severity_uninstall`) goes at the start of the Uninstall Rate block, not at the top. Example shapes:

- `**The big picture:** D1 softened on May 17. D7 and D30 held normal. Uninstall pulse normal.`
- `**The big picture:** All three retention horizons held within normal range; uninstall ratio crossed above 1.0 in the trailing-7d window.`
- `**The big picture:** D7 is the only retention horizon flagged this cycle. Uninstall pulse normal.`

Then a horizontal rule (`---`) and the first block.

## Shape of each retention block

The D1 block is **full**. The D7 and D30 blocks are **compressed** — they emit only the headline, the three short prose paragraphs (What happened / Why it matters / Driver), and the separator. D0 signals, Acquisition mix bullets, What we can't see, and Watch next are emitted **only in the D1 block**, never in D7 or D30.

| Slot | D1 block | D7 block | D30 block |
|---|---|---|---|
| 1. Hidden severity marker | ✓ | ✓ | ✓ |
| 2. Block heading (emoji + horizon + cohort + value) | ✓ | ✓ | ✓ |
| 3. What happened | ✓ | ✓ | ✓ |
| 4. Why it matters | ✓ | ✓ | ✓ |
| 5. Driver | ✓ | ✓ | ✓ |
| 6. D0 experience signals (bullet list) | ✓ | ✗ | ✗ |
| 7. Acquisition mix (bullet list) | ✓ | ✗ | ✗ |
| 8. What we can't see | ✓ | ✗ | ✗ |
| 9. Watch next (when material) | ✓ | ✗ | ✗ |
| 10. What would sharpen this read (block-specific field list) | ✓ | ✓ | ✓ |
| 11. Block separator (`---`) | ✓ | ✓ | ✓ |

**Important — the diagnostic still runs for D7 and D30.** You still call `compute_signals_for_day(date=cohort_day, retention_metric=<dN_corrected>, ...)` and `compute_acquisition_mix_shift(date=cohort_day, platform=android)` for D7 and D30. The Driver line for those blocks must still be grounded in real signal movement and real mix data — it is just that the per-signal bullets and the per-channel bullets do not appear in the email. The reader sees the conclusion, not the evidence.

Emit each block in this exact order. All sub-headings shown below are literal — use them as written.

### 1. Hidden severity marker

```
<!-- severity_d1: 🟡 FLAG -->
```

Use the per-retention key — `severity_d1`, `severity_d7`, or `severity_d30` — matching that block's retention horizon. Use one of: `🔴 ALERT`, `🟡 FLAG`, `🟢 NORMAL`, `🟡 RISE FLAG`, `🟢 RISE ALERT`. Severity selection follows the playbook's "Severity badge rules" (stable-baseline delta on **that block's retention metric**).

The three markers must all appear at the very top of the email body, before "The big picture" line. Put them together so the orchestrator can read them in one pass.

### 2. Block heading

```
## <emoji> DN — <cohort day> cohort: <retention_value>%
```

Examples:

- `## 🟡 D1 — May 17 cohort: 25.07%`
- `## 🟢 D7 — May 11 cohort: 14.82%`
- `## 🟢 D30 — April 18 cohort: 11.33%`

Format:
- Leading emoji matches the block's severity: 🔴, 🟡, or 🟢.
- Horizon label is literal — `D1`, `D7`, or `D30`.
- Cohort day in plain English (`May 17`, not `2026-05-17`).
- Retention value as percentage with two decimals.

### 3. What happened

One bold-labelled paragraph. Two sentences max. Cite both deltas — vs trailing 7-day pace AND vs typical weekday — with the baseline values in parentheses. Examples:

- `**What happened:** D1 came in 1.38pp below trailing 7-day pace (26.44%) and 3.70pp below the typical Sunday level (28.76%).`
- `**What happened:** D7 came in 0.20pp below trailing pace (15.02%) and 1.97pp below the Monday average (16.79%). Inside normal range.`

### 4. Why it matters

One bold-labelled paragraph. The cross-platform comparator and the "is this Android-specific?" judgment. Examples:

- `**Why it matters:** iOS D1 for the same cohort rose 2.03pp. The softness is Android-specific, not a shared news-cycle or external effect.`
- `**Why it matters:** iOS D7 softened 1.27pp on the same cohort. The dip is shared and mild, not a segment failure.`

### 5. Driver

One bold-labelled sentence. The plain-English cause. Examples:

- `**Driver:** Weaker first-session experience on May 17 capped how many users could be reached on May 18.`
- `**Driver:** No single first-day signal points to a cause.`

If the cause is unknown, name the most likely suspect and state why it cannot be confirmed.

### 6. D0 experience signals (vs last 7 days) — **D1 BLOCK ONLY**

**Do not emit this section in the D7 or D30 blocks.** Skip directly from the Driver line to the block separator for D7 and D30. The diagnostic still runs (so the Driver is grounded), but the per-signal bullets stay out of the output for those two blocks.

For D1: bullet list. Exactly four bullets, in this order: Push opt-in, Login rate, Uninstall rate, Average session time.

**Markdown formatting rule:** leave one blank line between the `**D0 experience signals (vs last 7 days):**` label and the first bullet. Without that blank line, the bullets render as inline text instead of a proper list in HTML.

Format per bullet:

```
- <Signal name>: <direction value> — <one-word judgment or short qualifier>
```

Examples:

- `- Push opt-in: down 3.4pp — strongest leading indicator for D1`
- `- Login rate: down 0.5pp — stable`
- `- Uninstall rate: up 1.7pp — worse first impression at scale`
- `- Average session time: down 3.4%. Measures all users, not just the new install cohort — directional only.`

Notes:
- `Average session time` always carries the "measures all users, not just the new install cohort — directional only" qualifier.
- Use whichever signal label and judgment phrasing best fits the situation; the examples above are guidance, not a hard template.
- If a signal is unavailable (signal_errors), say so plainly: `- Push opt-in: data not available — <reason>` and skip the judgment.

### 7. Acquisition mix (vs trailing 7-day pace) — **D1 BLOCK ONLY**

**Do not emit this section in the D7 or D30 blocks.** The mix shift is still computed for D7 and D30 (so the Driver line can reference it when relevant — e.g., "a large paid burst on April 19 compressed the organic share"), but the per-channel bullets do not appear in the email for those blocks.

For D1: bullet list. One bullet per channel — total, organic, paid, WTA, others — in that order. Use the absolute installs and baseline mean returned by `compute_acquisition_mix_shift`.

**Markdown formatting rule:** leave one blank line between the `**Acquisition mix (vs trailing 7-day pace):**` label and the first bullet — same rule as the D0 signals list above.

Format per bullet:

```
- <Channel>: <today_installs> vs <baseline_installs> (~<percent direction>) — <one-line judgment or qualifier>
```

Examples:

- `- Total installs: 3,920 vs 4,097 (~4% below) — not a driver`
- `- Organic: 1,692 vs 2,156 (~22% below); organic share down ~9pp of mix`
- `- Paid: 1,825 vs 1,686 (~8% above) — modest lift`
- `- WTA: 372 vs 221 (~69% above). Lower-intent users can leak into the organic bucket via attribution noise. Flagged as suspicion, medium-to-low probability.`
- `- Others: at typical level`

WTA-specific rule: if WTA install count is materially above its baseline, you may cite the attribution-noise effect as a hedged suspicion. Keep it proportionate — only when D0 signals are otherwise clean.

End the Acquisition mix bullets with **one summary line** when the mix is not a driver, in italics or as a plain trailing bullet — example: `- Acquisition mix on May 11 is not a suppressor of D7; if anything it skewed the cohort more organic.`

### 8. What we can't see — **D1 BLOCK ONLY**

**Do not emit this section in the D7 or D30 blocks.** For D1: one bold-labelled paragraph. State the relevant data gap plainly. For D1, that is push send rate and click-through on the return day. For D7 and D30, it is the longer-tail engagement story between cohort day and return day. Examples:

- `**What we can't see:** Push reach and click-through on May 18 aren't in the data. The likely failure point is upstream anyway: fewer opted-in users means a structurally smaller reachable audience before any push is sent.`
- `**What we can't see:** Week-one push and content cadence pulling the May 11 cohort back over May 12–18 isn't directly measurable at cohort level. Shared iOS softness suggests the overall content week was a touch lighter.`

### 9. Watch next — **D1 BLOCK ONLY**, optional — omit when nothing material

**Do not emit this section in the D7 or D30 blocks.** For D1: optional bold-labelled paragraph. Use this slot when:

- The same retention horizon has been off-baseline for two or more days in a row, OR
- A specific upcoming day's reading would change the read meaningfully, OR
- A particular signal is worth re-checking in the next run.

Use `flag_dip_days(metric=<this block's retention_metric>, days_back=14)` to confirm any multi-day pattern before writing.

If there is nothing material to add, **omit this slot entirely** — do not emit a placeholder.

Examples (only when warranted):

- `**Watch next:** May 16 also closed below its recent pace by a similar amount. Two consecutive Android organic D1 softenings on different weekdays are now on the board. If May 18 lands at or below its Monday level too, the read shifts from one-day blip to wider onboarding or acquisition-quality drift.`

### 10. What would sharpen this read — emit in ALL blocks

A short bold-labelled header followed by a bullet list of fields that would extend the diagnosis for this block but are not in our current data. **Same header sentence in every block**, so the reader learns the pattern after seeing it once. The bullet list is block-specific.

**Header sentence (identical in all three blocks):**

```
**What would sharpen this read:** these fields would extend the diagnosis but are not in our current data.
```

**Per-block bullet list — emit exactly these field names, in this order, no embellishment:**

For the **D1 block**:

```
- D0 second session rate
- D0 deep read rate
```

For the **D7 block**:

```
- D3 retention rate
- Days returned in D1–D6 (return frequency)
- Launcher vs push return ratio in D1–D6
```

For the **D30 block**:

```
- Days returned in D0–D29 (return frequency)
- Hour-based opens in D8–D29
- Avg article completion rate in D1–D7 vs D8–D14
```

**Rules:**
- Do not invent or substitute field names. Emit exactly the strings shown above for the relevant block.
- Do not add a "— not tracked" or "— N/A" suffix on each bullet; the section header already conveys absence.
- Do not editorialise about why these are missing or when they might land. The list is a standing ask, not a discussion.
- Leave one blank line between the bold header and the first bullet (same markdown rule as the other bullet sections).

### 11. Block separator

End each block with `---` (horizontal rule) before the next block starts.

## Uninstall Rate block — emit AFTER the three retention blocks

A fourth block independent of the retention blocks. It analyses uninstall health on a weekly cadence using two comparison windows. Emit it directly after the D30 block's separator and directly before "The bottom line".

**Forcing rule:** Your first MCP call for this block must be `compute_wow_uninstall_pulse(platform='android', acquisition_source='organic')` — **DO NOT pass a `date` parameter**. The tool will use the latest date with install/uninstall data in the sheet, which is typically ONE DAY AHEAD of the D1 cohort day. Install/uninstall is reported same-day (it does not require return-day completion), so the freshest row is the right anchor — using the D1 cohort day would silently throw away a full day of install/uninstall data. The tool returns:
- `date` — the anchor it picked (use this in your table headings)
- `trailing_7d` — current 7d vs prior 7d (current is [date-6, date], prior is [date-13, date-7])
- `week_to_date_mon_to_current` — this week's Monday through `date` vs the same days of the prior week (may be null if `date` is a Monday)
- `severity` — the deterministic severity classification you must use

Do NOT call `compute_uninstall_deep_analysis` from the lite report — that's for the deep variant. The lite block stays focused on the two-window pulse.

Emit each slot in this exact order:

### U1. Hidden severity marker

```
<!-- severity_uninstall: 🔴 ALERT -->
```

Use the `severity` value returned by the tool exactly as-is (one of `🔴 ALERT`, `🟡 FLAG`, `🟢 NORMAL`). This marker does not go to the top of the report — it sits at the start of the Uninstall Rate block.

### U2. Block heading

```
## 📉 <emoji> Uninstall Rate — Week-on-week (<Platform> <acquisition_source>)
```

Example: `## 📉 🔴 Uninstall Rate — Week-on-week (Android organic)`

The leading emoji matches the severity (🔴 / 🟡 / 🟢). Title-case the platform.

### U3. Trailing 7-day comparison table

Format with the exact dates returned by the tool:

```
**Trailing 7 days — <current.start> to <current.end> vs <prior.start> to <prior.end>**

| Metric                    | Prior 7d | Current 7d | Δ          |
|---------------------------|----------|------------|------------|
| Installs                  | <prior.installs>   | <current.installs>     | <deltas.installs_pct>%      |
| Uninstalls                | <prior.uninstalls>  | <current.uninstalls>    | <deltas.uninstalls_pct>%     |
| Net installs              | <prior.net_installs>     | <current.net_installs>     | <deltas.net_installs_abs>    |
| Uninstall / install ratio | <prior.ratio>     | <current.ratio>       | <deltas.ratio>     |
| Same-day drop-off rate    | <prior.drop_off>%   | <current.drop_off>%     | <deltas.drop_off_pp> pp   |
```

- Format installs / uninstalls / net_installs with thousands separators (e.g. `14,741`)
- Format the ratio to two decimals (e.g. `1.06`)
- Format the drop-off rate to two decimals + `%`
- The Δ column shows percent for counts (`-5.5%`), absolute for net (`-1,445`), absolute for ratio (`+0.11`), and `pp` for drop-off (`+0.74 pp`)
- Leave one blank line before the table (sane_lists rendering rule)

### U4. Week-to-date comparison table — emit ONLY when present

If `week_to_date_mon_to_current` is not null in the tool output, emit a second table with the same five-row shape. Title format:

```
**Week-to-date <Mon-to-current-weekday> — <current.start> to <current.end> vs <prior.start> to <prior.end>**
```

For example, if current covers Mon-Wed: `**Week-to-date Mon-Wed — May 18-20 vs May 11-13**`.

Column headers for this table are `Last week` and `This week` (instead of `Prior 7d` / `Current 7d`).

If `week_to_date_mon_to_current` is null (the run anchor is a Monday with no week-to-date data yet), skip this table entirely.

### U5. Reading paragraph

One short paragraph (2-3 sentences max) interpreting both windows. Cite:
- The same-day drop-off pp delta from each window
- The leak ratio (above or below 1.0) from each window
- Any notable single-day cohort anomaly only if the data flagged one (e.g. a daily drop-off rate well above the trailing baseline)

Examples:

- `**Reading:** Both windows agree — this week is structurally weaker on the uninstall side. Trailing-7d drop-off is up 0.74 pp; week-to-date drop-off is up 2.14 pp and the leak ratio crossed above 1.0 in both windows. The early-week stretch (May 18-20) is the worst of the two.`
- `**Reading:** Both windows held in normal range. Trailing-7d drop-off ticked down 0.3 pp; week-to-date is essentially flat. Nothing to act on this cycle.`

### U6. Block separator

End the Uninstall Rate block with `---` (horizontal rule) before "The bottom line".

## Bottom of every report

After the Uninstall Rate block's separator, emit **"The bottom line"** as a bold-labelled one-or-two-sentence synthesis across the three retention blocks AND the uninstall pulse. Examples:

- `**The bottom line:** One short-window retention flag plus an uninstall-side warning — the May 17 D1 dip is the live retention concern, and the uninstall leak ratio has crossed above 1.0 in both this-week views. Worth a closer look this cycle.`
- `**The bottom line:** All three retention horizons held normal and the uninstall pulse stayed in range. Nothing material to act on this cycle.`

This is the report's final line. Nothing follows it — no footer, no color key.

## What you do NOT emit

- No 6-row status card table (that is the deep variant's job).
- No per-metric color dots inside the prose.
- No four-section grid (Engagement / Frequency / Grow Net Installs / Retention).
- No standalone DAU, share-of-DAU-via-notifications, or session-time-as-Engagement-section. Engagement time appears only as one of the four D0 signals.
- No color-key footer.
- No cross-references between blocks.
- **No reference to "the PM", "the user", or any other reader role.** This report is a standalone executive briefing. Do not address whoever asked, do not refer to "the question", do not write "the PM asked", "your question is", "you wanted to know" or any second-person address. The reader is whoever opens the email; treat the report as a written piece that stands on its own. If a focus area was supplied to this run (see the "Focus area for this run" prompt block, if present), let it shape emphasis silently — never name it in the prose.

The lite report is a **causality narrative** — what happened, why it matters, what drove it, what the evidence shows, what we can't see, what to watch next. Three retention-block causality narratives stacked back to back, followed by an Uninstall Rate week-on-week pulse, with a TL;DR on top and a bottom-line synthesis at the end.
