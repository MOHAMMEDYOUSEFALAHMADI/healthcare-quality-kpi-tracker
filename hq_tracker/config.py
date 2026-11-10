"""Units, CBAHI-style domains, KPI definitions and targets.

Domain names follow the general structure of hospital accreditation standards
(e.g. CBAHI-style chapters). They are illustrative and not an official mapping.
"""

UNITS = ["Medical Ward A", "Surgical Ward B", "ICU", "Emergency Dept", "Paediatrics", "Maternity"]

# Baseline patient days per month and device days (central line / urinary catheter)
UNIT_PROFILE = {
    "Medical Ward A":  {"patient_days": 900, "cl_days": 120, "uc_days": 260, "fall_rate": 3.2, "hh_base": 0.86},
    "Surgical Ward B": {"patient_days": 820, "cl_days": 140, "uc_days": 300, "fall_rate": 2.1, "hh_base": 0.88},
    "ICU":             {"patient_days": 300, "cl_days": 240, "uc_days": 250, "fall_rate": 0.8, "hh_base": 0.91},
    "Emergency Dept":  {"patient_days": 600, "cl_days": 40,  "uc_days": 90,  "fall_rate": 1.6, "hh_base": 0.80},
    "Paediatrics":     {"patient_days": 450, "cl_days": 60,  "uc_days": 40,  "fall_rate": 1.0, "hh_base": 0.89},
    "Maternity":       {"patient_days": 520, "cl_days": 20,  "uc_days": 110, "fall_rate": 0.6, "hh_base": 0.87},
}

DOMAINS = {
    "Patient Safety (PS)": ["Falls", "Medication errors", "Incident reporting"],
    "Infection Prevention & Control (IPC)": ["Hand hygiene", "CLABSI", "CAUTI"],
    "Quality Management (QM)": ["Incident closure", "RCA completion"],
    "Patient-Centred Care (PC)": ["Complaints"],
}

INCIDENT_CATEGORIES = ["Fall", "Medication error", "Pressure injury", "Patient identification",
                       "Equipment / device", "Delay in care", "Documentation", "Other"]
INCIDENT_WEIGHTS = [0.18, 0.22, 0.08, 0.07, 0.10, 0.12, 0.15, 0.08]

# Severity scale (harm-based, NCC MERP-like simplified)
SEVERITIES = ["Near miss", "No harm", "Minor harm", "Moderate harm", "Severe harm / Sentinel"]
SEVERITY_WEIGHTS = [0.30, 0.42, 0.19, 0.075, 0.015]

# KPI targets
TARGETS = {
    "fall_rate": 2.5,            # falls per 1,000 patient days (lower is better)
    "fall_injury_rate": 0.5,     # falls with harm per 1,000 patient days
    "med_error_rate": 3.0,       # medication errors per 1,000 patient days
    "hand_hygiene_pct": 90.0,    # % compliant observations (higher is better)
    "clabsi_rate": 1.0,          # per 1,000 central-line days
    "cauti_rate": 1.5,           # per 1,000 urinary catheter days
    "closure_30d_pct": 85.0,     # % incidents closed within 30 days
}
