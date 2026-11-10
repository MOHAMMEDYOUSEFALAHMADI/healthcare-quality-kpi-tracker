"""Monthly quality report export (Excel workbook and Markdown summary)."""
from __future__ import annotations

import io

import pandas as pd

from . import config

KPI_LABELS = {
    "fall_rate": ("Falls / 1,000 patient days", False),
    "fall_injury_rate": ("Falls with harm / 1,000 patient days", False),
    "med_error_rate": ("Medication errors / 1,000 patient days", False),
    "hand_hygiene_pct": ("Hand hygiene compliance %", True),
    "clabsi_rate": ("CLABSI / 1,000 central-line days", False),
    "cauti_rate": ("CAUTI / 1,000 catheter days", False),
}


def scorecard(month_row: pd.Series, prev_row: pd.Series | None = None) -> pd.DataFrame:
    rows = []
    for key, (label, higher_better) in KPI_LABELS.items():
        val, tgt = float(month_row[key]), config.TARGETS[key]
        met = val >= tgt if higher_better else val <= tgt
        prev = float(prev_row[key]) if prev_row is not None else None
        rows.append({"KPI": label, "Value": round(val, 2), "Target": tgt,
                     "Status": "Met" if met else "Not met",
                     "Change vs previous": None if prev is None else round(val - prev, 2)})
    return pd.DataFrame(rows)


def to_excel(scorecard_df: pd.DataFrame, unit_table: pd.DataFrame, incidents: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        scorecard_df.to_excel(xw, sheet_name="Scorecard", index=False)
        unit_table.to_excel(xw, sheet_name="By unit", index=False)
        incidents.to_excel(xw, sheet_name="Incidents", index=False)
        pd.DataFrame({"Note": ["All data in this workbook is SYNTHETIC and for demonstration only."]}) \
            .to_excel(xw, sheet_name="About", index=False)
    return buf.getvalue()


def to_markdown(month_label: str, scorecard_df: pd.DataFrame, incidents: pd.DataFrame) -> str:
    met = (scorecard_df["Status"] == "Met").sum()
    sev = incidents["severity"].value_counts().reindex(config.SEVERITIES, fill_value=0)
    lines = [f"# Monthly Quality & Patient Safety Report – {month_label}", "",
             "_Synthetic demonstration data._", "",
             f"**KPIs meeting target:** {met} of {len(scorecard_df)}", "",
             "| KPI | Value | Target | Status |", "|---|---|---|---|"]
    lines += [f"| {r.KPI} | {r.Value} | {r.Target} | {r.Status} |" for r in scorecard_df.itertuples()]
    lines += ["", f"**Incidents reported:** {len(incidents)}", ""]
    lines += [f"- {k}: {v}" for k, v in sev.items()]
    return "\n".join(lines)
