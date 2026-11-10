"""Synthetic quality data generator. All output is SYNTHETIC and for demonstration only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def generate(start: str = "2024-01-01", months: int = 24, seed: int = 7) -> dict[str, pd.DataFrame]:
    """Return {'monthly': unit-month measures, 'incidents': incident log}."""
    rng = np.random.default_rng(seed)
    month_starts = pd.date_range(start, periods=months, freq="MS")
    monthly, incidents = [], []
    inc_id = 1
    for m_idx, m in enumerate(month_starts):
        # gentle improvement trend after a simulated quality initiative at month 12
        improve = 1.0 if m_idx < 12 else 0.85
        hh_lift = 0.0 if m_idx < 12 else 0.035
        for unit, prof in config.UNIT_PROFILE.items():
            pdays = int(rng.normal(prof["patient_days"], prof["patient_days"] * 0.06))
            cl_days = max(int(rng.normal(prof["cl_days"], prof["cl_days"] * 0.1)), 1)
            uc_days = max(int(rng.normal(prof["uc_days"], prof["uc_days"] * 0.1)), 1)
            falls = rng.poisson(prof["fall_rate"] * pdays / 1000 * improve)
            fall_harm = rng.binomial(falls, 0.22)
            med_err = rng.poisson(3.4 * pdays / 1000 * improve)
            hh_obs = int(rng.integers(60, 140))
            hh_ok = rng.binomial(hh_obs, min(prof["hh_base"] + hh_lift + rng.normal(0, 0.015), 0.99))
            clabsi = rng.poisson(1.1 * cl_days / 1000 * improve)
            cauti = rng.poisson(1.7 * uc_days / 1000 * improve)
            complaints = rng.poisson(pdays / 1000 * 1.8)
            monthly.append(dict(month=m, unit=unit, patient_days=pdays, central_line_days=cl_days,
                                urinary_catheter_days=uc_days, falls=falls, falls_with_harm=fall_harm,
                                medication_errors=med_err, hh_observations=hh_obs, hh_compliant=hh_ok,
                                clabsi=clabsi, cauti=cauti, complaints=complaints))
            # incident log: falls and med errors are part of the incident stream + others
            other = rng.poisson(pdays / 1000 * 9)
            cats = (["Fall"] * falls + ["Medication error"] * med_err +
                    list(rng.choice([c for c in config.INCIDENT_CATEGORIES if c not in ("Fall", "Medication error")],
                                    size=other)))
            for cat in cats:
                day = m + pd.Timedelta(days=int(rng.integers(0, m.days_in_month)))
                sev = rng.choice(config.SEVERITIES, p=config.SEVERITY_WEIGHTS)
                days_to_close = int(rng.gamma(2.2, 9 if m_idx < 12 else 7.5))
                closed = day + pd.Timedelta(days=days_to_close)
                needs_rca = sev in config.SEVERITIES[3:]
                incidents.append(dict(incident_id=f"SYN-QI-{inc_id:06d}", reported=day, unit=unit, category=cat,
                                      severity=sev, closed=closed, days_to_close=days_to_close,
                                      rca_required=needs_rca,
                                      rca_completed=bool(needs_rca and rng.random() < 0.82)))
                inc_id += 1
    return {"monthly": pd.DataFrame(monthly), "incidents": pd.DataFrame(incidents)}


def add_rates(monthly: pd.DataFrame) -> pd.DataFrame:
    """Add standard rate columns to a unit-month (or aggregated month) table."""
    df = monthly.copy()
    df["fall_rate"] = df["falls"] / df["patient_days"] * 1000
    df["fall_injury_rate"] = df["falls_with_harm"] / df["patient_days"] * 1000
    df["med_error_rate"] = df["medication_errors"] / df["patient_days"] * 1000
    df["hand_hygiene_pct"] = df["hh_compliant"] / df["hh_observations"] * 100
    df["clabsi_rate"] = df["clabsi"] / df["central_line_days"] * 1000
    df["cauti_rate"] = df["cauti"] / df["urinary_catheter_days"] * 1000
    return df


SUM_COLS = ["patient_days", "central_line_days", "urinary_catheter_days", "falls", "falls_with_harm",
            "medication_errors", "hh_observations", "hh_compliant", "clabsi", "cauti", "complaints"]


def aggregate_monthly(monthly: pd.DataFrame, units: list[str] | None = None) -> pd.DataFrame:
    df = monthly if units is None else monthly[monthly["unit"].isin(units)]
    return add_rates(df.groupby("month", as_index=False)[SUM_COLS].sum())
