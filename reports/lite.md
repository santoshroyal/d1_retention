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

## Three retention blocks per report

Emit three blocks back to back in this order: D1 first, then D7, then D30.

**No cross-references between blocks.** Each block analyses its own cohort day independently. Do not say "the same cohort had a worse D1" inside the D7 block; do not compare across blocks. Each block stands alone.

If the orchestrator marks a block as **data missing**, emit only this stub for that block instead of the full content:

```
## DN — <cohort day> install cohort

> Data missing — the retention column for this cohort was not present in the sheet at run time. The other blocks ran normally; this one will populate on the next scheduled run once the upstream pipeline catches up.
```

Then proceed to the next block.

## Top of every report

**No preamble.** The very first non-empty line of your output MUST be the first block's hidden severity marker (an HTML comment, see below). Do not write any narration, thinking aloud, or process commentary above it. Begin at the marker. Stop at the bottom-line synthesis.

**Subject line** is set by the orchestrator from `config.yaml`. Do not emit it in the report body.

After the three hidden severity markers, write a single one-line **"The big picture"** TL;DR that summarises the three blocks in plain English. Example shapes:

- `**The big picture:** D1 softened on May 17. D7 and D30 held normal.`
- `**The big picture:** All three retention horizons held within normal range.`
- `**The big picture:** D7 is the only horizon flagged this cycle.`

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

## Bottom of every report

After the last block's separator, emit **"The bottom line"** as a bold-labelled one-or-two-sentence synthesis across all three blocks. Examples:

- `**The bottom line:** One short-window flag, two longer-window normals. The May 17 D1 dip is the only signal worth acting on this cycle. Next reads (May 18 D1, May 16 follow-through) will tell us whether to treat onboarding push opt-in as the live issue.`
- `**The bottom line:** All three horizons held normal. Nothing material to act on this cycle.`

This is the report's final line. Nothing follows it — no footer, no color key.

## What you do NOT emit

- No 6-row status card table (that is the deep variant's job).
- No per-metric color dots inside the prose.
- No four-section grid (Engagement / Frequency / Grow Net Installs / Retention).
- No standalone DAU, share-of-DAU-via-notifications, or session-time-as-Engagement-section. Engagement time appears only as one of the four D0 signals.
- No color-key footer.
- No cross-references between blocks.
- **No reference to "the PM", "the user", or any other reader role.** This report is a standalone executive briefing. Do not address whoever asked, do not refer to "the question", do not write "the PM asked", "your question is", "you wanted to know" or any second-person address. The reader is whoever opens the email; treat the report as a written piece that stands on its own. If a focus area was supplied to this run (see the "Focus area for this run" prompt block, if present), let it shape emphasis silently — never name it in the prose.

The lite report is now a **causality narrative** — what happened, why it matters, what drove it, what the evidence shows, what we can't see, what to watch next. Three of those, stacked, with a TL;DR on top and a bottom-line synthesis at the end.
