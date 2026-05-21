# PM Quickstart

One page. Get the sandbox running in five minutes.

## What you need

- macOS or Linux terminal
- Python 3.11 or newer (check: `python3 --version`)
- `uv` package manager (check: `uv --version`; install if missing: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Claude Code CLI, signed in (check: `claude --version`)

## One-time setup

```bash
git clone https://github.com/santoshroyal/d1_retention.git
cd d1_retention
uv sync
./tune doctor
```

`./tune doctor` should print all green checks. If anything is red, the message tells you what to fix.

## Your first run

```bash
./tune
```

This reads `d1-retention-analysis.md` (the playbook) and writes a report to `outputs/`. The latest report is always at `outputs/latest.md`.

You can also pass a question:

```bash
./tune "why did Android organic D1 dip last week?"
```

## Tuning the analysis

The tuning loop is mostly one file: `d1-retention-analysis.md`. Open it in any editor, change the prose — hypothesis, diagnostic steps, output language — and re-run `./tune`. That is the workflow for changing methodology.

Optional context lives in `data/docs/` (release notes, holidays, news events, methodology). The LLM loads what it needs on its own; you do not have to reference them.

## Picking the report shape

There are two report variants. Choose with `--report`:

| Command | What you get |
|---|---|
| `./tune` or `./tune --report deep` | Default. A 6-row status card on top (cohort, D1 number, deltas, severity, primary driver, iOS comparison) followed by a free-form diagnostic narrative (Diagnosis / Evidence / Context / What to watch next). For when you want full reasoning. |
| `./tune --report lite` | Three short retention blocks per email — D1, D7, and D30 — each a tight causality narrative (What happened, Why it matters, Driver). The D1 block goes deeper (D0 signals, acquisition mix, "What we can't see", "Watch next"); D7 and D30 stop at the Driver line. Every block ends with a fixed list of "fields that would sharpen this read." For daily reading and email digests. |
| `./tune --report both` | The lite dashboard first, then the deep card and diagnosis below. For when you want both quick-scan and full reasoning in one report. |

The shape of each variant is defined in `reports/`:

- `reports/deep.md` — the deep variant template (engineer-managed; do not edit casually).
- `reports/lite.md` — the lite variant template (engineer-managed; do not edit casually). The lite shape is fixed in the template — there is no PM-tunable layout file.

## Where things go

| What | Where |
|---|---|
| The playbook you tune | `d1-retention-analysis.md` |
| Each run's report | `outputs/<date>-d1-retention-analysis.md` |
| Latest report (symlink) | `outputs/latest.md` |
| Context docs the LLM may load | `data/docs/` |

## Daily email — where to update the recipients

The project can send a daily D1 retention report by email at 11:05 AM IST. The recipients list lives in one file:

```
data/email_recipients.yaml
```

There are TWO lists in that file:

| List | Used by | Edit when... |
|---|---|---|
| `recipients:` | `./tune schedule` (testing) — used for repeated dev runs | You want a smaller list during testing |
| `extended_recipients:` | `./tune schedule --prod` (the daily cron run) — used for production | You want to add or remove someone from the daily team email |

Open the file, add or remove email addresses under whichever list, save. The next scheduled run picks up the change — no restart, no engineer involvement. SMTP credentials and timing are engineer-managed (in `config.yaml` and a local `.env` file you do not see).

If the daily email is not arriving:

| Check | What to do |
|---|---|
| Is the scheduled run set up at all? | Ask the engineer to confirm the cron entry exists: `crontab -l | grep "tune schedule"` |
| Is the `extended_recipients:` list non-empty? | Open `data/email_recipients.yaml`; the prod list must have at least one address |
| Did the analysed cohort's data arrive in the sheet? | The daily run targets the install cohort from 2 days ago (whose D1 completed measuring overnight). If still not in the sheet, the script retries up to 5 times. After 5 failures it sends a "data unavailable" email. Check your inbox for that notice. |

## When something does not work

| Symptom | Try this |
|---|---|
| `claude` not signed in | Run `claude` once and complete sign-in. |
| Sheet refresh failed (network) | Re-run `./tune`, or force a refetch with `./tune --refresh`. |
| Anything else | `./tune doctor` — the output names the broken thing. |

For deeper architecture and conventions, see `README.md`. You do not need to read it to use the sandbox.
