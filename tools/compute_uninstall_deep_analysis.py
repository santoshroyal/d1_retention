"""Deep uninstall analysis for the deep report's Uninstall Rate section.

Extends `compute_wow_uninstall_pulse` (which the deep report should also
call separately for the WoW pulse + severity) with three additional cuts:

  1. composition — total uninstalls split into same-day (D0) vs
     longer-tail (non-D0, i.e. installed before today) for 7d / 15d / 30d
     windows ending at `date`.

  2. weekday_pattern_last_30d — mean installs / uninstalls / d0_uninstalls /
     net_installs by weekday over the last 30 days; helps spot recurring
     weekday spikes or troughs (e.g. the Wednesday install burst pattern).

  3. mtd_mom_comparison — month-to-date totals (day 1 through day-of-month
     of `date`) for the current month vs the same period of the prior
     month; controls for where-in-the-month we are when comparing trends.

Only Android has uninstall data — pass platform='android' for meaningful
results.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd

from tools._common import sheet, server, validate_segment


def _round_or_none(value: float | None, ndigits: int) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return round(float(value), ndigits)


@server.tool(
    description=(
        "Deep uninstall analysis for the deep report's Uninstall Rate "
        "section. Returns three cuts beyond the WoW pulse (call "
        "compute_wow_uninstall_pulse separately for that): "
        "(1) composition — total uninstalls split into same-day (D0) vs "
        "longer-tail (non-D0) for 7d / 15d / 30d windows ending at `date`; "
        "(2) weekday_pattern_last_30d — mean installs / uninstalls / "
        "d0_uninstalls / net_installs per weekday over the last 30 days; "
        "(3) mtd_mom_comparison — month-to-date (day 1 through day-of-month "
        "of `date`) totals for current month vs same period of prior month, "
        "including leak ratio and same-day drop-off rate deltas. Use this "
        "for the deep report's diagnostic narrative on uninstall health. "
        "Only Android has uninstall data — pass platform='android'. "
        "Parameters: "
        "  date — OPTIONAL. YYYY-MM-DD anchor. If omitted or null, the tool "
        "uses the latest date with install/uninstall data for the segment "
        "(install/uninstall is reported same-day, so the freshest row IS "
        "the right anchor — NOT the D1 cohort day, which lags by 2 days). "
        "Recommended: omit this parameter to use the freshest available data. "
        "  platform — 'android' or 'ios' (default 'android'). "
        "  acquisition_source — 'organic' / 'paid' / 'WTA' / 'others' / "
        "'All' (default 'organic'). "
        "Returns {ok, date, platform, acquisition_source, composition, "
        "weekday_pattern_last_30d, mtd_mom_comparison}."
    )
)
def compute_uninstall_deep_analysis(
    date: str | None = None,
    platform: str = "android",
    acquisition_source: str = "organic",
) -> dict[str, Any]:
    err = validate_segment(platform, acquisition_source)
    if err:
        return {"ok": False, "error": err}

    df = sheet()
    seg = df[
        (df["platform"] == platform)
        & (df["acquisition_source"] == acquisition_source)
    ].copy()
    if seg.empty:
        return {
            "ok": False,
            "error": f"no rows for segment {platform}/{acquisition_source}",
        }

    if date is None or (isinstance(date, str) and date.strip() == ""):
        end = seg["date"].max()
        date = end.date().isoformat()
    else:
        end = pd.to_datetime(date, errors="coerce")
        if pd.isna(end):
            return {"ok": False, "error": f"date not parseable: {date!r}"}

    for col in ("installs", "uninstalls", "d0_uninstalls", "net_installs"):
        if col in seg.columns:
            seg[col] = pd.to_numeric(seg[col], errors="coerce")

    # ----- (1) composition: D0 vs non-D0 across 7d / 15d / 30d -----
    composition: dict[str, Any] = {}
    for days in (7, 15, 30):
        start = end - timedelta(days=days - 1)
        w = seg[(seg["date"] >= start) & (seg["date"] <= end)]
        if w.empty:
            continue
        total_un = int(w["uninstalls"].sum())
        d0 = int(w["d0_uninstalls"].sum())
        non_d0 = total_un - d0
        composition[f"last_{days}d"] = {
            "start": start.date().isoformat(),
            "end": end.date().isoformat(),
            "total_uninstalls": total_un,
            "d0_uninstalls": d0,
            "non_d0_uninstalls": non_d0,
            "d0_share_pct": _round_or_none(d0 / total_un * 100, 1)
            if total_un
            else None,
            "non_d0_share_pct": _round_or_none(non_d0 / total_un * 100, 1)
            if total_un
            else None,
        }

    # ----- (2) weekday pattern over last 30 days -----
    win30_start = end - timedelta(days=29)
    win30 = seg[(seg["date"] >= win30_start) & (seg["date"] <= end)].copy()
    win30["weekday"] = win30["date"].dt.day_name().str[:3]
    day_order = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    weekday_pattern: list[dict[str, Any]] = []
    for d in day_order:
        sub = win30[win30["weekday"] == d]
        if sub.empty:
            continue
        weekday_pattern.append(
            {
                "weekday": d,
                "n_days": int(len(sub)),
                "installs_avg": int(round(sub["installs"].mean(), 0)),
                "uninstalls_avg": int(round(sub["uninstalls"].mean(), 0)),
                "d0_uninstalls_avg": int(round(sub["d0_uninstalls"].mean(), 0)),
                "net_installs_avg": int(round(sub["net_installs"].mean(), 0)),
            }
        )

    # ----- (3) Month-to-date MoM same-period comparison -----
    day_of_month = int(end.day)
    cur_month_start = end.replace(day=1)
    prior_month_start = (cur_month_start - timedelta(days=1)).replace(day=1)
    # Prior-month end at the same day-of-month, capped if the prior month
    # is shorter (e.g. anchor day 31 with prior month February).
    prior_month_end_target = prior_month_start + timedelta(days=day_of_month - 1)
    # If we walked into the month after prior_month_start (e.g. Feb + 30 days
    # crosses into March), cap to the last day of the prior month.
    last_of_prior_month = cur_month_start - timedelta(days=1)
    if prior_month_end_target > last_of_prior_month:
        prior_month_end_target = last_of_prior_month

    cur_window = seg[(seg["date"] >= cur_month_start) & (seg["date"] <= end)]
    prior_window = seg[
        (seg["date"] >= prior_month_start)
        & (seg["date"] <= prior_month_end_target)
    ]

    def mtd_stats(w: pd.DataFrame) -> dict[str, Any] | None:
        if w.empty:
            return None
        installs = int(w["installs"].sum())
        uninstalls = int(w["uninstalls"].sum())
        d0 = int(w["d0_uninstalls"].sum())
        net = int(w["net_installs"].sum())
        return {
            "start": w["date"].min().date().isoformat(),
            "end": w["date"].max().date().isoformat(),
            "days": int(len(w)),
            "installs": installs,
            "uninstalls": uninstalls,
            "d0_uninstalls": d0,
            "net_installs": net,
            "uninstall_to_install_ratio": _round_or_none(
                uninstalls / installs, 3
            ) if installs else None,
            "same_day_drop_off_rate_pct": _round_or_none(
                d0 / installs * 100, 2
            ) if installs else None,
        }

    cur_stats = mtd_stats(cur_window)
    prior_stats = mtd_stats(prior_window)

    mtd_deltas: dict[str, Any] | None = None
    if cur_stats and prior_stats:
        mtd_deltas = {
            "installs_pct": _round_or_none(
                (cur_stats["installs"] / prior_stats["installs"] - 1) * 100, 1
            ) if prior_stats["installs"] else None,
            "uninstalls_pct": _round_or_none(
                (cur_stats["uninstalls"] / prior_stats["uninstalls"] - 1) * 100,
                1,
            ) if prior_stats["uninstalls"] else None,
            "net_installs_abs": cur_stats["net_installs"]
            - prior_stats["net_installs"],
            "uninstall_to_install_ratio": _round_or_none(
                cur_stats["uninstall_to_install_ratio"]
                - prior_stats["uninstall_to_install_ratio"],
                3,
            ) if (
                cur_stats.get("uninstall_to_install_ratio") is not None
                and prior_stats.get("uninstall_to_install_ratio") is not None
            ) else None,
            "same_day_drop_off_pp": _round_or_none(
                cur_stats["same_day_drop_off_rate_pct"]
                - prior_stats["same_day_drop_off_rate_pct"],
                2,
            ) if (
                cur_stats.get("same_day_drop_off_rate_pct") is not None
                and prior_stats.get("same_day_drop_off_rate_pct") is not None
            ) else None,
        }

    return {
        "ok": True,
        "date": date,
        "platform": platform,
        "acquisition_source": acquisition_source,
        "composition": composition,
        "weekday_pattern_last_30d": weekday_pattern,
        "mtd_mom_comparison": {
            "current_mtd": cur_stats,
            "prior_mtd_same_period": prior_stats,
            "deltas": mtd_deltas,
        },
    }
