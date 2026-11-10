"""Improvement scenario estimates for falls prevention and infection-prevention bundles.

These are planning estimates based on user-supplied assumptions (effect size, adoption,
cost per event). They are not outcome predictions.
"""
from __future__ import annotations

import pandas as pd


def annualise(agg: pd.DataFrame, months: int = 12) -> pd.Series:
    """Sum the most recent `months` rows of an aggregated monthly table and scale to 12 months."""
    tail = agg.sort_values("month").tail(months)
    return tail.sum(numeric_only=True) * (12 / max(len(tail), 1))


def falls_impact(falls_per_year: float, harm_falls_per_year: float, effect_pct: float, adoption_pct: float,
                 cost_per_harm_fall_sar: float, extra_los_days: float) -> dict:
    """Expected effect of a falls-prevention bundle.

    effect_pct   relative reduction in falls where the bundle is fully used
    adoption_pct share of eligible patients who actually receive the bundle
    """
    rr = (effect_pct / 100) * (adoption_pct / 100)
    avoided = falls_per_year * rr
    avoided_harm = harm_falls_per_year * rr
    return {"relative_reduction_pct": rr * 100, "falls_avoided": avoided, "harm_falls_avoided": avoided_harm,
            "bed_days_saved": avoided_harm * extra_los_days, "cost_avoided_sar": avoided_harm * cost_per_harm_fall_sar}


def hai_impact(clabsi_per_year: float, cauti_per_year: float, compliance_gain_pts: float,
               reduction_per_10pts_pct: float, cost_clabsi_sar: float, cost_cauti_sar: float) -> dict:
    """Expected effect of better bundle / hand-hygiene compliance on CLABSI and CAUTI.

    Assumes a linear relative reduction of `reduction_per_10pts_pct` for every 10 points of compliance gain,
    capped at 80 %.
    """
    rr = min(compliance_gain_pts / 10 * reduction_per_10pts_pct / 100, 0.8)
    a_cl, a_ca = clabsi_per_year * rr, cauti_per_year * rr
    return {"relative_reduction_pct": rr * 100, "clabsi_avoided": a_cl, "cauti_avoided": a_ca,
            "cost_avoided_sar": a_cl * cost_clabsi_sar + a_ca * cost_cauti_sar}
