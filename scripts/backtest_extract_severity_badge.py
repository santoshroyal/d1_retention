#!/usr/bin/env python3
"""Backtest harness for tune._extract_severity_badge.

The extractor is a pure string function. Feed it canned inputs and capture
what it returns. Two groups of cases:

  REGRESSION cases — must produce the same badge pre- and post-refactor.
  POST-ONLY cases   — only meaningful post-refactor (they exercise the new
                      primary_retention parameter or demonstrate the
                      intentional behavioural change).

The diff script compares files present in the before-set; files that exist
only in the after-set (post-only cases) are silently ignored.

Usage:
    uv run python scripts/backtest_extract_severity_badge.py --out tests/backtest/extract_severity_badge_before
    # ...refactor _extract_severity_badge...
    uv run python scripts/backtest_extract_severity_badge.py --out tests/backtest/extract_severity_badge_after
    uv run python scripts/diff_backtest.py tests/backtest/extract_severity_badge_before tests/backtest/extract_severity_badge_after
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Input that lives on disk (so the regression test reflects the current
# real report shape, not a synthetic).
_REAL_REPORT_PATH = PROJECT_ROOT / "outputs" / "latest.md"

# Each tuple is (case_label, raw_input). raw_input prefixed with "@@FILE@@"
# is resolved as a path read at run time.
REGRESSION_CASES: list[tuple[str, str]] = [
    (
        "01_real_latest_report",
        "@@FILE@@outputs/latest.md",
    ),
    (
        "02_legacy_single_marker",
        "<!-- severity: 🔴 ALERT -->\n"
        "# D1 fell sharply on Saturday May 16\n\n"
        "## Engagement\n",
    ),
    (
        "03_per_retention_marker_d1_only",
        "<!-- severity_d1: 🟢 NORMAL -->\n"
        "# D1 held at typical Monday level\n\n"
        "## Engagement\n",
    ),
    (
        "04_three_markers_in_order_d1_d7_d30",
        # Phase-4 future shape: three markers in the natural D1 → D7 → D30
        # order. Pre-refactor finds the first badge in line order = D1's.
        # Post-refactor finds the severity_d1 marker by key = D1's.
        # Same answer, but for different reasons.
        "<!-- severity_d1: 🟢 NORMAL -->\n"
        "<!-- severity_d7: 🔴 ALERT -->\n"
        "<!-- severity_d30: 🟡 FLAG -->\n"
        "# Combined retention report\n\n"
        "## D1 — May 17 cohort\n",
    ),
    (
        "05_empty_report",
        "",
    ),
    (
        "06_no_badge_anywhere",
        "Just some text with no severity badge at all.\n"
        "Multiple lines, but none of them contain a marker.\n",
    ),
]

# Each tuple is (case_label, raw_input, extra_kwargs). Captured only when
# the function supports the primary_retention parameter (post-refactor).
POST_ONLY_CASES: list[tuple[str, str, dict]] = [
    (
        # Same three markers as case 04 but in scrambled order. Pre-refactor
        # would return the first badge in line order (D7's = ALERT).
        # Post-refactor returns D1's badge regardless of where its marker
        # sits — that is the whole point of the per-retention parameter.
        "post_only_three_markers_d1_last",
        "<!-- severity_d7: 🔴 ALERT -->\n"
        "<!-- severity_d30: 🟡 FLAG -->\n"
        "<!-- severity_d1: 🟢 NORMAL -->\n"
        "# Combined retention report\n",
        {},  # primary_retention defaults to d1_corrected
    ),
    (
        # Stretch: same scrambled-order three-marker input, this time
        # asking for D7 as the primary. Should return D7's badge = ALERT.
        "post_only_stretch_d7_primary",
        "<!-- severity_d1: 🟢 NORMAL -->\n"
        "<!-- severity_d7: 🔴 ALERT -->\n"
        "<!-- severity_d30: 🟡 FLAG -->\n"
        "# Combined retention report\n",
        {"primary_retention": "d7_corrected"},
    ),
    (
        # Stretch: same input, D30 primary. Should return D30's badge = FLAG.
        "post_only_stretch_d30_primary",
        "<!-- severity_d1: 🟢 NORMAL -->\n"
        "<!-- severity_d7: 🔴 ALERT -->\n"
        "<!-- severity_d30: 🟡 FLAG -->\n"
        "# Combined retention report\n",
        {"primary_retention": "d30_corrected"},
    ),
]


def _resolve_input(spec: str) -> str:
    """Resolve a raw_input spec — either an inline literal or a @@FILE@@ path."""
    if spec.startswith("@@FILE@@"):
        rel = spec.removeprefix("@@FILE@@")
        path = PROJECT_ROOT / rel
        if not path.exists():
            return f"(file missing: {rel})"
        return path.read_text(encoding="utf-8")
    return spec


def _load_function():
    from importlib.machinery import SourceFileLoader

    mod = SourceFileLoader(
        "_tune_helper_probe", str(PROJECT_ROOT / "tune")
    ).load_module()
    return mod._extract_severity_badge


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        rel_out = out_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        rel_out = out_dir

    fn = _load_function()
    sig = inspect.signature(fn)
    accepts_primary = "primary_retention" in sig.parameters

    print(f"_extract_severity_badge backtest")
    print(f"  function signature: {sig}")
    print(f"  accepts primary_retention: {accepts_primary}")
    print(f"  output: {rel_out}")
    print()

    print("Regression cases (compared by diff script):")
    for label, raw_input in REGRESSION_CASES:
        text = _resolve_input(raw_input)
        returned = fn(text)
        record = {
            "case": label,
            "input_length_chars": len(text),
            "returned_badge": returned,
        }
        path = out_dir / f"{label}.json"
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  {label:42s} → {returned!r}")

    if accepts_primary:
        print()
        print("Post-only cases (not compared; documented behavioural / stretch tests):")
        for label, raw_input, kwargs in POST_ONLY_CASES:
            text = _resolve_input(raw_input)
            returned = fn(text, **kwargs)
            record = {
                "case": label,
                "input_length_chars": len(text),
                "kwargs": kwargs,
                "returned_badge": returned,
            }
            path = out_dir / f"{label}.json"
            path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            kwargs_str = f"  (kwargs={kwargs})" if kwargs else ""
            print(f"  {label:42s} → {returned!r}{kwargs_str}")

    print()
    print(f"Done. Output: {rel_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
