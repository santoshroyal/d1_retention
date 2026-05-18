# CLAUDE.md

Orientation for any Claude session working in this project. Keep it accurate; update when conventions change.

## What this is

A PM tuning sandbox for D1 retention analysis at Times of India. A product manager edits one Markdown playbook (`d1-retention-analysis.md`) and runs `./tune`. The script sends the playbook to an LLM (Claude or Codex CLI) along with a curated set of MCP tools. The LLM analyses the question, calls deterministic-math tools (`compute_*`, `compare_to_baseline`, `flag_dip_days`, `get_rows`) to fetch numbers, and writes a report under `outputs/`.

The project's central design choice: the prompt itself contains **no inlined data**. Every retention number is fetched at run time through an MCP tool. This keeps the prompt small (~16k chars) and lets the LLM query any segment / window the PM asks about. Pre-baking data into the prompt was tried earlier and removed.

## Architecture in 30 seconds

```
PM edits d1-retention-analysis.md (playbook prose)
        │
        ▼
PM runs ./tune "optional question"
        │
        ▼
tune script  ── reads playbook
             ── computes full-sheet stats for the banner
             ── writes per-run MCP config
             ── launches Claude/Codex CLI subprocess
        │
        ▼
LLM reads system preamble (config.yaml) + playbook
LLM calls MCP tools as the playbook prose directs
        │
        ▼
tune_mcp.py  ── FastMCP server
             ── auto-imports every tools/*.py file
             ── each tool reads data/sheets/app_health_daily.csv (and 3 cohort pivots)
        │
        ▼
LLM writes Markdown report
        │
        ▼
tune script  ── streams output, renders inline
             ── writes outputs/<date>-d1-retention-analysis.md
             ── updates outputs/latest.md symlink
```

## File map and edit boundary

**What reaches the LLM at runtime:** only the playbook (`d1-retention-analysis.md`), the system preamble (`config.yaml`), and the data loaded through `tools/*.py` calls. Nothing else. `CLAUDE.md`, `README.md`, and the `reference/` folder are for humans only.

Files fall into four roles. Knowing the role of a file tells you what changing it affects.

### Runtime — read into the LLM's prompt during `./tune`

| Path | Owner | Purpose |
|---|---|---|
| `d1-retention-analysis.md` | **PM** | The playbook. Forcing rule, diagnostic flow, report shape, output language. Loaded into the prompt every run. Methodology rules specific to D1 analysis live here. |
| `config.yaml` | Engineer | System preamble, model selection, output template. Engineer-owned non-negotiable rules. |
| `data/sheets/app_health_daily.csv` | Data | Primary daily fact table. Checked into the repo so first clone works without network. The daily refresh pipeline keeps it current. |
| `data/sheets/app_d1_retention_health_*.csv` | Data | Three D1 cohort pivots (daily / weekly / monthly). Auto-fetched lazily; gitignored. |
| `data/dict/<sheet>.md` | Engineer-managed | Per-sheet column dictionaries. Primary sheet's dict is appended to the prompt every run; pivot dicts are bundled into `get_rows` responses. |
| `data/docs/*.md` | **PM-additive** | Methodology + event-context docs (release log, holidays, news events, known incidents). The LLM `load_file()`s them mid-reasoning. PM drops new docs in; engineer pre-populates. |
| `data/email_recipients.yaml` | **PM** | Recipients list for the daily scheduled email (`./tune schedule`). PM edits freely. SMTP plumbing lives in `config.yaml`; credentials in `.env`. |

### Code — runs the project, not read as prose

| Path | Owner | Purpose |
|---|---|---|
| `tune` | Engineer | Orchestration script. Runs the analysis end-to-end. ~1,100 lines. |
| `tune_mcp.py` | Engineer | FastMCP server. Auto-imports every `tools/*.py` file. Stays at root, not inside `tools/`. |
| `tools/<name>.py` | Engineer or PM | Each registered MCP tool. Filename = function name = lower_snake_case verb phrase. |
| `tools/_common.py` | Engineer | Helpers (`get_rows`, `aggregate`, `cohort_rate`, `delta_pp`, `filter_window`, `validate_segment`), constants (`VALID_PLATFORMS`, `VALID_SOURCES`, `MIX_SOURCES`), and the shared `server = FastMCP(...)` instance. |
| `tools/_TEMPLATE.py` | Template | Heavily annotated. PMs and engineers copy this to author new tools. Skipped by aggregator (leading underscore). |
| `scripts/generate_catalog.py` | Engineer | Build-time utility — regenerates `reference/primitives.md` from the live tool registry. Not run during `./tune`. |
| `pyproject.toml`, `uv.lock` | Engineer | Dependencies. Project uses `uv` for run + lock. |

### Reference — for humans only, never reaches the LLM at runtime

| Path | Owner | Purpose |
|---|---|---|
| `README.md` | Engineer | Project overview. Auto-rendered on the GitHub landing page. |
| `CLAUDE.md` | Engineer | This file. Orientation for any human or Claude session opening the repo. |
| `reference/PM_QUICKSTART.md` | Engineer | One-page setup guide for PMs receiving the project. |
| `reference/primitives.md` | Auto-generated | PM-facing catalog of MCP tools. One card per tool. Regenerated by `generate_catalog.py`. The LLM gets the same descriptions via the MCP protocol, not from this file. |
| `reference/request.md` | **PM** | Blank template the PM fills out to request a new MCP tool. |

### Output — generated by runs

| Path | Purpose |
|---|---|
| `outputs/<date>-d1-retention-analysis.md` | One dated report per run. |
| `outputs/latest.md` | Symlink to the most recent report. |

## Project-wide invariants

A handful of rules apply across every analysis, not just D1. These belong in `config.yaml` system_preamble or the playbook — they are the source of truth for runtime behaviour. CLAUDE.md does not duplicate methodology rules; the playbook and system preamble own them.

The only project-wide invariant worth restating here, because it is engineer-facing (not LLM-facing):

- **Do not assume a tool exists.** `reference/primitives.md` reflects only what is actually registered with the FastMCP server. The README's worked example uses `compute_install_to_dau_ratio` for illustration but the tool does not exist. Always verify a tool is registered before referencing it from the playbook — check `reference/primitives.md` or run `./tune --verify`.

## Common workflows

| Goal | Command |
|---|---|
| Validate playbook tool calls (sub-second, no LLM) | `./tune --verify` |
| Inspect the prompt that would go to the LLM | `./tune --dry-run "<query>"` |
| Real run | `./tune "<question>"` or `./tune` (uses playbook only) |
| Environment + dependency check | `./tune doctor` |
| Regenerate the tool catalog after adding/changing a tool | `uv run python scripts/generate_catalog.py` |
| Switch model for one run | `./tune --model sonnet "..."` (also: `opus`, `haiku`, `gpt-5.5` for Codex) |
| Test SMTP credentials without spending an LLM call | `./tune schedule --test-email <addr>` |
| One-shot scheduled run, testing list (`recipients:`) | `./tune schedule` — analyses the most recent COMPLETE D1 cohort (today − 2 IST, because yesterday's `d1_corrected` is not yet populated at 11:05 AM). `--dry-run` skips the email send. |
| One-shot scheduled run, full team (`extended_recipients:`) | `./tune schedule --prod` — same flow, sends to the extended list. This is what the daily cron entry should invoke. |
| Cron entry to install for daily 11:05 IST runs | `5 11 * * * cd "<project>" && ./tune schedule --prod >> "logs/schedule-$(date +\%Y-\%m).log" 2>&1` |

The `--verify` flag imports `tune_mcp.py` (which transitively imports every tool file) and parses the playbook for tool calls, validating each against the live registry. Use it as the cheap iteration loop before paying for an LLM run.

## Conventions for new tools

When adding a tool to `tools/`:

- Copy `tools/_TEMPLATE.py` to a new file with a `lower_snake_case` verb-phrase name (e.g. `tools/compute_funnel_share.py`). Function name matches filename stem.
- Import from `tools._common`: `server`, `validate_segment`, and whichever helpers (`get_rows`, `aggregate`, `cohort_rate`, `delta_pp`, `filter_window`) the math needs. **Do not write raw pandas in tool files.** If the helpers are insufficient, extend `_common.py` rather than reaching into pandas locally.
- Decorate with `@server.tool(description=...)`. The description is what the LLM reads to decide whether to call your tool *and* what `generate_catalog.py` turns into a card. Keep it under ~8 sentences; cover what it does, when to call it, every parameter, and the return shape.
- Validate inputs first: `err = validate_segment(platform, acquisition_source); if err: return {"ok": False, "error": err}`.
- Return shape: always include `"ok": True/False`, always echo the inputs (`date`, `platform`, `acquisition_source`), and on error include `"error"` (and optionally `"hint"`). Round numbers consistently: 2 decimals for percentages and pp deltas, 3 for ratios, 6 for fractions, 0 for integer counts.
- Save → `./tune --verify` → `uv run python scripts/generate_catalog.py` → reference the new tool from the playbook prose.

`tune_mcp.py` discovers files automatically:

```python
for path in sorted(TOOLS_DIR.glob("*.py")):
    name = path.stem
    if name.startswith("_") or name == "generate_catalog":
        continue
    importlib.import_module(f"tools.{name}")
```

Files starting with `_` (`_common.py`, `_TEMPLATE.py`) and `generate_catalog.py` are skipped. Everything else registers via decorator at import time.

### Tool-level conventions for surfacing weak data

These conventions emerged from real failure modes and are now project-wide. The LLM is told (in the playbook) to read these specific fields, so naming matters. Follow them when your tool's shape matches the pattern.

| Pattern | When to apply | Fields to add to the response | Live example |
|---|---|---|---|
| **Partial-window flag** | Your tool computes over a window of N units (days, weeks) but may have fewer than N units of data | `partial_window: bool`, `coverage_pct: float` | `tools/compute_rolling_average.py` (and `tools/compare_to_baseline.py` propagates as `baseline_meta.partial_window`) |
| **`signal_errors` dict** | Your tool returns several signals in one response and any signal can fail to compute | `signal_errors: {signal_name: reason_string}` (empty dict on the happy path; populated per failure) — never collapse "did not move" with "could not compute" into the same `None` | `tools/compute_signals_for_day.py` |
| **Dictionary bundling** | Your tool reads a non-primary registered sheet | `dictionary_path: "dict/<sheet>.md"`, `dictionary_md: <file content>` so the LLM gets column-level semantics in the same payload as the data | `tools/get_rows.py` (uses a per-process cache; primary sheet is excluded because its dictionary is in the prompt) |
| **Echo inputs in success returns** | Always | Echo `date`, `platform`, `acquisition_source`, and any other input that determined the result | Every `tools/compute_*.py` |
| **Stream-handler errors are surfaced, not swallowed** | If you add a new event-stream parser anywhere, increment `state["stream_parse_errors"]` on swallowed exceptions instead of `continue`-ing silently | `state["stream_parse_errors"]` propagated into the run summary | `tune` lines around 996 (Claude) and 1112 (Codex) |

Why these are conventions and not optional polish: each fixed a real failure mode where the LLM produced a confidently wrong report because it had no signal that the underlying computation was weak. The partial-window flag came from `n=5` baselines being silently treated as full-7. The `signal_errors` dict came from per-signal failures collapsing into "did not move." The dictionary bundling came from the `d0_uninstall_rate` substitution. Each pattern is the lesson from a specific incident.

## Sheet ingestion

The project reads from a Google Sheets workbook with multiple tabs. The primary daily fact table is `app_health_daily.csv`, checked into the repo so first clone works without network. Three D1 cohort pivots are downloaded lazily and cached locally:

| Tab name | What it is | Coverage |
|---|---|---|
| `app_health_daily` | Primary 50-col daily fact table | All platforms × all sources × dates from 2025-05-01 |
| `app_d1_retention_health_daily` | Daily D1 cohort pivot | **android × WTA only** |
| `app_d1_retention_health_weekly` | Weekly D1 cohort pivot | All platforms × all sources |
| `app_d1_retention_health_monthly` | Monthly D1 cohort pivot | **android × {WTA, paid} only** |

**Files involved.**

| Path | Role |
|---|---|
| `data/sheets/_registry.yaml` | Single declarative file: spreadsheet id, pub_key, refresh threshold (11:00 IST), and per-tab metadata (`gid`, `dictionary`, `description`, `aliases`, `pre_fetch`). Engineer-managed. |
| `data/sheets/_cache/<name>.meta` | Per-tab JSON sidecar holding `content_sha256`, `last_fetched_at`, `last_changed_at`, `schema_columns`. Auto-managed by the sheet store. Gitignored. |
| `data/sheets/_cache/<name>.lock` | Per-tab `fcntl.flock` so two parallel `./tune` runs cannot corrupt the cache. Gitignored. |
| `data/sheets/<name>.csv` | The tab's local copy. Only the primary is committed; auto-fetched ones are gitignored. |
| `tools/_sheet_store.py` | The only place network IO happens. Public API: `ensure_fresh`, `list_sheets`, `prefetch_due_sheets`, `force_refresh_all`, `is_due_for_refresh`. |
| `data/dict/<sheet_name>.md` | Per-sheet column dictionary. Hand-written; one file per registered sheet, filename matches the sheet name. |

**Daily-threshold refresh contract.** The first `./tune` run on or after 11:00 IST refreshes every `pre_fetch: true` tab whose `last_fetched_at` is older than today's threshold. Same-day later runs are silent. The trigger is in `tune` preflight (`_run_sheet_prefetch`), not in any MCP tool — the LLM never sees freshness as its concern.

**Why no conditional GET.** Tested: Google publish-to-web does not send `ETag` or `Last-Modified` and ignores `If-Modified-Since`. The hash compare on the response body is the only correctness mechanism for skipping unnecessary disk writes. Every refresh past the schedule window pays the full body download — a few hundred KB per pivot, 1.5 MB for the primary.

**Aliases.** A registry entry can declare aliases (e.g., `app_health_daily` has `["d1_retention"]`). The sheet store resolves any alias to the canonical name; old prose that says `load_file('sheets/d1_retention.csv')` keeps working as long as the alias entry stays.

**Adding a new sheet.** Append a stanza to `_registry.yaml` with the tab's `gid`, set `pre_fetch: true` if it should be in the daily refresh wave, write a `<sheet_name>.md` file in `data/dict/` (filename matches the sheet's canonical name). Next run auto-picks it up. No code change.

### Playbook vs dictionary — what goes where

For each registered sheet, knowledge about the sheet lives in two places:

- The **playbook** (`d1-retention-analysis.md`) carries the diagnostic flow. It references columns by name with one-line meanings so the flow reads as self-contained. Loaded into the prompt every run.
- The **dictionary** (`data/dict/<sheet>.md`) carries the full column reference, data gaps, channel caveats, and methodology rationale. **Always travels with the sheet's data** — see the loading rules below.

Boundary rule: the playbook teaches **what to do**; the dictionary teaches **what each column means**. When a methodology rule has both sides (the never-average-daily-rates pivot rule is the live example), the dictionary is the authoritative source and the playbook procedural version follows it.

When changing the column model: edit the dictionary first; cascade to the playbook only if the change affects the diagnostic flow. When the same fact appears in both files, that is duplication that should be cleaned up — the playbook gets a one-line summary plus a path reference, the dictionary keeps the full version.

**Dictionary loading rules (revised after the d0_uninstall_rate incident — see anti-patterns):**

| Rule | Where the dictionary lives at run time |
|---|---|
| **Primary sheet** | The dictionary content is appended to the user message at preflight (`_primary_dictionary()` in `tune`). The LLM has it from instant zero, every run. |
| **Pivot sheets** | The dictionary content is bundled into every `get_rows` response that reads that pivot (`_load_dictionary_for()` in `tools/get_rows.py`). The LLM sees rows and semantics in the same payload. |
| **Methodology / event-context docs in `data/docs/`** | Stay on-demand via `load_file`. Those genuinely vary by question (news, holidays, incidents, methodology). |

## Anti-patterns (decided against; do not reintroduce)

- **Pre-baked data slices in the prompt.** Tried; produced wasted tokens for non-Android queries and contradicted the "query-driven" architecture. Removed.
- **Raw pandas inside tool files.** `tools/_common.py` exposes the helpers PMs use. Reaching into pandas locally fragments the abstraction and makes PM-authored tools harder to write.
- **Hardcoding `platform="android"` in playbook tool examples.** Locks the LLM into the Android default even when the PM asks about iOS or paid. Use `<segment.platform>` placeholder syntax.
- **Moving `tune_mcp.py` into `tools/`.** Considered; rejected. `tune_mcp.py` is engineer-managed orchestration, sibling to `tune` and `config.yaml`. Putting it inside `tools/` confuses the import paths and crowds the PM-author folder.
- **Splitting engineer tools and PM tools into separate folders.** Considered; rejected for now (one folder is simpler and existing tools serve as reference patterns for PM authors). Revisit if PM authoring volume grows.
- **`AskUserQuestion` for confirmation when the user has been clear.** This user prefers direct execution after a prose-stated question. Use `AskUserQuestion` for genuine ambiguity, not for "is this OK?".
- **Adding tools speculatively.** New tools require a real diagnostic gap. Composing existing tools in playbook prose covers most needs.
- **LLM-driven sheet refresh.** Considered an MCP `refresh_sheet` tool the LLM could call. Rejected — freshness is a preflight concern handled by `tune` before the LLM is invoked. The LLM never thinks about staleness. The `--refresh` CLI flag covers manual override.
- **Conditional GET on the Google publish-to-web URLs.** Confirmed empirically: the server does not send `ETag` or `Last-Modified` and ignores `If-Modified-Since`. Do not add the request headers — they do nothing. The body-hash compare is the load-bearing mechanism.
- **Hand-maintained `--allowed-tools` whitelist.** v1.3 added two tools (`get_rows`, `list_sheets`) and the static whitelist in `tune` was not updated. Result: Claude got a permission error mid-run and the LLM had to write the report without the data those tools would have provided. The whitelist now derives from `server.list_tools()` at module load (`_allowed_mcp_tools()` in `tune`). Do not reintroduce a hand-maintained list; lists drift the moment a new tool lands. Same principle as the catalog generator and the MCP aggregator — single source of truth, not a manual mirror.
- **On-demand dictionary loading.** Tried first; produced a silent count-vs-rate substitution failure (`d0_uninstall_rate` → `d0_uninstalls`) that flipped a Stage-2 evidence line. Root cause: `get_rows` errors give column *names* via a hint, but not *semantics*. The LLM substituted the closest-named column from the hint and treated a count as if it were a rate. The dictionary is the only place column kinds (count vs rate vs derived) are spelled out; on-demand loading meant the LLM rarely had it. The current contract — primary dict in the prompt, pivot dicts bundled into `get_rows` — costs ~6 KB on every prompt and ~3 KB per pivot read, which is rounding error compared to the cost of a confidently wrong evidence line. Do not roll back to on-demand. Earlier versions of CLAUDE.md and the playbook had a "Column-name discovery is NOT a reason to load the dictionary" rule that was actively harmful — it told the LLM to use the tool's hint as the source of truth, which produced exactly this substitution. That rule is gone; do not reintroduce it.

## Style notes for any Claude working here

- Prose with selective tables. Tables for comparisons, file lists, parameter docs. Connective explanation in flowing complete sentences, not choppy bullets.
- Short responses. End-of-turn summary one or two sentences. State results, not process.
- The user is technically strong and prefers precise terminology. No hedging language ("maybe", "could potentially") when the answer is concrete.
- When the user says "go for the third" or "okay add it", they mean execute, not re-plan. Auto mode toggles often.

## Recent architectural state

These changes landed during the most recent design session:

- The inlined Android-organic slice (180 days × 28 cols) was removed from the prompt. User-message size dropped from ~109k chars to ~16k.
- `get_rows` was added so the LLM can fetch any segment / window on demand. 30-day default window, 400-row hard cap, 11-column standard projection, named-column override.
- The playbook gained the `d1_corrected` forcing rule, the no-duplicate-calls rule, the `get_rows` overlap rule, the comparator-platform symmetry, and a window-from-phrasing table.
- `_render_inlined_sheet` was renamed to `_compute_sheet_stats` (the slice work is gone; only banner stats remain).
- `config.yaml` lost its `inline_data:` block (40 lines of dead config).
- README gained: a "How to write a tool call in your prose" section naming the convention; a worked end-to-end example for authoring a new tool; clearer PM/engineer boundary headers across files.
