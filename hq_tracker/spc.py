"""Statistical process control: p-chart, u-chart and run-chart rules (Western Electric / IHI style)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def p_chart(events: pd.Series, n: pd.Series) -> pd.DataFrame:
    """Proportion chart (e.g. hand hygiene compliance). Returns p, centre line and 3-sigma limits."""
    events, n = np.asarray(events, float), np.asarray(n, float)
    p = events / n
    pbar = events.sum() / n.sum()
    sigma = np.sqrt(pbar * (1 - pbar) / n)
    return pd.DataFrame({"value": p, "cl": pbar, "ucl": np.minimum(pbar + 3 * sigma, 1.0),
                         "lcl": np.maximum(pbar - 3 * sigma, 0.0)})


def u_chart(events: pd.Series, exposure: pd.Series, per: float = 1000.0) -> pd.DataFrame:
    """Rate chart for counts per exposure (e.g. falls per 1,000 patient days)."""
    events, exposure = np.asarray(events, float), np.asarray(exposure, float) / per
    u = events / exposure
    ubar = events.sum() / exposure.sum()
    sigma = np.sqrt(ubar / exposure)
    return pd.DataFrame({"value": u, "cl": ubar, "ucl": ubar + 3 * sigma, "lcl": np.maximum(ubar - 3 * sigma, 0.0)})


def special_cause_flags(chart: pd.DataFrame, run_length: int = 8, trend_length: int = 6) -> pd.Series:
    """Flag special-cause variation.

    Rule 1: point outside control limits.
    Rule 2 (shift): `run_length` or more consecutive points on one side of the centre line.
    Rule 3 (trend): `trend_length` or more consecutive points all increasing or all decreasing.
    Returns a Series of rule labels ('' when no signal).
    """
    v, cl = chart["value"].to_numpy(), chart["cl"].to_numpy()
    flags = np.array([""] * len(v), dtype=object)
    outside = (v > chart["ucl"].to_numpy()) | (v < chart["lcl"].to_numpy())
    flags[outside] = "Outside limits"

    side = np.sign(v - cl)
    start = 0
    for i in range(1, len(v) + 1):
        if i == len(v) or side[i] != side[start] or side[i] == 0:
            if side[start] != 0 and i - start >= run_length:
                for j in range(start, i):
                    flags[j] = flags[j] or "Shift"
            start = i
    diffs = np.sign(np.diff(v))
    start = 0
    for i in range(1, len(diffs) + 1):
        if i == len(diffs) or diffs[i] != diffs[start] or diffs[i] == 0:
            if diffs[start] != 0 and (i - start + 1) >= trend_length:
                for j in range(start, i + 1):
                    flags[j] = flags[j] or "Trend"
            start = i
    return pd.Series(flags, index=chart.index)
