#!/usr/bin/env python3
"""Diff two backtest output directories.

Used after a refactor to confirm that the new code's output is numerically
identical to the pre-refactor baseline, modulo controlled changes
(renamed keys, brand-new fields).

Usage:
    uv run python scripts/diff_backtest.py BEFORE_DIR AFTER_DIR

Exit code:
    0 = zero diffs (refactor is clean)
    1 = real diffs found (refactor changed values)
    2 = setup problem (missing dir, no files)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Key renames applied to the after-set before comparison. Populate this map
# when a refactor deliberately renames a field — left side is the path tuple
# AS IT APPEARS IN THE AFTER FILE; right side is the path it should map to
# in the before file. Both paths are tuples of strings (use repeated keys
# for nested locations, e.g. ("signals", "platform_d1_delta_pp")).
KEY_RENAMES: dict[tuple[str, ...], tuple[str, ...]] = {
    # compute_signals_for_day Phase-1 refactor: generic key names that no
    # longer carry the retention horizon in the key itself.
    ("signals", "platform_delta_pp"):       ("signals", "platform_d1_delta_pp"),
    ("signals", "ios_delta_pp"):            ("signals", "ios_d1_delta_pp"),
    ("signal_errors", "platform_delta_pp"): ("signal_errors", "platform_d1_delta_pp"),
    ("signal_errors", "ios_delta_pp"):      ("signal_errors", "ios_d1_delta_pp"),
}

# Top-level keys the refactored tool is allowed to add without it counting
# as a regression. Anything else that appears in the after-set but not the
# before-set will be flagged.
NEW_KEYS_ALLOWED_IN_AFTER: set[str] = {
    # Phase-1: tool now echoes which retention_metric was requested.
    "retention_metric",
}

# Path prefixes whose values are descriptive prose, not numerical results.
# Diffs inside these paths are not flagged. Useful for `notes` arrays where
# the refactor reworded the docstrings without changing any computed value.
SKIP_PATH_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("notes",),
)

# Tolerance for float comparison (rounding-order changes that are
# numerically benign).
FLOAT_EPS = 1e-9


def flatten(obj, prefix: tuple[str, ...] = ()):
    """Yield (path_tuple, value) pairs for every leaf in a JSON object."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flatten(v, prefix + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flatten(v, prefix + (f"[{i}]",))
    else:
        yield prefix, obj


def apply_renames(flat: dict[tuple[str, ...], object]) -> dict[tuple[str, ...], object]:
    """Rewrite renamed-key paths on the after-set side before comparison."""
    if not KEY_RENAMES:
        return flat
    out: dict[tuple[str, ...], object] = {}
    for path, value in flat.items():
        # Direct hit on the renamed key.
        if path in KEY_RENAMES:
            out[KEY_RENAMES[path]] = value
            continue
        # The renamed key sits as a prefix of this path (renaming a parent
        # dict). Apply the prefix rename and keep the rest.
        rewritten = path
        for old, new in KEY_RENAMES.items():
            if len(path) > len(old) and path[: len(old)] == old:
                rewritten = new + path[len(old) :]
                break
        out[rewritten] = value
    return out


def diff_one(before_path: Path, after_path: Path) -> list[tuple[str, object, object]]:
    """Return a list of (dotted_path, before_value, after_value) diffs."""
    before = dict(flatten(json.loads(before_path.read_text(encoding="utf-8"))))
    after = dict(flatten(json.loads(after_path.read_text(encoding="utf-8"))))
    after = apply_renames(after)

    diffs: list[tuple[str, object, object]] = []
    for key in sorted(set(before) | set(after), key=lambda t: ".".join(t)):
        b_val = before.get(key, _MISSING)
        a_val = after.get(key, _MISSING)
        if b_val is _MISSING and a_val is _MISSING:
            continue
        # Brand-new top-level key in the after set is allowed.
        if (
            b_val is _MISSING
            and len(key) >= 1
            and key[0] in NEW_KEYS_ALLOWED_IN_AFTER
        ):
            continue
        # Skip prose-only paths (notes / descriptions).
        if any(key[: len(p)] == p for p in SKIP_PATH_PREFIXES):
            continue
        if b_val == a_val:
            continue
        # Tolerate tiny float drift.
        if (
            isinstance(b_val, float)
            and isinstance(a_val, float)
            and abs(b_val - a_val) < FLOAT_EPS
        ):
            continue
        diffs.append((".".join(key), b_val, a_val))
    return diffs


_MISSING = object()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", help="Baseline directory (pre-refactor output)")
    parser.add_argument("after", help="New directory (post-refactor output)")
    args = parser.parse_args()

    before_dir = Path(args.before)
    after_dir = Path(args.after)

    if not before_dir.is_dir():
        print(f"before directory not found: {before_dir}", file=sys.stderr)
        return 2
    if not after_dir.is_dir():
        print(f"after directory not found: {after_dir}", file=sys.stderr)
        return 2

    files = sorted(p.name for p in before_dir.glob("*.json"))
    if not files:
        print(f"no JSON files in {before_dir}", file=sys.stderr)
        return 2

    total_diffs = 0
    total_files_with_diffs = 0
    for fname in files:
        b = before_dir / fname
        a = after_dir / fname
        if not a.exists():
            print(f"  {fname}: ✗ MISSING in after/")
            total_files_with_diffs += 1
            total_diffs += 1
            continue
        diffs = diff_one(b, a)
        if not diffs:
            print(f"  {fname}: ✓ identical")
            continue
        total_files_with_diffs += 1
        total_diffs += len(diffs)
        print(f"  {fname}: ✗ {len(diffs)} diff(s)")
        for path, b_val, a_val in diffs:
            print(f"    {path}")
            print(f"      before: {b_val!r}")
            print(f"      after:  {a_val!r}")

    print()
    print(f"Compared {len(files)} file pair(s).")
    if total_diffs == 0:
        print("Zero numerical drift. Refactor is clean.")
        return 0
    print(f"{total_diffs} diff(s) across {total_files_with_diffs} file(s).")
    print("Refactor changed values — investigate before proceeding.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
