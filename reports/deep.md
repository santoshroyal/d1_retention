# Deep report — visual rules and shape

This file defines the DEEP D1 retention report. The orchestrator passes it to you alongside the playbook (`d1-retention-analysis.md`).

- The **playbook** defines methodology — windowing, the three-stage framework, the diagnostic checklist, thresholds, and general output language.
- This **template** defines the report shape — a fixed status card on top, a free-form diagnosis below.

Diagnosis-first — never walk through all the data and land on a conclusion at the end.

**No preamble.** The very first non-empty line of your output MUST be the hidden severity marker (HTML comment, see below). Do not write any narration, thinking aloud, or process commentary above it — no "I have enough evidence", no "pulling it together", no "let me write the report". Begin at the marker. Stop at the end of Part 2. If you need to reason out loud, do it in your private thinking before producing the final report; nothing of that should appear in the output.

The subject line already carries the severity badge — do not repeat the badge in the body banner. The visible body banner is a plain title; the orchestrator reads the hidden marker to set the subject.

## Part 1 — Status card (always emit, exact shape)

Open the report with:

1. A hidden severity marker as an HTML comment (the orchestrator reads this to set the subject; it renders as nothing in the body):

   ```
   <!-- severity: 🔴 ALERT -->
   ```

   Use one of: `🔴 ALERT`, `🟡 FLAG`, `🟢 NORMAL`, `🟡 RISE FLAG`, `🟢 RISE ALERT`.

2. A plain one-line title (no emoji, no badge word) — just the short headline.

3. Then the 6-row table.

The title is a **short headline (≤ ~70 characters)** stating one fact about D1. Do not pack the cause, the iOS comparator, or any reasoning into the title — those go in the card rows and the Diagnosis paragraph below. If your title would need a comma, semicolon, or em-dash to fit, it is too long; cut it.

Examples of acceptable titles:
- `D1 fell sharply on Saturday May 16`
- `D1 missed Saturday by 3 points`
- `D1 held at typical Monday level`

```
<!-- severity: 🔴 ALERT -->
<short title>

| Field               | Value                                                              |
|---------------------|--------------------------------------------------------------------|
| Cohort / segment    | <YYYY-MM-DD install cohort> · <platform> · <acquisition_source>   |
| D1 Retention        | <value%>                                                          |
| vs Last 7 Days      | <±X.XXpp> (avg <value%>)                                          |
| vs <Weekday> average| <±X.XXpp> (avg <value%>) — basis for <🔴/🟡/🟢> <ALERT/FLAG/NORMAL/RISE FLAG/RISE ALERT> |
| Primary driver      | <plain English one-sentence cause — see card-specific rules below>|
| iOS comparison      | <±X.XXpp> (<iOS direction in plain English> → <looks segment-specific | likely external | unclear>) |
```

**Comparator rule:** the comparator is always the *other* platform. If the headline segment is Android, the comparator row reports iOS. If the headline segment is iOS, the comparator row reports Android. Use the same metric the Headline picked (see the playbook's Forcing rule).

**Severity badge rules** (first cell of the banner — pick exactly one, based on the **stable baseline** delta):

| Badge | When |
|---|---|
| 🔴 ALERT | Δ ≤ −4pp vs stable baseline |
| 🟡 FLAG | Δ between −2pp and −4pp vs stable baseline |
| 🟢 NORMAL | Δ within ±2pp vs stable baseline |
| 🟡 RISE FLAG | Δ between +2pp and +4pp vs stable baseline |
| 🟢 RISE ALERT | Δ ≥ +4pp vs stable baseline (still surface — what worked is worth knowing) |

**Card field discipline:**
- Every numeric value must come from a tool return, not your own arithmetic.
- The "D1 Retention", "vs Last 7 Days", and "vs <Weekday> average" rows must all use `d1_corrected`. Never mix metrics across these three rows. (See the playbook's Forcing rule.)
- If a field is genuinely unknown or not yet computable, write `data not available` — do not omit the row silently.
- Keep the card to exactly these 6 rows. Do not add rows. The whole point is consistency across runs.

**Card-specific output rules:**

- **Primary driver field.** One plain English sentence. No stage numbers, no column names. If cause is unknown, name the most likely suspect and state why it cannot be confirmed. Examples: "Likely push notification quality — data unavailable to confirm." / "Install mix shifted toward lower-retention paid channels." / "No clear cause — all measurable signals were stable."

- **Streak-leads rule.** When D1 has been consistently soft (or consistently strong) across multiple recent same-weekdays or consecutive days, the streak is the headline — not the single cohort day. Open the Primary driver field with the streak: "D1 has been running below the Monday average for N weeks" or "D1 has been soft for N consecutive days." Single-day detail follows as supporting context only. Use `flag_dip_days` or `compute_rolling_average` to confirm the pattern before citing it.

- **Thin-baseline rule.** When `compare_to_baseline` returns `baseline_meta.n_observations < 4` on the stable baseline, the day-of-week group has very few data points and the mean is unreliable. Append `— THIN BASELINE (n=<n_observations>)` to the "vs <Weekday> average" row and treat the severity verdict as indicative only — state this explicitly in the Diagnosis. Four or more observations is sufficient; below four, do not state the severity with confidence. (Note: the rolling7 baseline still carries `partial_window` in its metadata — that flag applies to the "vs Last 7 Days" row only and does not affect the severity badge, which is driven by the stable baseline.)

## Part 2 — Diagnosis (free-form)

Below the card, write the sections in order. All sections follow the playbook's output language rules — no column names, no stage numbers, no internal framework terms anywhere.

1. **Diagnosis** — flowing paragraph, 2–4 sentences. Cover: (a) what the number was and whether it was soft or strong, (b) whether the cause looks platform-specific or external, (c) the most likely explanation, (d) whether it can be confirmed. Do not pad with filler sentences. Do not restate the headline number verbatim.

2. **Evidence** — three subsections in order:

   **Acquisition** — bullet list. One bullet per source (total, organic, paid, WTA, others) checked against its 7-day average. (Per-source acquisition uses a 7-day trailing comparison deliberately — acquisition mix moves faster than D1 and a stable weekday baseline would smooth out the short spikes that are the actual signal here.) If any source is running significantly above normal, flag it as a possible suppressor of organic D1 — medium-to-low probability, stated as a suspicion not a conclusion. The more sources spiking, the stronger the suspicion. If all sources are at or below normal, one bullet stating acquisition mix is not the driver. Never reference misattribution mechanics. Do not speculate beyond what the numbers show.

   **D0 Experience** — bullet list. One bullet per signal: plain English name, value, delta vs last 7 days, one-word judgment (stable / improving / declining). Format: "[Signal name]: [value], [delta] vs last 7 days — [judgment]." If the dictionary flags a signal as not cohort-specific (all-DAU), add: "this measures all users, not just the new install cohort — treat as directional only." If a signal is unavailable, skip it entirely.

   **D1 Return Trigger** — flowing paragraph. If cohort-level push data (send rate, click-through rate) is unavailable, say so plainly. Check for a proxy signal (e.g. overall push-driven DAU). If a proxy exists, report it with its recent range and state explicitly what it does and does not confirm. If no data at all is available, state that return behaviour could not be assessed from available data.

3. **Context & Flags** — bullet list. Appears ONLY when at least one of these is true: a known holiday or event falls on or near the cohort day, a logged incident (infra, push, release) overlaps the window, or a notable historical pattern repeats. One bullet per flag, plain English, with the implication for today's number. If none apply, omit this section entirely.

4. **What to watch next** — flowing paragraph. Appears ONLY when it adds something the Diagnosis did not already say: a broader pattern emerging, an ambiguous signal that needs more time to resolve, or a meaningful directional call about where retention is heading. Before writing it, assess whether you have enough history — fetch more if needed, using your own judgment on how far back matters. Minimal numbers unless essential. Maximum 2–3 sentences. If nothing to add beyond Diagnosis, omit entirely.

For a D1 rise, also close with: **is this repeatable?** News-driven → no, will normalise. Mix improvement → maybe, if held. D0 activation improvement → yes, if a product change drove it (name it). Unknown → say so.
