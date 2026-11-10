"""Root cause analysis (RCA) helpers: fishbone (Ishikawa) template and action plan scaffold."""
from __future__ import annotations

import pandas as pd

FISHBONE_CATEGORIES = ["People / Staff", "Process / Procedure", "Equipment / Technology",
                       "Environment", "Patient factors", "Policy / Communication"]

PROMPTS = {
    "People / Staff": ["Staffing level / skill mix", "Training & competency", "Fatigue / workload"],
    "Process / Procedure": ["Policy followed?", "Handover quality", "Double-check steps"],
    "Equipment / Technology": ["Device availability", "Alarm / alert design", "EMR usability"],
    "Environment": ["Lighting / layout", "Noise & interruptions", "Bed / bathroom access"],
    "Patient factors": ["Acuity / comorbidity", "Cognition / mobility", "Language / health literacy"],
    "Policy / Communication": ["Escalation pathway", "Team communication", "Patient & family education"],
}


def empty_fishbone(problem: str) -> dict:
    return {"problem": problem, "causes": {c: list(PROMPTS[c]) for c in FISHBONE_CATEGORIES}}


def fishbone_to_markdown(fb: dict) -> str:
    lines = [f"# RCA – Fishbone analysis", "", f"**Problem statement:** {fb['problem']}", ""]
    for cat, causes in fb["causes"].items():
        lines.append(f"## {cat}")
        lines += [f"- {c}" for c in causes if c.strip()] or ["- _(none recorded)_"]
        lines.append("")
    lines += ["## Action plan", "", "| # | Action | Owner | Due | Measure of success |",
              "|---|---|---|---|---|", "| 1 |  |  |  |  |", "| 2 |  |  |  |  |", ""]
    return "\n".join(lines)


def action_plan_template(n: int = 5) -> pd.DataFrame:
    return pd.DataFrame({"Action": [""] * n, "Root cause addressed": [""] * n, "Owner": [""] * n,
                         "Due date": [None] * n, "Status": ["Not started"] * n})
