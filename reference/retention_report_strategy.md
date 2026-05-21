# Retention Report Strategy — analysis and recommendation

A strategic discussion captured for the team about what the daily retention email at TOI should actually contain.

The doc has two parts:

1. **The in-depth, comprehensive view.** A clean-slate proposal for a CEO / Product Head grade retention report — what news-industry analytics actually emphasises, what CEOs want from this kind of email, and a seven-section structure that covers all of it.

2. **The crisp daily email + dashboard view.** A tighter recommendation that came out of the question "won't all of that be noisy?". Argues that a daily email should be ruthlessly short and that the comprehensive view belongs in a tiered set of artefacts — daily alert, weekly digest, monthly review, and an always-available dashboard.

Both views are kept here as alternatives so the team can compare. The recommendation at the bottom of the doc favours the tiered model in Part 2.

---

## Context

| | |
|---|---|
| **Audience** | CEO and Product Head at Times of India. Both are growth-focused; the CEO cares more about top-line growth and monetisation; the Product Head cares more about retention curves, channel mix, and activation funnel. |
| **What exists today** | A daily email at 11:05 IST that contains three retention blocks (D1, D7, D30), each with four sections (Engagement / Frequency / Grow Net Installs / Retention), each with per-metric coloured dots and a few sentences of impact prose. ~300 words. |
| **The strategic question** | Is this the right shape and depth for the audience? If not, what should it be? |

---

# Part 1 — In-depth, comprehensive view

What a maximally informative retention report would look like if we did not worry about length.

## 1.1 How the news industry actually treats retention

News apps have a retention profile unlike most other categories. The right report has to reflect this.

| Trait | Why it matters for retention |
|---|---|
| **Habit-loop driven** | The win condition is daily-multiple sessions. A news app that gets opened twice a day is healthy; once a week is dead. So the metric that matters most is not "did this cohort come back on day 1" — it is "has this cohort settled into a habit by week 4". |
| **News-cycle dependent** | Election week, cricket finals, major incidents drive install spikes followed by sharp decay. A 5pp D1 dip in the middle of a quiet news week is signal; the same dip the week after an election is noise. Without strategic context the same number means very different things. |
| **Push reach is existential** | Unlike social or commerce, news has almost no organic re-engagement trigger. Users do not naturally remember to check the news. Push notification reach is the leading indicator — opt-in rate, deliverability, click-through. If push is broken, retention dies. |
| **Acquisition channel mix dictates everything** | Organic users retain 2–3× better than paid in news. WTA (web-to-app, common in India) is the lowest-intent channel. The headline D1 number is meaningless without knowing the mix. |
| **Web and app share users** | Many news readers move between web and app. App-only retention is a partial story. The CEO is asking "is our audience growing" — that is a cross-platform question. |
| **Subscriber economics dominate at the top** | If there is a subscription product, retention of paid subscribers is more important to the CEO than retention of free users — typically by an order of magnitude. |

Standard analytics frameworks in this industry, more or less universal:

| Framework | Where it shows up |
|---|---|
| **Cohort retention curves** (D0 → D1 → D7 → D30 → D90) | The "retention shape" — flat or decaying — is the single best predictor of long-term health. |
| **DAU / MAU stickiness ratio** | News apps that hit 50%+ are healthy; below 20% is bleeding. |
| **Engaged minutes per user** | Used in monetisation (CPM × time = revenue) and a better engagement signal than session count. |
| **Channel retention curves separately** | Organic, paid, WTA each get their own retention curve — comparing them is the call PMs make on where to invest. |
| **Habit formation rate** | "What share of the D0 cohort became habitual (returned 4+ days in week 1)?" — better than D7 in isolation. |

## 1.2 What a CEO / Product Head actually wants to know each morning

Take a CEO opening the email at 8am. The questions they have, in priority order:

| # | Question | What answers it |
|---|---|---|
| 1 | "Are we growing?" | Week-on-week and month-on-month trend on MAU, DAU, new installs. |
| 2 | "Is anything on fire?" | Any cohort retention metric outside its normal band; any push or infrastructure anomaly. |
| 3 | "What's the story today?" | One-paragraph narrative tying the day's data to a real-world event or product change. |
| 4 | "Is the strategy working?" | Did the things we are investing in (personalisation, new feeds, paid campaigns) move the needle? |
| 5 | "What needs my attention this week?" | One to three specific things to ask the team about — not data, but decisions. |

A CEO does not consume metrics. A CEO consumes a story told with metrics as evidence.

## 1.3 What is structurally good about today's report

Crediting what works:

| What we built | Strategic value |
|---|---|
| Cohort-anchored retention read as `dN_corrected[cohort_day]` | Install-aligned, not return-aligned. Many news teams get this wrong; we got it right. |
| Push opt-in as the headline D0 signal | The industry-correct leading indicator. CEO-relevant. |
| Acquisition mix shift check on the cohort day | The right instinct (channel mix matters). The implementation is single-day; trend over weeks would be more actionable. |
| iOS comparator | Useful for separating product issues from external causes. CEO-grade context. |
| Severity thresholds | Useful for an analyst; less useful for a CEO. The CEO wants the story, not the badge. |

## 1.4 What is structurally missing

Six things that would belong in a CEO-grade retention report that are absent today:

| Gap | Why it matters at CEO / Product Head level |
|---|---|
| **TL;DR at the very top, three lines max** | The CEO scans the first three lines and decides whether to read on. "Net active users grew 2% week-on-week. D1 retention is back to typical Saturday levels after Wednesday's dip. One concern: paid install share is up 8 points over four weeks — diluting the cohort." |
| **Trend, not snapshot** | A single day's D1 against typical Saturday tells almost nothing strategic. "D1 has been drifting down 0.3pp/week for six weeks" is the actionable signal. Rolling trend lines, not single-cohort point estimates. |
| **MAU, WAU, growth deltas** | The CEO's primary metric is MAU. Today's email never mentions it. WoW, MoM, YoY growth on the active-user base — that is the headline. |
| **Channel retention separately** | Organic and paid retain very differently. Today we report one blended retention number per horizon. Splitting it shows whether a dip is a paid-volume problem or a true product problem. |
| **Habit formation / power user segment** | "What share of last week's installs became 4+ day weekly users?" — the leading indicator the CEO actually wants. D1 is a 24-hour lookback; the CEO wants a 30-day lookforward. |
| **Strategic context line** | Tie the day's numbers to real-world events (news cycle, product launches, paid campaigns). Without this, every retention dip looks like a product problem. Sometimes it is a slow news Friday. |

## 1.5 Clean-slate report shape — seven sections

If designed from scratch for a CEO / Product Head audience, the report would contain seven sections in this order:

| Section | Content | Why |
|---|---|---|
| **TL;DR (three lines max)** | Net active users today vs typical, headline retention vs typical, one concern or one win. | The five-second read. |
| **Growth dashboard** | MAU / WAU / DAU with WoW, MoM, YoY deltas; new installs (organic vs paid split) with the same deltas. | The headline metrics CEOs actually look at. |
| **Retention curves (D1 / D7 / D30) — trend, not snapshot** | Each of the three horizons shown as a six-week rolling trend, with today's cohort highlighted on that trend. | A snapshot is a moment; a curve tells whether things are improving or eroding. |
| **Channel health** | Organic retention vs paid retention curves separately. Push reach (overall and for the D1 cohort). Opt-in rate trend over four weeks. | Channels matter; one blended number hides everything. |
| **What moved today and why** | One paragraph diagnosis, plain English. Names the most likely cause and the confidence level. | The story the CEO consumes. |
| **Strategic context** | Bullet list of real-world events / product launches / campaigns relevant to the cohort window. | Without this, every dip looks like a product problem. |
| **What needs attention this week** | One to three specific things the team should investigate or decide. Not data — actions. | The CEO wants to know what to ask in their next product review. |

Notably **absent** in this clean-slate design:

- Per-metric color dots in the lite report style
- Severity badges in the subject line
- Six-row status cards
- D0 opt-in / login / uninstall as separate report items (they belong inside the "what moved today" diagnosis, not as standalone metrics)
- Cohort-day acquisition mix as a standalone section

These are analyst artefacts, not CEO artefacts.

## 1.6 Data we would want to cite

To support the clean-slate shape, additional data sources would help:

| Data | Why it matters | Where it might live |
|---|---|---|
| MAU / WAU history (~12 months) | The headline growth metric is unavailable today. Without it, we cannot tell the growth story. | Likely a separate sheet or a query against the source database. |
| Subscriber count + ARPU (if a subscription product exists) | Top-of-mind metric for any commercial CEO of a news organisation. | Billing / payments system or a finance dashboard. |
| Engaged minutes per user, page views per session | Industry-standard engagement depth; better than session count alone. | Mostly on the existing sheet — `pvs`, `avg_engagement_time_per_user`, `sessions` — used only directionally today. |
| D1–D7 retention split by channel (organic, paid, WTA, others) | Channel-specific retention curves; cannot be reconstructed from blended numbers. | Probably in the pivot sheets if we add a channel dimension. |
| Product release log + paid campaign calendar | The "strategic context" section needs this. | We have `data/docs/product_release_log.md` and `acquisition_campaigns.md`. The LLM does not currently load them as primary context, only on demand. |
| D90 retention | News industry truth: D90 separates "checks the app occasionally" from "habit". CEO-relevant. | Column appears to exist in the primary sheet (`d30_corrected`). D90 may need adding upstream. |
| Subscriber retention curves separately | If a subscriber product exists, this is more important than overall retention. | Separate data source. |
| Same-day-last-year comparison | Year-on-year context separates real trend from seasonal noise. | Same fact table, just a longer window. |

---

# Part 2 — Crisp daily email + dashboard view

What changed after the question "won't all of that be noisy?". A tighter recommendation.

## 2.1 The principle

An email is a **trigger**, not a **dashboard**. If the CEO needs more depth, they should click through to a dashboard — not read 800 words in their inbox at 8am.

A daily retention email that takes 5 minutes to read will be filtered to a folder within two weeks. A daily email that takes 15 seconds, every day, builds a habit.

So the right answer is: **crisp, ruthlessly. Almost certainly under 100 words.**

## 2.2 What "crisp" actually looks like

Concrete mockup of a daily CEO-grade email:

```
Subject: TOI Retention — May 18 cohort · D1 25.1% (typical)

D1 retention for Monday's cohort came in at 25.1%, in line with
the typical Monday (25.4%). Push opt-in held at 58%.

WAU is up 2% week-on-week and has been climbing steadily for
4 weeks — the organic acquisition push is paying off.

One concern: paid share of installs has crept up 6 points over
the last month and is starting to dilute cohort quality. Worth a
conversation with growth on whether the paid mix is bringing
habit-forming users or just install volume.

Full diagnostic dashboard: dashboard.example.com/retention
```

Roughly 60 words. Reads in 15 seconds. Tells a story. Names one thing to do. Points to a dashboard for everything else.

Compare to today's email, which renders ~300 words across three retention blocks, four sections each, twelve metrics with colour dots — for a CEO, that is a wall of data to wade through to find the story.

## 2.3 What CEOs actually consume — the executive-communications standard

Every successful executive newsletter is structured for scan, not study:

| Newsletter | Format | Why it works |
|---|---|---|
| Morning Brew / The Hustle | One headline plus three short bullets, around 60 words. | Trains the executive to expect short, get short. |
| McKinsey daily | One or two paragraphs of insight. | A single insight per email, not a data dump. |
| Bloomberg morning briefing | Bullet list of top market moves. | The executive scans, picks one to dig into. |
| Andreessen Horowitz portfolio updates | Headline number plus two sentences of context. | Trust signal: "if I write more, you will trust me less." |

None of them dump dashboards into the email body. All of them lead with a number and a story.

## 2.4 The right structural answer is a tiered cadence, not one email

This is where the comprehensive data from Part 1 lives — just not in the daily email.

| Artefact | Cadence | Length | Audience | Purpose |
|---|---|---|---|---|
| **Daily alert email** | Every day at 11:05 IST | < 100 words | CEO and Product Head | Trigger — "anything I need to know today?" |
| **Weekly digest email** | Monday morning | 300–500 words, includes trend tables | Product Head primarily, CEO on-demand | Trend story — "what changed across the week?" |
| **Monthly retention review** | First Monday of the month | One to two pages with charts | CEO, Product Head, Growth Head | Strategic — "are we on track? what to invest in next?" |
| **Live dashboard** | Always available | Drill-down | Anyone | Investigation — "I have a question, let me check." |

The daily email is the **trigger** that points at the dashboard when something interesting moves. The weekly digest is the **story** that ties trends together. The monthly is the **strategic** review with action items. Different audiences read different cadences.

What we built today is closer to a weekly digest collapsed into a daily email — that is why it reads as noisy. The diagnostic depth belongs in the weekly, not the daily.

## 2.5 An optional refinement — silent daily

Another defensible pattern for CEOs: the daily email goes out **only when something is off-baseline**. Quiet days produce no email. Loud days produce a short one. This further reduces inbox fatigue but loses the small habit-building effect of a regular daily touch.

Trade-off: a daily-with-content gets opened by habit; a silent-most-days email gets opened only when it arrives, which is when the news is bad — so the open rate is high and the cognitive load is low. Worth considering as an alternative to the always-on daily.

---

# Recommendation

**Move toward the tiered cadence in Part 2 over time.** The seven-section comprehensive view in Part 1 is correct in *content* but wrong in *container*. Trying to fit all of it into a single daily email creates noise the CEO will eventually filter out.

Specifically:

| Step | What |
|---|---|
| 1 | Define the crisp daily template — what fields, what max length, what tone. Around 60–80 words. Single severity in the subject. One paragraph of body. One concern or one win. One dashboard URL. |
| 2 | Build the weekly digest as a separate artefact. That is where the three retention blocks (D1, D7, D30) and the per-metric diagnostic depth belong. Goes out Monday morning. Around 300–500 words. |
| 3 | Build (or point to) a live retention dashboard. The daily email's footer carries the URL. The dashboard hosts the full picture — retention curves over time, channel mix, MAU/WAU/DAU, drill-down by segment. |
| 4 | Define the monthly retention review — slow cadence, deep content, strategic recommendations. One to two pages, possibly slides. First Monday of the month. |
| 5 | Decide whether the daily email is always-on (habit-building) or silent-when-quiet (low-noise). Both are defensible; my lean is always-on with a quiet-day template ("nothing material today; here is the WoW trend").  |

The data and analysis we have built so far are not wasted. They power the dashboard the daily email points to, and they generate the weekly digest. The CEO email itself just gets ruthlessly short.

---

# Open questions for the team before any change

1. **Cadence of the daily.** Always-on (habit-building, includes quiet days) or silent-when-quiet (only fires on off-baseline)?
2. **Audience clarity.** Is the daily for CEO only, Product Head only, or both? Different shapes serve each.
3. **Subscription product.** Does TOI have a subscriber tier? If yes, the report shape changes — subscriber retention and ARPU become headline metrics; free-tier retention drops a rung.
4. **Dashboard substrate.** Is there an existing analytics dashboard the daily email should link to, or does one need to be built? (Cloud-hosted Looker / Mixpanel / Amplitude / internal BI tool / Google Sheets — any of these can host the depth.)
5. **Data availability.** Which of the data sources listed in §1.6 can be made available? The answer determines how rich the dashboard and weekly digest can be.

This document is meant to be revised as those questions are answered.
