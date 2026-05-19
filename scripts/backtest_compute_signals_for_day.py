#!/usr/bin/env python3
"""Backtest harness for compute_signals_for_day.

Captures the tool's output across a fixed set of dates so a refactor
(parameterisation, key renames, generic cohort-day logic) can be verified
against the pre-refactor baseline.

Usage:
    uv run python scripts/backtest_signals.py --out tests/backtest/signals_before
    # ...refactor compute_signals_for_day...
    uv run python scripts/backtest_signals.py --out tests/backtest/signals_after
    uv run python scripts/diff_backtest.py tests/backtest/signals_before tests/backtest/signals_after
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 10 stratified dates — all 7 weekdays represented, spread across Jan to May
# 2026, includes the most recent fully-complete D1 cohort and a known alert
# day. We pass these to compute_signals_for_day exactly as the LLM does in
# the live reports, so the captured outputs match what the daily run sees.
BACKTEST_DATES: list[str] = [
    "2026-05-17",  # Sunday   — most recent fully-complete D1 cohort
    "2026-05-16",  # Saturday — the 🔴 ALERT cohort in this morning's email
    "2026-05-13",  # Wednesday — mid-week, recent, normal-looking
    "2026-05-04",  # Monday    — recent Monday
    "2026-04-28",  # Tuesday   — a month back, fully-mature
    "2026-04-10",  # Friday    — earlier April
    "2026-03-15",  # Sunday    — two months back, different weekday class
    "2026-02-26",  # Thursday  — late February
    "2026-01-31",  # Saturday  — near baseline_start_date, thin-territory
    "2026-01-04",  # Sunday    — earliest stable-baseline candidate
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        required=True,
        help="Directory to write the per-date JSON files into.",
    )
    parser.add_argument(
        "--platform",
        default="android",
        help="Platform segment (default: android).",
    )
    parser.add_argument(
        "--source",
        default="organic",
        help="Acquisition source (default: organic).",
    )
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    from tools.compute_signals_for_day import compute_signals_for_day

    try:
        rel_out = out_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        rel_out = out_dir

    print(f"compute_signals_for_day backtest")
    print(f"  segment: {args.platform} / {args.source}")
    print(f"  dates:   {len(BACKTEST_DATES)}")
    print(f"  output:  {rel_out}")
    print()

    fail_count = 0
    for date in BACKTEST_DATES:
        try:
            result = compute_signals_for_day(
                date=date,
                platform=args.platform,
                acquisition_source=args.source,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  {date}: ✗ exception {type(e).__name__}: {e}")
            fail_count += 1
            continue
        path = out_dir / f"{date}.json"
        path.write_text(
            json.dumps(result, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        ok = result.get("ok", False)
        n_err = len(result.get("signal_errors") or {})
        flag = "✓" if ok and n_err == 0 else "·"
        print(f"  {date}: {flag} ok={ok}  signal_errors={n_err}  →  {path.name}")

    print()
    if fail_count:
        print(f"{fail_count} date(s) failed.")
        return 1
    print(f"Wrote {len(BACKTEST_DATES)} files to {rel_out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
