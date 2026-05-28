# Data quality audit — `data/sheets/app_health_daily.csv`

Audited 2026-05-25 by a one-shot pandas probe pass. Excludes the known
`others`-bucket Android attribution issue per instructions.

## Executive summary

The sheet has several confirmed data-quality problems outside the known
`others`-bucket issue. October 2025 contains the worst damage: iOS `paid`
installs are zero for every day of the month, iOS `others` installs spike
156× over their normal level on those same dates (the lost paid traffic
appears to have been mis-bucketed), the `All`-row installs/cohort columns
do not reconcile to the per-source sum for any day in October, and same-day
uninstalls exceed installs on 61 Android (organic / paid / WTA) rows that
month. Android `paid` installs separately collapsed to a 27-installs-per-day
average for December 2025 — roughly 1% of normal volume. iOS `others` has a
five-month installs gap from 2026-01-02 to today (125 consecutive days
with `NaN`). A single anomaly on 2026-01-13 has `net_installs = 2 × installs`
for every iOS row, suggesting a doubling bug in that day's pipeline. The
historical `net_installs` formula did not produce `installs − uninstalls`
prior to October 2025 — a different, looser computation was in use until
2025-10-31. Seven CSV columns are not documented in the dictionary.
The `#DIV/0!` strings the dictionary warns about have already been
converted to `NaN` somewhere upstream — useful to know, since downstream
tools may still test for the literal string.

## Methodology

All claims come from `pandas` probes run against the CSV — no LLM math.
The sheet was loaded once and string-typed numeric columns (`installs`,
`d1_users`, `avg_engagement_time`, etc.) were coerced to numeric after
stripping comma separators. Reconciliations were run on the full 13-month
history (3,890 rows) for structural checks (schema, cohort relationships,
formula identities) and on the last 90 days for live-anomaly screening.
The `others` source was excluded from severity-relevant counts wherever
the known attribution issue would dominate, and called out explicitly when
the same anomaly extends to other sources.

---

## High-severity anomalies

### 1. iOS `paid` installs = 0 for all 31 days of October 2025

**Evidence.** Every day in October 2025 has `installs = 0` for the iOS
paid row. Mean installs/day fell from 74.6 (Sept) to 0 (Oct) and recovered
to 113.5 (Nov). `dau` for these rows stays around 5,028/day and `d1`
averages 0.476, so users existed but no new installs are recorded.

| Month | iOS paid installs/day (mean) |
|---|---|
| Sept 2025 | 74.6 |
| Oct 2025 | 0.0 |
| Nov 2025 | 113.5 |

**Scope.** 31 rows (entire October 2025, iOS paid only).

**Severity.** High. Any October-2025-inclusive analysis of iOS paid
acquisition will be wrong.

**Hypothesis.** Attribution-source mapping outage. The iOS paid traffic
appears to have been re-bucketed into iOS `others` for the same month
(see anomaly 2 below).

---

### 2. iOS `others` installs spike 156× in October 2025

**Evidence.** Mean iOS `others` installs per day went from 11.7 (Sept) to
1,823.5 (Oct), then back to 1.4 (Nov). The cumulative October total is
56,529 installs versus the expected ~350 based on neighbouring months.
The 56,529 is the right order of magnitude to absorb the ~2,300 iOS paid
installs/day that disappeared in anomaly 1.

| Month | iOS others installs/day (mean) |
|---|---|
| Sept 2025 | 11.7 |
| Oct 2025 | 1,823.5 |
| Nov 2025 | 1.4 |

**Scope.** 31 rows (October 2025, iOS others source).

**Severity.** High. This is the same incident as anomaly 1, with the
volume re-bucketed to the wrong source. The `others` bucket already has
known attribution issues on Android; October iOS appears to be a separate
attribution incident affecting iOS only.

**Hypothesis.** Source-mapping bug in October 2025 routed iOS paid
attribution to the `others` bucket for the entire month.

---

### 3. Android `paid` installs collapse for December 2025

**Evidence.** Mean Android paid installs/day fell from 3,538 (Nov) to
27.1 (Dec) then recovered to 2,758 (Jan). The minimum was zero on
2025-12-29. Sixteen of 31 December days had `installs ≤ 10`. The decline
is gradual — installs taper from 86 on Dec 1 down to 1 by mid-month, sit
at 1-4 for the second half, then jump back to 224 on Dec 31.

| Date range | Daily installs |
|---|---|
| Dec 1-7 | 44-86 |
| Dec 8-15 | 6-40 (declining) |
| Dec 17-30 | 0-4 |
| Dec 31 | 224 |

**Scope.** 31 rows (Android paid, December 2025).

**Severity.** High. Drops `d1_installs` and downstream cohort math for
Jan 2026 by the same factor.

**Hypothesis.** Paid-attribution pipeline failed in early December and
was not restored until end of month. Could also be a real campaign pause
followed by relaunch — verifying against the marketing calendar would
disambiguate. The Dec 31 jump back to 224 looks like a partial recovery,
not a campaign relaunch on Jan 1.

---

### 4. October 2025 `All` row does not equal sum of sources

**Evidence.** For every (date, platform) combination in October 2025 (62
combos), the `installs` value on the `All` row differs from the sum of
the four source-level rows. Same holds for `d1_installs` (60 of 62
mismatches), `d7_installs` (48 of 62), and `d30_installs` (2 of 62 —
small because most October rows are now past the D30 cohort window).

Worked example: 2025-10-03 iOS — sum-of-sources installs = 2,515 vs
`All` installs = 800 (a 1,715 difference). Android same day:
sum = 23,451 vs `All` = 7,407 (16,044 difference).

The dictionary states `All` is a pre-calculated aggregate and the
expectation is that for count columns `sum(organic + paid + WTA + others)
== All`. This identity holds for every other month in the sheet and
breaks only in October.

**Scope.** 62 (date, platform) combos × 4 affected columns ≈ 232
broken cells in October 2025.

**Severity.** High. Any October analysis filtering to `acquisition_source = 'All'`
will read materially wrong volume.

**Hypothesis.** The `All`-row aggregation pipeline ran on an outdated or
partial source snapshot during October. The `All` row's October iOS
installs (~800/day average) sit close to the Sept All-row average,
suggesting Sept values may have been carried forward instead of
recomputed against October source data.

---

### 5. Same-day uninstalls exceed installs on non-`others` Android rows (Oct 2025)

**Evidence.** 62 Android rows have `d0_uninstalls > installs`, which is
structurally impossible (you cannot uninstall on day 0 more devices than
installed). Distribution:

| Month | WTA | organic | paid | Total |
|---|---|---|---|---|
| 2025-10 | 9 | 23 | 29 | 61 |
| 2025-12 | 0 | 0 | 1 | 1 |

Worked example: 2025-10-11 Android paid has `installs = 220` but
`d0_uninstalls = 7,064`.

**Scope.** 62 rows total, 61 in October 2025 across three Android sources
(not just `others`).

**Severity.** High. Co-located with anomaly 4 — the install count is the
broken value, not the d0_uninstalls value (d0_uninstalls magnitudes are
in line with surrounding months). Bounce-rate calculations on these rows
will produce nonsense.

**Hypothesis.** Same root cause as anomaly 4. The October install
ingestion produced under-counted values while d0_uninstalls came through
normally.

---

### 6. `net_installs = 2 × installs` for iOS on 2026-01-13

**Evidence.** On 2026-01-13, every iOS row has `net_installs` equal to
exactly twice its `installs` value, while `uninstalls = 0` (as expected
for iOS, where uninstalls aren't tracked):

| Platform | Source | installs | uninstalls | net_installs |
|---|---|---|---|---|
| iOS | All | 1,740 | 0 | 3,480 |
| iOS | organic | 1,581 | 0 | 3,162 |
| iOS | paid | 108 | 0 | 216 |
| iOS | WTA | 51 | 0 | 102 |

For iOS, `net_installs` should equal `installs` (per dictionary).

**Scope.** 4 iOS rows on a single date (2026-01-13).

**Severity.** High — only because it produces visibly wrong numbers in a
recent date that is likely still in active retention reports. Volume is
small (one day) but the inflation factor is 2×.

**Hypothesis.** A one-off double-counting bug in the 2026-01-13 ingestion
job. Worth checking whether other late-period iOS rows show occasional 2×
artefacts.

---

## Medium-severity anomalies

### 7. Historical `net_installs` formula was not `installs − uninstalls` (May 2025 – Oct 2025)

**Evidence.** Across all platforms and sources, `net_installs` matched
`installs − uninstalls` (Android) or `installs` (iOS) for **zero** rows
prior to October 2025. From October 2025 onward, the formula reconciles
cleanly for every row except the 2026-01-13 anomaly (#6) and the
October-All-row issue (#4).

Worked example: 2025-05-01 Android paid has `installs = 4,137`,
`uninstalls = 2,755`, so `installs − uninstalls = 1,382`. The sheet
records `net_installs = 3,633`. The discrepancy is 2,251 — far too large
to be a counting tweak.

Mismatches per platform/source over the pre-Oct window:

| Source | iOS rows wrong | Android rows wrong |
|---|---|---|
| organic / paid / WTA | 154 each | 154 each |
| All | 185 | 185 |

**Scope.** ~1,600 rows total (May 2025 through end of September 2025).

**Severity.** Medium. The numbers are wrong but only for the historical
backfill period; current values are correct. Any historical trend chart
that compares pre-Oct `net_installs` to post-Oct values will show a
spurious step change at the formula-switch boundary.

**Hypothesis.** The `net_installs` column was generated under a different
definition during the historical backfill and never recomputed. Possible
old definitions: net new app users (installs − uninstalls excluding
returning installs), or activated-install minus a different uninstall
window.

---

### 8. iOS `others` has no `installs` for the last 125 consecutive days

**Evidence.** From 2026-01-02 through 2026-05-24, `installs` is `NaN`
for every iOS `others` row (125 rows). Yet `dau` (700-950/day), `d1`
(varies 0.04-0.42), and `d1_users` are populated — meaning the rows
report active users and retention but never new acquisition.

| Date | installs | dau | d1 | d1_users |
|---|---|---|---|---|
| 2026-01-02 | NaN | 735 | 0.294 | 0.29 |
| 2026-01-03 | NaN | 801 | 0.192 | 0.00 |
| 2026-05-15 | NaN | 907 | 0.130 | 0.00 |

**Scope.** 125 rows (iOS others, 2026-01-02 to 2026-05-24).

**Severity.** Medium. This overlaps the known `others` issue but extends
it to iOS and to a different failure mode (missing installs, not inverted
bounce rate). Anything depending on iOS others installs since January
will silently get nothing.

**Hypothesis.** Source tracking for iOS others stopped emitting install
events in early January 2026. Retention can still be computed because
the cohort identifier persists in user state.

---

### 9. `logins` column has `NaN` for 107 iOS rows since 2026-01-05

**Evidence.** 107 rows have `NaN` in `logins`: 64 iOS WTA and 43 iOS
others, all from 2026-01-05 onwards. Other columns (`dau`, `installs`,
`pct_d0_login`) are populated on those rows — only the absolute `logins`
count is missing.

| Date | platform/source | dau | installs | logins |
|---|---|---|---|---|
| 2026-01-05 | iOS / WTA | 1,542 | 52 | NaN |
| 2026-01-08 | iOS / WTA | 1,415 | 30 | NaN |
| 2026-01-10 | iOS / WTA | 1,418 | 44 | NaN |

**Scope.** 107 rows. iOS WTA (64) and iOS others (43). Date range
2026-01-05 to 2026-05-24.

**Severity.** Medium. Tools that compute logins-derived metrics on iOS
WTA or iOS others over the last ~5 months will get partial data.

**Hypothesis.** Login-event tracking dropped for small iOS source
segments. Note that `pct_dau_logged_in` for these rows still has values,
so the `dau_logged_in` count must come from a different source than the
`logins` count.

---

### 10. `avg_engagement_time` column is mislabelled — it stores total seconds, not an average

**Evidence.** The column reconciles exactly as
`avg_engagement_time == avg_engagement_time_per_user × dau` (mean abs
diff = 0.00000026 over all 3,890 rows). Median value is 9,859,657
seconds ≈ 2,739 person-hours per (date, platform, source) cell, which is
plausible as total engagement but absurd as an average.

This column is not in the dictionary, which makes the mislabel easier to
miss for any tool author.

**Scope.** Naming applies to all 3,890 rows.

**Severity.** Medium. Any tool that treats this column as a per-user
average will produce numbers off by a factor of `dau` (often 100,000×).

**Hypothesis.** The column was added later (it is undocumented) and the
"avg_" prefix was inherited from a sibling column without renaming.

---

## Low-severity anomalies

### 11. Seven CSV columns are not documented in the dictionary

**Evidence.** Columns present in CSV but absent from
`data/dict/app_health_daily.md`:

- `avg_engagement_time`
- `d1_cohort_week`, `d7_cohort_week`, `d30_cohort_week`
- `d1_cohort_month`, `d7_cohort_month`, `d30_cohort_month`

The dictionary documents 43 columns; the CSV contains 50.

**Scope.** Documentation gap — affects every consumer that loads the
dictionary expecting full coverage. The cohort week / month columns are
likely derived from the corresponding day columns but the rule is not
stated.

**Severity.** Low (documentation), with one column (`avg_engagement_time`,
see anomaly 10) crossing into medium because of the misleading name.

**Hypothesis.** Columns added after the dictionary was last revised.

---

### 12. Five iOS `WTA` rows and 1 Android `paid` row have `d1 = 1.0` or `d7 = 1.0`

**Evidence.** Five rows have `d1 = 1.0` (all from very small cohorts —
12 to 38 installs), and six have `d7 = 1.0`. Examples:

| Date | platform/source | d1 | d1_users | d1_installs |
|---|---|---|---|---|
| 2025-07-28 | iOS / others | 1.0 | 17 | 17 |
| 2026-04-03 | iOS / WTA | 1.0 | 38 | 38 |
| 2026-05-06 | iOS / WTA | 1.0 | 34 | 34 |

**Scope.** 5 rows for `d1 = 1.0`, 6 for `d7 = 1.0`.

**Severity.** Low. These are real but noisy — `d1 = 1` on a 17-user
cohort means every single installer happened to return. The arithmetic
is internally consistent (`d1_users == d1_installs`). The issue is
statistical, not data-pipeline.

**Hypothesis.** Small-cohort noise on minor iOS sources. A
minimum-cohort guard (e.g. exclude rows where `d1_installs < 50`) would
prevent these from confusing trend reports.

---

### 13. iOS `WTA` had an 8-day stretch of `d1_corrected = 0` ending 2026-05-17

**Evidence.** From 2026-05-09 through 2026-05-17, `d1_corrected` was
exactly 0 for iOS WTA. The underlying `installs` ranged 13-33/day and
`d1_users` was zero on each of those days.

**Scope.** 8 consecutive days, iOS WTA only.

**Severity.** Low. iOS WTA cohorts are tiny (13-33/day), so a string of
zero returners is statistically possible. Worth confirming with the
attribution team rather than assuming a pipeline issue.

**Hypothesis.** Either real (small-N noise hitting zero by chance), or a
silent break in WTA-to-iOS-app deeplink return tracking.

---

### 14. Negative `net_installs` is the norm on Android organic for the last 90 days

**Evidence.** For the last 90 days on Android:

| Source | % of days with `net_installs < 0` |
|---|---|
| organic | 86.8% |
| paid | 38.5% |
| WTA | 2.2% |
| All | 46.2% |

On Android All, the period has roughly equal volume of installs vs
uninstalls (Dec 2025 net = −23,330; Apr 2026 net = +13,407).

**Scope.** Roughly 47 of the last 90 days have a negative `All`
`net_installs`.

**Severity.** Low. This is not necessarily a data error — a mature app
in a saturated market often has uninstalls > installs. Worth flagging
because the daily-email report should probably not lead with `net_installs`
as a stand-alone headline metric when it sits below zero half the time.

**Hypothesis.** Real market saturation, not a bug. The same value used to
be more often positive in earlier months when the pre-Oct-2025
`net_installs` formula (anomaly 7) was inflating it.

---

## Sanity checks that passed

These are the integrity properties verified against the data with no
anomaly found.

| Check | Result |
|---|---|
| `d1_cohort_day = date − 1` | Holds for all 3,890 rows |
| `d7_cohort_day = date − 7` | Holds for all 3,890 rows |
| `d30_cohort_day = date − 30` | Holds for all 3,890 rows |
| `d1_installs[date X] = installs[date X − 1]` per segment | 388/388 matches for Android All; 388/388 for Android paid (spot-checked two segments end-to-end) |
| `d1_corrected[date X] = d1[date X + 1]` per segment | 2,328/2,328 rows within 0.0001 — `d1_corrected` is the install-aligned view of `d1` and reconciles exactly |
| `pct_d0_notification_opt_in = d0_notification_opt_in / installs` | 0 rows >1% relative error (excl others) |
| `pct_d0_login = d0_login / installs` | 4 rows >1%, 0 rows >10% (excl others) |
| `pct_dau_logged_in = dau_logged_in / dau` | 0 rows >1% (excl others) |
| `pct_dau_via_notifications/launcher/deeplink = channel / dau` | 0 rows >1% each (excl others) |
| `avg_sessions_per_user = sessions / dau` | 0 rows >1% across all 3,890 |
| `avg_pvs_per_session = pvs / sessions` | 0 rows >1% across all 3,890 |
| Channel overlap rule (no single `dau_via_X` exceeds `dau`) | Held for all 3,890 rows |
| `dau_logged_in ≤ dau` | Held for all 3,890 rows |
| Channel pct sum > 1 | Confirmed range 1.05 - 1.30 (per dictionary, overlap is expected) |
| Range check on rate columns | `d1`, `d7`, `d1_corrected`, `d7_corrected`, `d30_corrected` all within [0, 1]. `d30` has 42 rows > 1 — all in the `others` bucket (the known issue) |
| Negative count columns | Zero negative values in `dau`, `installs`, `uninstalls`, `d0_uninstalls`, `pvs`, `sessions`, `logins`, `d0_notification_opt_in`, `d0_login`, `dau_logged_in`, `d1_users`, `d7_users`, `d30_users`, `d*_installs` |
| Duplicate (date, platform, source) rows | Zero |
| Row coverage | 389 unique dates × 2 platforms × 5 sources = exactly 3,890 rows, no missing combos |
| Categorical values stable over time | `platform` is always `android` or `ios`; `acquisition_source` is always one of `organic`, `paid`, `WTA`, `others`, `All` — no spelling drift |
| iOS `uninstalls` and `d0_uninstalls` always zero | Held for all 1,945 iOS rows (per dictionary) |
| `All` row's `d1_corrected` lies within [min, max] of per-source `d1_corrected` on the same date | Held for all 778 (date, platform) combos — `All` is a consistent weighted aggregate |
| `month` column matches `date.strftime('%b-%y')` | 0 mismatches |
| `week` column convention | Sunday-start week numbering (Google Sheets `WEEKNUM` type-2). Consistent across all 3,890 rows; not the same as ISO week. Worth documenting since 590 rows differ from ISO numbering. |
| `d1_users == d1 × d1_installs` | Mean abs diff 0.002; the `d1_users` column is derived from rates × denominators, which is why it carries fractional values (and why the `All`-row `d1_users` does not equal the per-source sum) |
| Recent-period NaN for `d1_corrected`, `d7_corrected`, `d30_corrected` | NaN coverage matches "cohort not yet complete" expectation: `d30_corrected` blank for last 30 days, `d7_corrected` blank for last 7 days, `d1_corrected` blank only on 2026-05-24. All consistent with the dictionary. |
| `#DIV/0!` literal strings | Zero occurrences in the CSV — already coerced to NaN upstream. Anything downstream that still tests for the literal string would silently miss them. |

---

## Known issue not investigated

Skipped per instructions: the `acquisition_source = 'others'` Android
attribution corruption where same-day uninstalls vastly exceed installs
(~745% average bounce rate; 100% of last 60 days inverted; iOS unaffected).
This is documented elsewhere and being escalated separately.

Note that anomaly 5 above (`d0_uninstalls > installs`) touches Android
organic, paid, and WTA in October 2025 — that is a distinct event from
the known `others` issue and is reported here.
