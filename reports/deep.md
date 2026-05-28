# Deep retention report — visual rules and shape

This file defines the DEEP retention report. The orchestrator passes it to you alongside the playbook (`d1-retention-analysis.md`) and one or more retention-block specs (each carries its retention horizon and cohort day).

- The **playbook** defines methodology — windowing, the three-stage framework, the diagnostic checklist, thresholds, and general output language.
- Each **block spec** says which retention horizon (D1 / D7 / D30) is being analysed in that block and what cohort day to read.
- This **template** defines the report shape — a fixed status card on top of each block, a free-form diagnosis below.

Diagnosis-first within each block — never walk through all the data and land on a conclusion at the end.

## Block sequence per report

The orchestrator passes **three retention blocks** for a combined run — one each for D1, D7, and D30. Emit them back to back in the order given (D1 first, then D7, then D30), then emit a fourth **Uninstall Rate** block (see "Uninstall Rate — Deep analysis block" section near the end of this template).

Final order: D1 retention → D7 retention → D30 retention → Uninstall Rate.

**No cross-references between blocks.** Each block analyses its own slice independently. Do not reference the D1 cohort's metrics inside the D7 block; do not say "the same cohort had a worse D1" anywhere; do not compare across blocks. Each block stands alone with its own status card and its own diagnosis prose.

If the orchestrator marks a block as **data missing** (the cohort's retention column was not in the sheet at run time), emit only this stub for that block instead of the card + diagnosis:

```
# DN — <cohort day> install cohort

> Data missing — the retention column for this cohort was not present in the sheet at run time. The other retention blocks in this email still ran normally; this one will populate on the next scheduled run once the upstream pipeline catches up.
```

Then proceed to the next block.

## Top of every report

**No preamble.** The very first non-empty line of your output MUST be the first block's severity marker (an HTML comment, see below). Do not write any narration, thinking aloud, or process commentary above it. Begin at the marker. Stop at the end of the last block.

**Subject line** is set by the orchestrator from `config.yaml`. Do not emit it in the report body. The subject already carries the severity badge (D1's, by default).

## Shape of each retention block

Emit each block in this exact order:

### 1. Hidden severity marker

```
<!-- severity_d1: 🔴 ALERT -->
```

Use the per-retention key — `severity_d1`, `severity_d7`, or `severity_d30` — matching that block's retention horizon. Use one of: `🔴 ALERT`, `🟡 FLAG`, `🟢 NORMAL`, `🟡 RISE FLAG`, `🟢 RISE ALERT`. Severity selection follows the playbook's "Severity badge rules" (stable-baseline delta on **that block's retention metric**, not always D1).

### 2. Block heading

```
# D1 — <cohort day> install cohort
```

Format: `# <horizon> — <cohort day in plain English> install cohort`. No emoji, no badge word — the severity badge already lives in the hidden marker above. The orchestrator tells you the exact cohort day for each block.

### 3. Status card (always emit, exact shape)

Open the block with a one-line title under the heading, then a 6-row table. The title is a **short headline (≤ ~70 characters)** stating one fact about that block's retention. Examples: `D1 fell sharply on Saturday May 16`, `D7 held at typical Monday level`. Do not pack the cause or comparator into the title.

```
<short title for this block>

| Field               | Value                                                              |
|---------------------|--------------------------------------------------------------------|
| Cohort / segment    | <YYYY-MM-DD install cohort> · <platform> · <acquisition_source>   |
| <DN> Retention      | <value%>                                                          |
| vs Last 7 Days      | <±X.XXpp> (avg <value%>)                                          |
| vs <Weekday> average| <±X.XXpp> (avg <value%>) — basis for <🔴/🟡/🟢> <ALERT/FLAG/NORMAL/RISE FLAG/RISE ALERT> |
| Primary driver      | <plain English one-sentence cause>                                |
| iOS comparison      | <±X.XXpp> (<iOS direction in plain English> → <looks segment-specific | likely external | unclear>) |
```

`<DN>` is **literal D1, D7, or D30** depending on this block. So the D1 block's card row label reads `D1 Retention`, the D7 block's reads `D7 Retention`, the D30 block's reads `D30 Retention`. Do not write `<DN>` or `DN` literally in the output.

**Comparator rule:** the comparator is always the *other* platform. If the headline segment is Android, the comparator row reports iOS, using the **same retention horizon as this block** (iOS D1 for the D1 block, iOS D7 for the D7 block, iOS D30 for the D30 block).

**Severity badge rules** (first cell of the banner / hidden marker — pick exactly one, based on the **stable baseline** delta for this block's retention horizon):

| Badge | When |
|---|---|
| 🔴 ALERT | Δ ≤ −4pp vs stable baseline |
| 🟡 FLAG | Δ between −2pp and −4pp vs stable baseline |
| 🟢 NORMAL | Δ within ±2pp vs stable baseline |
| 🟡 RISE FLAG | Δ between +2pp and +4pp vs stable baseline |
| 🟢 RISE ALERT | Δ ≥ +4pp vs stable baseline (still surface — what worked is worth knowing) |

**Card field discipline:**
- Every numeric value must come from a tool return, not your own arithmetic.
- The "DN Retention", "vs Last 7 Days", and "vs Weekday average" rows must all use **this block's retention metric** (e.g., `d7_corrected` for the D7 block). Never mix metrics across these three rows.
- If a field is genuinely unknown or not yet computable, write `data not available` — do not omit the row silently.
- Keep the card to exactly these 6 rows. Do not add rows.

**Card-specific output rules:**

- **Primary driver field.** One plain English sentence. No stage numbers, no column names. If cause is unknown, name the most likely suspect and state why it cannot be confirmed.

- **Streak-leads rule.** When this block's retention has been consistently soft (or consistently strong) across multiple recent same-weekdays or consecutive cohort days, the streak is the headline — not the single cohort day. Open the Primary driver field with the streak. Use `flag_dip_days(metric=<this block's retention_metric>, ...)` to confirm.

- **Thin-baseline rule.** When `compare_to_baseline` returns `baseline_meta.n_observations < 4` on the stable baseline, the day-of-week group has very few data points and the mean is unreliable. Append `— THIN BASELINE (n=<n_observations>)` to the "vs Weekday average" row and treat the severity verdict as indicative only.

### 4. Diagnosis (free-form, scoped to this block)

Below the card, write the sections in order. All sections follow the playbook's output language rules — no column names, no stage numbers, no internal framework terms anywhere.

1. **Diagnosis** — flowing paragraph, 2–4 sentences. Cover: (a) what the number was and whether it was soft or strong, (b) whether the cause looks platform-specific or external, (c) the most likely explanation, (d) whether it can be confirmed. Do not pad with filler sentences. Do not restate the headline number verbatim.

2. **Evidence** — three subsections in order:

   **Acquisition** — bullet list. One bullet per source (total, organic, paid, WTA, others) checked against its 7-day average. (Per-source acquisition uses a 7-day trailing comparison deliberately — acquisition mix moves faster than retention and a stable weekday baseline would smooth out the short spikes that are the actual signal here.) If any source is running significantly above normal, flag it as a possible suppressor of organic retention — medium-to-low probability, stated as a suspicion not a conclusion. If all sources are at or below normal, one bullet stating acquisition mix is not the driver.

   **D0 Experience** — bullet list. One bullet per signal: plain English name, value, delta vs last 7 days, one-word judgment (stable / improving / declining). Format: "[Signal name]: [value], [delta] vs last 7 days — [judgment]." If the dictionary flags a signal as not cohort-specific (all-DAU), add: "this measures all users, not just the new install cohort — treat as directional only." If a signal is unavailable, skip it entirely.

   **Return Trigger** — flowing paragraph. For D1: this is the push hook on the return day. For D7 and D30: this is the longer-tail engagement story — push reach, content variety, repeat visits — over the window. If cohort-level data on the return-window mechanism is unavailable, say so plainly.

3. **Context & Flags** — bullet list. Appears ONLY when at least one of these is true: a known holiday or event falls on or near the cohort day or the return day, a logged incident (infra, push, release) overlaps the window, or a notable historical pattern repeats. One bullet per flag, plain English, with the implication for this block's number. If none apply, omit this section entirely.

4. **What to watch next** — flowing paragraph. Appears ONLY when it adds something the Diagnosis did not already say: a broader pattern emerging, an ambiguous signal that needs more time to resolve, or a meaningful directional call about where this retention horizon is heading. Maximum 2–3 sentences. If nothing to add beyond Diagnosis, omit entirely.

For a retention rise, also close with: **is this repeatable?** News-driven → no, will normalise. Mix improvement → maybe, if held. D0 activation improvement → yes, if a product change drove it (name it). Unknown → say so.

### 5. Horizontal rule

End each retention block with `---` (horizontal rule) to visually separate it from the next block.

## Uninstall Rate — Deep analysis block (emit AFTER the three retention blocks)

A fourth block independent of the retention blocks. The deep version extends the lite WoW pulse with composition, weekday pattern, and month-to-date same-period comparison, then closes with a free-form diagnostic paragraph.

**Forcing rule:** Call BOTH MCP tools as your first calls for this block. **DO NOT pass a `date` parameter to either tool** — both tools default to the latest date with install/uninstall data in the sheet, which is typically ONE DAY AHEAD of the D1 cohort day. Install/uninstall is reported same-day (no return-day-completion requirement), so the freshest row is the right anchor — using the D1 cohort day would silently discard a full day of install/uninstall data.

1. `compute_wow_uninstall_pulse(platform='android', acquisition_source='organic')` — returns the trailing-7d window, week-to-date Mon-to-current window, the anchor `date` it picked (use this in table headings), and the deterministic severity classification.
2. `compute_uninstall_deep_analysis(platform='android', acquisition_source='organic')` — returns the D0 vs non-D0 composition for 7d / 15d / 30d windows, the 30-day weekday pattern, and the month-to-date MoM same-period comparison.

Use the `severity` from the WoW tool as the block's badge. Emit each slot in this exact order:

### U1. Hidden severity marker

```
<!-- severity_uninstall: 🔴 ALERT -->
```

Use the WoW pulse tool's `severity` field exactly.

### U2. Block heading

```
# Uninstall Rate — <platform> <acquisition_source>
```

Example: `# Uninstall Rate — Android organic`

No emoji, no badge word — the hidden marker carries the severity. The block stays focused on the uninstall side of the funnel and stands alone from the retention card+diagnosis pattern above.

### U3. WoW status card

Short one-line title under the heading stating one fact about the uninstall pulse (e.g. `Trailing-7d leak ratio crossed above 1.0 with drop-off up 0.74pp`), then two compact comparison tables.

**Trailing 7-day table** — five rows, three columns (Prior 7d, Current 7d, Δ):

```
**Trailing 7 days — <current.start> to <current.end> vs <prior.start> to <prior.end>**

| Metric                    | Prior 7d | Current 7d | Δ          |
|---------------------------|----------|------------|------------|
| Installs                  | ...      | ...        | ...%       |
| Uninstalls                | ...      | ...        | ...%       |
| Net installs              | ...      | ...        | ...        |
| Uninstall / install ratio | ...      | ...        | ...        |
| Same-day drop-off rate    | ...%     | ...%       | ... pp     |
```

**Week-to-date table** — same shape, columns labelled `Last week` and `This week`. Emit ONLY if `week_to_date_mon_to_current` is non-null in the tool output. If null (the anchor is a Monday with no week-to-date data yet), skip this table and explicitly note "No week-to-date data — anchor falls on a Monday." in the diagnostic paragraph.

### U4. D0 vs non-D0 composition

Use `composition` from `compute_uninstall_deep_analysis`. Three rows, one per window:

```
**Uninstall composition — same-day (D0) vs longer-tail (non-D0, installed before today):**

| Window   | Total uninstalls | D0 (same-day) | D0 share | Non-D0 (existing base) | Non-D0 share |
|----------|------------------|---------------|----------|------------------------|--------------|
| Last 7d  | ...              | ...           | ...%     | ...                    | ...%         |
| Last 15d | ...              | ...           | ...%     | ...                    | ...%         |
| Last 30d | ...              | ...           | ...%     | ...                    | ...%         |
```

### U5. 30-day weekday pattern

Use `weekday_pattern_last_30d`. Seven rows in Mon–Sun order. Format averages with thousands separators where appropriate.

```
**Weekday pattern (last 30 days, daily averages):**

| Weekday | Installs | Uninstalls | D0 (same-day) | Net    |
|---------|----------|------------|---------------|--------|
| Mon     | ...      | ...        | ...           | ...    |
| Tue     | ...      | ...        | ...           | ...    |
| Wed     | ...      | ...        | ...           | ...    |
| Thu     | ...      | ...        | ...           | ...    |
| Fri     | ...      | ...        | ...           | ...    |
| Sat     | ...      | ...        | ...           | ...    |
| Sun     | ...      | ...        | ...           | ...    |
```

### U6. Month-to-date same-period comparison

Use `mtd_mom_comparison`. Five rows comparing current month-to-date totals against the same day-of-month window of the prior month:

```
**Month-to-date vs prior-month same period — <current.start> to <current.end> vs <prior.start> to <prior.end>**

| Metric                    | Prior MTD | Current MTD | Δ          |
|---------------------------|-----------|-------------|------------|
| Installs                  | ...       | ...         | ...%       |
| Uninstalls                | ...       | ...         | ...%       |
| Net installs              | ...       | ...         | ...        |
| Uninstall / install ratio | ...       | ...         | ...        |
| Same-day drop-off rate    | ...%      | ...%        | ... pp     |
```

The MTD comparison controls for where-in-the-month we are, so it answers "is this month better or worse than last month so far?" without the drift you get from rolling-30-day windows.

### U7. Diagnostic paragraph (free-form, 4-6 sentences)

Synthesise across the WoW pulse, composition, weekday pattern, and MTD comparison. Cover, in order:

1. What does the WoW pulse say — both windows direction and magnitude.
2. What does the composition tell us — is the leak from new users (D0) or existing base (non-D0), and is that mix stable?
3. Is there a weekday anomaly worth flagging — particularly a recurring spike or trough day?
4. Is the MTD trajectory better or worse than the prior month at the same point, and by how much?
5. A single-sentence verdict at the end: net direction (worsening / stable / improving), where the leak is concentrated, and any single concrete suspect to investigate.

No stage numbers, no column names, no internal framework terms. Plain English throughout. Cite specific numbers from the tool returns when stating findings (e.g. "+0.74 pp drop-off", "90% non-D0 share").

### U8. Horizontal rule

End the Uninstall Rate block with `---` (horizontal rule).

After the Uninstall Rate block, emit nothing further — no footer, no color key. The deep report does not use the lite color-dot system.
