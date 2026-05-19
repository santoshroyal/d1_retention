#!/usr/bin/env python3
"""Backtest harness for tune._check_data_present.

Captures the helper's bool return for the same 10 dates Phase 1 used, so a
refactor (parameterising on retention_metric) can be verified.

Pre-refactor: function signature is _check_data_present(target_date, config).
Post-refactor: function signature is
    _check_data_present(target_date, retention_metric, config)
The harness inspects the signature and calls accordingly.

Usage:
    uv run python scripts/backtest_check_data_present.py --out tests/backtest/check_data_present_before
    # ...refactor _check_data_present...
    uv run python scripts/backtest_check_data_present.py --out tests/backtest/check_data_present_after
    uv run python scripts/diff_backtest.py tests/backtest/check_data_present_before tests/backtest/check_data_present_after
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Same 10 dates as compute_signals_for_day backtest, so the two captures can
# be cross-referenced if a date question ever comes up.
BACKTEST_DATES: list[str] = [
    "2026-05-17",
    "2026-05-16",
    "2026-05-13",
    "2026-05-04",
    "2026-04-28",
    "2026-04-10",
    "2026-03-15",
    "2026-02-26",
    "2026-01-31",
    "2026-01-04",
]


def _load_tune():
    """Import the tune module so we can call its private helpers."""
    from importlib.machinery import SourceFileLoader

    return SourceFileLoader("_tune_helper_probe", str(PROJECT_ROOT / "tune")).load_module()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        required=True,
        help="Directory to write the per-date JSON files into.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        rel_out = out_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        rel_out = out_dir

    tune_mod = _load_tune()
    fn = tune_mod._check_data_present
    sig = inspect.signature(fn)
    accepts_metric = "retention_metric" in sig.parameters

    # The function needs a config that defines schedule.target_segment.
    config = tune_mod._load_config()

    print(f"_check_data_present backtest")
    print(f"  function signature: {sig}")
    print(f"  accepts retention_metric: {accepts_metric}")
    print(f"  target_segment: {config['schedule']['target_segment']}")
    print(f"  output: {rel_out}")
    print()

    # Capture default-D1 result for every date. Both before- and after-refactor
    # forms should produce the same bool — pre-refactor reads d1_corrected
    # hardcoded; post-refactor reads it via the default retention_metric arg.
    # The JSON intentionally omits the call shape so the before/after files
    # are byte-comparable; the call shape is documented in the filename
    # suffix (__default vs __d7_corrected vs __d30_corrected).
    for date in BACKTEST_DATES:
        if accepts_metric:
            present = fn(date, "d1_corrected", config)
        else:
            present = fn(date, config)
        record = {
            "target_date": date,
            "metric_effectively_checked": "d1_corrected",
            "data_present": bool(present),
        }
        path = out_dir / f"{date}__default.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {date}  d1_corrected   present={present}  →  {path.name}")

    # Stretch capture (only post-refactor): same dates with d7_corrected and
    # d30_corrected. No regression baseline for these; just confirms the
    # parameter is wired through and produces sensible bools.
    if accepts_metric:
        print()
        for metric in ("d7_corrected", "d30_corrected"):
            for date in BACKTEST_DATES:
                present = fn(date, metric, config)
                record = {
                    "target_date": date,
                    "metric_effectively_checked": metric,
                    "data_present": bool(present),
                }
                path = out_dir / f"{date}__{metric}.json"
                path.write_text(
                    json.dumps(record, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"  {date}  {metric:14s} present={present}  →  {path.name}")

    print()
    print(f"Done. Output: {rel_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
