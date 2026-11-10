"""Healthcare Quality & Patient Safety KPI Tracker - Streamlit app (synthetic data)."""
from pathlib import Path

import pandas as pd
import streamlit as st

from hq_tracker import charts, config, rca, report, spc, ui, whatif
from hq_tracker.data import add_rates, aggregate_monthly, generate

DATA = Path(__file__).parent / "data"
st.set_page_config(page_title="Quality & Patient Safety KPI Tracker", page_icon="🏥", layout="wide")
ui.inject_css()


@st.cache_data
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    m, i = DATA / "synthetic_monthly.csv", DATA / "synthetic_incidents.csv"
    if m.exists() and i.exists():
        monthly = pd.read_csv(m, parse_dates=["month"])
        inc = pd.read_csv(i, parse_dates=["reported", "closed"])
    else:
        d = generate()
        monthly, inc = d["monthly"], d["incidents"]
    return monthly, inc


monthly, incidents = load()

ui.sidebar_brand("Quality & Patient Safety", "Monthly KPI and accreditation tracker")
st.sidebar.markdown("---")
units = st.sidebar.multiselect("Units", config.UNITS, default=config.UNITS)
months = sorted(monthly["month"].dt.to_period("M").astype(str).unique())
report_month = st.sidebar.selectbox("Report month", months, index=len(months) - 1)
st.sidebar.markdown("---")
st.sidebar.markdown("**SPC rules**  \n- Point outside 3σ limits  \n- Shift: 8+ points on one side of the centre line  \n- Trend: 6+ points rising or falling")

if not units:
    st.warning("Select at least one unit.")
    st.stop()

agg = aggregate_monthly(monthly, units)
inc = incidents[incidents["unit"].isin(units)]
rm = pd.Period(report_month).to_timestamp()
cur = agg[agg["month"] == rm].iloc[0]
prev = agg[agg["month"] < rm].iloc[-1] if (agg["month"] < rm).any() else None
inc_month = inc[inc["reported"].dt.to_period("M").dt.to_timestamp() == rm]

ui.hero("Quality & Patient Safety KPI Tracker",
        "Accreditation-style quality dashboard covering incidents, falls, medication safety, infection prevention, "
        "SPC charts and root-cause analysis.",
        ["Patient safety", "Infection prevention", "SPC control charts", "RCA / fishbone", "Improvement scenarios",
         "Monthly report export", "Synthetic data"])

T = config.TARGETS


def d(key: str, higher: bool = False, digits: int = 2) -> str:
    return ui.fmt_delta(None if prev is None else float(cur[key] - prev[key]), "", digits, higher)


c = st.columns(6)
ui.kpi(c[0], "Falls / 1,000 pt-days", f"{cur.fall_rate:.2f}", f"target ≤ {T['fall_rate']} · vs prev. month",
       ui.status_for(cur.fall_rate, T["fall_rate"], T["fall_rate"] * 1.2, False), d("fall_rate"))
ui.kpi(c[1], "Med errors / 1,000 pt-days", f"{cur.med_error_rate:.2f}", f"target ≤ {T['med_error_rate']}",
       ui.status_for(cur.med_error_rate, T["med_error_rate"], T["med_error_rate"] * 1.2, False), d("med_error_rate"))
ui.kpi(c[2], "Hand hygiene", f"{cur.hand_hygiene_pct:.1f}%", f"target ≥ {T['hand_hygiene_pct']:.0f}%",
       ui.status_for(cur.hand_hygiene_pct, T["hand_hygiene_pct"], T["hand_hygiene_pct"] - 5),
       d("hand_hygiene_pct", True, 1))
ui.kpi(c[3], "CLABSI / 1,000 line-days", f"{cur.clabsi_rate:.2f}", f"target ≤ {T['clabsi_rate']}",
       ui.status_for(cur.clabsi_rate, T["clabsi_rate"], T["clabsi_rate"] * 1.5, False), d("clabsi_rate"))
ui.kpi(c[4], "CAUTI / 1,000 catheter-days", f"{cur.cauti_rate:.2f}", f"target ≤ {T['cauti_rate']}",
       ui.status_for(cur.cauti_rate, T["cauti_rate"], T["cauti_rate"] * 1.5, False), d("cauti_rate"))
closed30 = (inc_month["days_to_close"] <= 30).mean() * 100 if len(inc_month) else 0
ui.kpi(c[5], "Incidents closed ≤ 30 d", f"{closed30:.0f}%", f"{len(inc_month)} reported in {report_month}",
       ui.status_for(closed30, T["closure_30d_pct"], T["closure_30d_pct"] - 10))
st.write("")

tabs = st.tabs(["Overview", "Incidents", "SPC charts", "Infection control", "Unit trends", "Improvement scenarios",
                "RCA / Fishbone", "Monthly report"])

with tabs[0]:
    ui.synthetic_banner()
    st.write("")
    cols = st.columns(4)
    for col, (domain, items) in zip(cols, config.DOMAINS.items()):
        ui.card(col, domain, "<br>".join(f"• {x}" for x in items))
    st.write("")
    met = report.scorecard(cur, prev)
    n_met = int((met["Status"] == "Met").sum())
    misses = ", ".join(met.loc[met["Status"] != "Met", "KPI"].head(3)) or "none"
    ui.insight(f"<b>{report_month}</b>: {n_met} of {len(met)} scorecard KPIs met target. Not met: {misses}.")
    l, r = st.columns(2)
    l.plotly_chart(charts.severity_stack(inc), width="stretch")
    r.plotly_chart(charts.category_pareto(inc), width="stretch")

with tabs[1]:
    l, r = st.columns([2, 1])
    sev = inc["severity"].value_counts().reindex(config.SEVERITIES, fill_value=0).reset_index()
    sev.columns = ["Severity", "Incidents"]
    l.plotly_chart(charts.severity_by_unit(inc), width="stretch")
    r.markdown("#### Harm severity mix")
    r.dataframe(sev, hide_index=True, width="stretch")
    rca_req = inc[inc["rca_required"]]
    r.metric("RCA completion (moderate+ harm)", f"{rca_req['rca_completed'].mean() * 100:.0f}%",
             help="Share of moderate/severe incidents with a completed RCA")
    st.plotly_chart(charts.incident_treemap(inc), width="stretch")
    st.markdown("#### Incident log")
    st.dataframe(inc.sort_values("reported", ascending=False).head(200), hide_index=True, width="stretch")

with tabs[2]:
    l, r = st.columns(2)
    ch = spc.u_chart(agg["falls"], agg["patient_days"])
    l.plotly_chart(charts.spc_chart(agg["month"], ch, spc.special_cause_flags(ch),
                                    "Falls per 1,000 patient days (u-chart)", "Rate", T["fall_rate"]),
                   width="stretch")
    ch = spc.u_chart(agg["medication_errors"], agg["patient_days"])
    r.plotly_chart(charts.spc_chart(agg["month"], ch, spc.special_cause_flags(ch),
                                    "Medication errors per 1,000 patient days (u-chart)", "Rate", T["med_error_rate"]),
                   width="stretch")
    ch = spc.p_chart(agg["hh_compliant"], agg["hh_observations"])
    st.plotly_chart(charts.spc_chart(agg["month"], ch, spc.special_cause_flags(ch),
                                     "Hand hygiene compliance (p-chart)", "% compliant", T["hand_hygiene_pct"], pct=True),
                    width="stretch")
    st.caption("Amber diamonds mark special-cause signals. Synthetic data includes a simulated improvement "
               "initiative from month 13 to demonstrate shift detection.")

with tabs[3]:
    l, r = st.columns(2)
    ch = spc.u_chart(agg["clabsi"], agg["central_line_days"])
    l.plotly_chart(charts.spc_chart(agg["month"], ch, spc.special_cause_flags(ch),
                                    "CLABSI per 1,000 central-line days", "Rate", T["clabsi_rate"]), width="stretch")
    ch = spc.u_chart(agg["cauti"], agg["urinary_catheter_days"])
    r.plotly_chart(charts.spc_chart(agg["month"], ch, spc.special_cause_flags(ch),
                                    "CAUTI per 1,000 catheter days", "Rate", T["cauti_rate"]), width="stretch")
    last6 = monthly[monthly["unit"].isin(units) & (monthly["month"] > rm - pd.DateOffset(months=6)) & (monthly["month"] <= rm)]
    ut = add_rates(last6.groupby("unit", as_index=False).sum(numeric_only=True))
    st.plotly_chart(charts.unit_heatmap(ut, ["fall_rate", "med_error_rate", "clabsi_rate", "cauti_rate"],
                                        ["Falls", "Med errors", "CLABSI", "CAUTI"]), width="stretch")
    st.caption("Unit comparison uses the 6 months up to the report month.")

with tabs[4]:
    um = add_rates(monthly[monthly["unit"].isin(units)])
    st.plotly_chart(charts.unit_bubble_animation(um), width="stretch")
    st.caption("Bubble size reflects patient days. Each frame is one month of synthetic data.")

with tabs[5]:
    ui.section("Improvement scenarios",
               "Estimate the annual effect of a falls-prevention bundle and better infection-prevention compliance. "
               "All assumptions are editable.")
    yr = whatif.annualise(agg)
    l, r = st.columns(2)
    with l:
        st.markdown("##### Falls-prevention bundle")
        eff = st.slider("Expected reduction where the bundle is used (%)", 0, 50, 25)
        adopt = st.slider("Bundle adoption (% of at-risk patients)", 0, 100, 70)
        cost = st.number_input("Cost per fall with harm (SAR, assumption)", 0, 200000, 25000, 1000)
        los = st.number_input("Extra length of stay per fall with harm (days, assumption)", 0.0, 20.0, 4.0, 0.5)
        fi = whatif.falls_impact(yr["falls"], yr["falls_with_harm"], eff, adopt, cost, los)
        m1, m2, m3 = st.columns(3)
        ui.kpi(m1, "Falls avoided / yr", f"{fi['falls_avoided']:.0f}", f"{fi['relative_reduction_pct']:.1f}% fewer")
        ui.kpi(m2, "Bed-days saved / yr", f"{fi['bed_days_saved']:.0f}", f"{fi['harm_falls_avoided']:.1f} harm falls")
        ui.kpi(m3, "Cost avoided / yr", f"SAR {fi['cost_avoided_sar'] / 1e3:,.0f}k", "at the assumed cost")
        st.plotly_chart(charts.impact_waterfall(yr["falls"], fi["falls_avoided"], "Inpatient falls"), width="stretch")
    with r:
        st.markdown("##### Infection-prevention compliance")
        gain = st.slider("Bundle / hand-hygiene compliance gain (points)", 0, 20, 8)
        red = st.slider("Relative HAI reduction per 10 points of compliance (%)", 0, 40, 15)
        c_cl = st.number_input("Cost per CLABSI (SAR, assumption)", 0, 500000, 90000, 5000)
        c_ca = st.number_input("Cost per CAUTI (SAR, assumption)", 0, 200000, 20000, 1000)
        hi = whatif.hai_impact(yr["clabsi"], yr["cauti"], gain, red, c_cl, c_ca)
        m1, m2, m3 = st.columns(3)
        ui.kpi(m1, "CLABSI avoided / yr", f"{hi['clabsi_avoided']:.1f}", f"{hi['relative_reduction_pct']:.0f}% fewer")
        ui.kpi(m2, "CAUTI avoided / yr", f"{hi['cauti_avoided']:.1f}", "catheter-associated")
        ui.kpi(m3, "Cost avoided / yr", f"SAR {hi['cost_avoided_sar'] / 1e3:,.0f}k", "at the assumed costs")
        st.plotly_chart(charts.impact_waterfall(yr["clabsi"] + yr["cauti"], hi["clabsi_avoided"] + hi["cauti_avoided"],
                                                "CLABSI + CAUTI"), width="stretch")
    st.caption("Baselines are the last 12 months for the selected units. Effect sizes and costs are planning "
               "assumptions to be replaced with local evidence.")

with tabs[6]:
    problem = st.text_input("Problem statement", "Increase in inpatient falls on Medical Ward A")
    fb = rca.empty_fishbone(problem)
    st.plotly_chart(charts.fishbone_figure(fb), width="stretch")
    st.markdown("#### Contributing factors (edit to capture your team's analysis)")
    cols = st.columns(3)
    for i, cat in enumerate(rca.FISHBONE_CATEGORIES):
        txt = cols[i % 3].text_area(cat, "\n".join(fb["causes"][cat]), height=110, key=f"fb_{i}")
        fb["causes"][cat] = [x for x in txt.splitlines() if x.strip()]
    st.markdown("#### Action plan")
    st.data_editor(rca.action_plan_template(), num_rows="dynamic", width="stretch", hide_index=True)
    st.download_button("Download RCA template (Markdown)", rca.fishbone_to_markdown(fb), "rca_fishbone.md")

with tabs[7]:
    sc = report.scorecard(cur, prev)
    st.markdown(f"### Scorecard – {report_month}")
    st.dataframe(sc.style.map(lambda v: "color:#2a9d8f;font-weight:600" if v == "Met" else
                              ("color:#d1495b;font-weight:600" if v == "Not met" else ""), subset=["Status"]),
                 hide_index=True, width="stretch")
    mm = monthly[(monthly["month"] == rm) & monthly["unit"].isin(units)]
    unit_tbl = add_rates(mm)[["unit", "patient_days", "falls", "medication_errors", "fall_rate", "med_error_rate",
                              "hand_hygiene_pct", "clabsi_rate", "cauti_rate"]].round(2)
    st.markdown("#### By unit")
    st.dataframe(unit_tbl, hide_index=True, width="stretch")
    a, b = st.columns(2)
    a.download_button("Export monthly report (Excel)", report.to_excel(sc, unit_tbl, inc_month),
                      f"quality_report_{report_month}.xlsx")
    b.download_button("Export summary (Markdown)", report.to_markdown(report_month, sc, inc_month),
                      f"quality_report_{report_month}.md")

ui.footer()
