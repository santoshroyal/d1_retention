#!/usr/bin/env python3
"""Backtest harness for tune._target_cohort_date.

Captures what the helper returns and the offset from today's IST date, so a
refactor (parameterising on retention_metric) can be verified against the
pre-refactor baseline without depending on the wall-clock.

The captured value pairs the returned date with today's IST date and the
difference in days. The diff script compares (offset, returned_date) — both
must match between the before-set and the after-set when retention_metric
defaults to "d1_corrected".

Usage:
    uv run python scripts/backtest_target_cohort_date.py --out tests/backtest/target_cohort_date_before
    # ...refactor _target_cohort_date...
    uv run python scripts/backtest_target_cohort_date.py --out tests/backtest/target_cohort_date_after
    uv run python scripts/diff_backtest.py tests/backtest/target_cohort_date_before tests/backtest/target_cohort_date_after
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _load_function():
    """Import `_target_cohort_date` from the tune CLI script."""
    from importlib.machinery import SourceFileLoader

    mod = SourceFileLoader("_tune_helper_probe", str(PROJECT_ROOT / "tune")).load_module()
    return mod._target_cohort_date


def _capture(fn, *, retention_metric: str | None = None) -> dict:
    """Call the function in a way that works for both the old and new signatures.

    Old signature: `_target_cohort_date()` — no args.
    New signature: `_target_cohort_date(retention_metric="d1_corrected")`.

    We inspect the function's parameter list and pass `retention_metric` only
    when it is accepted. This way one harness drives both before and after.
    """
    sig = inspect.signature(fn)
    kwargs = {}
    if retention_metric is not None and "retention_metric" in sig.parameters:
        kwargs["retention_metric"] = retention_metric

    today_ist = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    result = fn(**kwargs)
    offset_days = (today_ist - result).days

    return {
        "called_with": kwargs,
        "today_ist": today_ist.isoformat(),
        "result": result.isoformat(),
        "offset_days_from_today_ist": offset_days,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        required=True,
        help="Directory to write the per-call JSON files into.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        rel_out = out_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        rel_out = out_dir

    fn = _load_function()
    accepts_param = "retention_metric" in inspect.signature(fn).parameters

    print(f"_target_cohort_date backtest")
    print(f"  function signature: {inspect.signature(fn)}")
    print(f"  accepts retention_metric: {accepts_param}")
    print(f"  output: {rel_out}")
    print()

    # Always capture the no-arg default call. This is the only call shape that
    # exists pre-refactor, and post-refactor it routes through the
    # retention_metric="d1_corrected" default. Both must produce the same value.
    cases: list[tuple[str, str | None]] = [("default", None)]
    if accepts_param:
        cases.extend([
            ("d1_corrected", "d1_corrected"),
            ("d7_corrected", "d7_corrected"),
            ("d30_corrected", "d30_corrected"),
        ])

    for label, retention_metric in cases:
        record = _capture(fn, retention_metric=retention_metric)
        path = out_dir / f"{label}.json"
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(
            f"  {label:14s}  offset={record['offset_days_from_today_ist']}d  "
            f"result={record['result']}  →  {path.name}"
        )

    print()
    print(f"Wrote {len(cases)} file(s) to {rel_out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
