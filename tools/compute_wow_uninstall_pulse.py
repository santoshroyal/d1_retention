"""Week-on-week uninstall pulse for the daily Uninstall Rate block.

Returns two comparison windows on the install / uninstall side:
  1. Trailing 7 days: [date-6, date] vs [date-13, date-7]
  2. Week-to-date Mon-through-current: this week's Monday through `date`
     vs the same days of the prior week

For each window the tool reports installs, uninstalls, same-day (D0)
uninstalls, net installs, the uninstall-to-install ratio (leak ratio),
and the same-day drop-off rate (d0_uninstalls / installs). It also
returns a severity classification (🔴 ALERT / 🟡 FLAG / 🟢 NORMAL)
computed deterministically from the combined movement of the drop-off
rate and the leak ratio across both windows.

Only Android has uninstall data — Apple's API does not expose iOS
uninstalls (every iOS row in the sheet has uninstalls = 0). Caller
should pass platform='android' for meaningful output.

This is the LITE-report tool. The DEEP report additionally calls
`compute_uninstall_deep_analysis` for composition / weekday / MoM cuts.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd

from tools._common import sheet, server, validate_segment


def _round_or_none(value: float | None, ndigits: int) -> float | None:
    """Round, but propagate None / NaN as None instead of crashing."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return round(float(value), ndigits)


def _classify_severity(
    t7_drop_pp: float | None,
    t7_ratio_delta: float | None,
    t7_cur_ratio: float | None,
    wtd_drop_pp: float | None,
    wtd_ratio_delta: float | None,
    wtd_cur_ratio: float | None,
) -> str:
    """Deterministic severity classification.

    🔴 ALERT — both windows are clearly worsening, OR ratio crossed above 1.0
       in either window AND drop-off rose ≥1.5pp in that window.
    🟡 FLAG  — one window is clearly worsening (drop-off ≥0.75pp or ratio ≥0.05),
       OR both windows are mildly worsening.
    🟢 NORMAL — both windows are stable or improved on both metrics.

    A window is "clearly worsening" if drop-off rose ≥0.75pp AND ratio rose
    ≥0.05, or if the ratio crossed above 1.0 with any positive drop-off move.
    """

    def severe(drop_pp, ratio_d, cur_ratio):
        if drop_pp is None or ratio_d is None:
            return False
        crossed_one = (cur_ratio is not None and cur_ratio > 1.0)
        return (drop_pp >= 1.5) or (crossed_one and drop_pp >= 1.0 and ratio_d >= 0.0)

    def clearly_worse(drop_pp, ratio_d, cur_ratio):
        if drop_pp is None or ratio_d is None:
            return False
        crossed_one = (cur_ratio is not None and cur_ratio > 1.0)
        return (drop_pp >= 0.75 and ratio_d >= 0.05) or (crossed_one and ratio_d > 0)

    def mildly_worse(drop_pp, ratio_d):
        if drop_pp is None or ratio_d is None:
            return False
        return drop_pp > 0 or ratio_d > 0

    t7_severe = severe(t7_drop_pp, t7_ratio_delta, t7_cur_ratio)
    wtd_severe = severe(wtd_drop_pp, wtd_ratio_delta, wtd_cur_ratio)
    t7_clear = clearly_worse(t7_drop_pp, t7_ratio_delta, t7_cur_ratio)
    wtd_clear = clearly_worse(wtd_drop_pp, wtd_ratio_delta, wtd_cur_ratio)
    t7_mild = mildly_worse(t7_drop_pp, t7_ratio_delta)
    wtd_mild = mildly_worse(wtd_drop_pp, wtd_ratio_delta)

    if t7_severe and wtd_severe:
        return "🔴 ALERT"
    if t7_severe or wtd_severe:
        # Severe on one side + at least mild deterioration on the other = ALERT
        if (t7_severe and wtd_mild) or (wtd_severe and t7_mild):
            return "🔴 ALERT"
        return "🟡 FLAG"
    if t7_clear and wtd_clear:
        return "🔴 ALERT"
    if t7_clear or wtd_clear:
        return "🟡 FLAG"
    if t7_mild and wtd_mild:
        return "🟡 FLAG"
    return "🟢 NORMAL"


@server.tool(
    description=(
        "Week-on-week uninstall pulse for the lite report's Uninstall Rate "
        "block. Returns two comparison windows: trailing 7 days "
        "([date-6, date] vs [date-13, date-7]) and week-to-date Mon-through-"
        "current (this week's Monday through `date` vs the same days of the "
        "prior week). Per window: installs, uninstalls, d0_uninstalls, "
        "net_installs, uninstall_to_install_ratio, same_day_drop_off_rate_pct, "
        "plus pp / percent deltas between current and prior. Also returns a "
        "deterministic severity classification ('🔴 ALERT' / '🟡 FLAG' / "
        "'🟢 NORMAL') computed from combined drop-off rate and leak ratio "
        "movement across both windows. Only Android has uninstall data — pass "
        "platform='android' for meaningful results. The deep report should "
        "additionally call compute_uninstall_deep_analysis for composition, "
        "weekday pattern, and MoM same-period comparison. Parameters: "
        "  date — OPTIONAL. YYYY-MM-DD anchor for the windows. If omitted or "
        "null, the tool uses the latest date with install/uninstall data in "
        "the sheet for this segment (which is one day ahead of the D1 cohort "
        "day, because install/uninstall is reported same-day and does not "
        "wait for return-day completion). Recommended: omit this parameter "
        "for the daily Uninstall Rate block so the freshest data is used. "
        "  platform — 'android' or 'ios' (default 'android'). "
        "  acquisition_source — 'organic' / 'paid' / 'WTA' / 'others' / 'All' "
        "(default 'organic'). "
        "Returns {ok, date, platform, acquisition_source, trailing_7d, "
        "week_to_date_mon_to_current, severity}."
    )
)
def compute_wow_uninstall_pulse(
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
        # Use the latest available date in the sheet for this segment.
        # Install/uninstall is reported same-day, so the freshest row IS
        # the right anchor for the WoW pulse (vs the D1 cohort day which
        # is a return-day-completion concept).
        end = seg["date"].max()
        date = end.date().isoformat()
    else:
        end = pd.to_datetime(date, errors="coerce")
        if pd.isna(end):
            return {"ok": False, "error": f"date not parseable: {date!r}"}

    for col in ("installs", "uninstalls", "d0_uninstalls", "net_installs"):
        if col in seg.columns:
            seg[col] = pd.to_numeric(seg[col], errors="coerce")

    def window_stats(start_d: pd.Timestamp, end_d: pd.Timestamp) -> dict[str, Any] | None:
        w = seg[(seg["date"] >= start_d) & (seg["date"] <= end_d)]
        if w.empty:
            return None
        installs = int(w["installs"].sum())
        uninstalls = int(w["uninstalls"].sum())
        d0_uninstalls = int(w["d0_uninstalls"].sum())
        net_installs = int(w["net_installs"].sum())
        return {
            "start": start_d.date().isoformat(),
            "end": end_d.date().isoformat(),
            "days": int((end_d - start_d).days) + 1,
            "installs": installs,
            "uninstalls": uninstalls,
            "d0_uninstalls": d0_uninstalls,
            "net_installs": net_installs,
            "uninstall_to_install_ratio": _round_or_none(
                uninstalls / installs, 3
            ) if installs else None,
            "same_day_drop_off_rate_pct": _round_or_none(
                d0_uninstalls / installs * 100, 2
            ) if installs else None,
        }

    def window_deltas(cur: dict | None, prior: dict | None) -> dict | None:
        if not cur or not prior:
            return None
        return {
            "installs_pct": _round_or_none(
                (cur["installs"] / prior["installs"] - 1) * 100, 1
            ) if prior["installs"] else None,
            "uninstalls_pct": _round_or_none(
                (cur["uninstalls"] / prior["uninstalls"] - 1) * 100, 1
            ) if prior["uninstalls"] else None,
            "d0_uninstalls_pct": _round_or_none(
                (cur["d0_uninstalls"] / prior["d0_uninstalls"] - 1) * 100, 1
            ) if prior["d0_uninstalls"] else None,
            "net_installs_abs": cur["net_installs"] - prior["net_installs"],
            "uninstall_to_install_ratio": _round_or_none(
                cur["uninstall_to_install_ratio"]
                - prior["uninstall_to_install_ratio"],
                3,
            ) if (
                cur.get("uninstall_to_install_ratio") is not None
                and prior.get("uninstall_to_install_ratio") is not None
            ) else None,
            "same_day_drop_off_pp": _round_or_none(
                cur["same_day_drop_off_rate_pct"]
                - prior["same_day_drop_off_rate_pct"],
                2,
            ) if (
                cur.get("same_day_drop_off_rate_pct") is not None
                and prior.get("same_day_drop_off_rate_pct") is not None
            ) else None,
        }

    # Trailing 7d
    t7_current = window_stats(end - timedelta(days=6), end)
    t7_prior = window_stats(end - timedelta(days=13), end - timedelta(days=7))
    t7_deltas = window_deltas(t7_current, t7_prior)

    # Week-to-date Mon-through-current
    week_start = end - timedelta(days=int(end.weekday()))  # Monday
    if end >= week_start:
        wtd_current = window_stats(week_start, end)
        wtd_prior = window_stats(
            week_start - timedelta(days=7), end - timedelta(days=7)
        )
    else:
        wtd_current = None
        wtd_prior = None
    wtd_deltas = window_deltas(wtd_current, wtd_prior) if wtd_current else None

    # Collision check: when the anchor is a Sunday, the WTD window
    # (Mon-Sun) is identical to the trailing-7d window. Showing both
    # tables would just repeat the same numbers. Suppress the WTD side
    # in that case — the trailing-7d table carries the weekly story.
    if (
        wtd_current
        and t7_current
        and wtd_current["start"] == t7_current["start"]
        and wtd_current["end"] == t7_current["end"]
    ):
        wtd_current = None
        wtd_prior = None
        wtd_deltas = None

    severity = _classify_severity(
        t7_deltas.get("same_day_drop_off_pp") if t7_deltas else None,
        t7_deltas.get("uninstall_to_install_ratio") if t7_deltas else None,
        t7_current.get("uninstall_to_install_ratio") if t7_current else None,
        wtd_deltas.get("same_day_drop_off_pp") if wtd_deltas else None,
        wtd_deltas.get("uninstall_to_install_ratio") if wtd_deltas else None,
        wtd_current.get("uninstall_to_install_ratio") if wtd_current else None,
    )

    return {
        "ok": True,
        "date": date,
        "platform": platform,
        "acquisition_source": acquisition_source,
        "trailing_7d": {
            "current": t7_current,
            "prior": t7_prior,
            "deltas": t7_deltas,
        },
        "week_to_date_mon_to_current": (
            {
                "current": wtd_current,
                "prior": wtd_prior,
                "deltas": wtd_deltas,
            }
            if wtd_current
            else None
        ),
        "severity": severity,
    }
