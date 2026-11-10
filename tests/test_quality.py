import numpy as np
import pandas as pd
import pytest

from hq_tracker import charts, config, rca, report, spc
from hq_tracker.data import aggregate_monthly, generate


@pytest.fixture(scope="module")
def data():
    return generate(months=18, seed=3)


def test_generator_shapes(data):
    m, i = data["monthly"], data["incidents"]
    assert len(m) == 18 * len(config.UNITS)
    assert set(i["severity"]) <= set(config.SEVERITIES)
    assert i["incident_id"].str.startswith("SYN-").all()
    assert (m["hh_compliant"] <= m["hh_observations"]).all()


def test_fall_incidents_match_monthly(data):
    assert (data["incidents"]["category"] == "Fall").sum() == data["monthly"]["falls"].sum()


def test_rates(data):
    agg = aggregate_monthly(data["monthly"])
    row = agg.iloc[0]
    assert row["fall_rate"] == pytest.approx(row["falls"] / row["patient_days"] * 1000)
    assert agg["hand_hygiene_pct"].between(0, 100).all()


def test_p_chart_limits():
    ch = spc.p_chart(pd.Series([90, 85, 95]), pd.Series([100, 100, 100]))
    assert ch["cl"].iloc[0] == pytest.approx(0.9)
    assert (ch["ucl"] >= ch["cl"]).all() and (ch["lcl"] <= ch["cl"]).all()
    assert (ch["ucl"] <= 1).all()


def test_u_chart_centre():
    ch = spc.u_chart(pd.Series([2, 4]), pd.Series([1000, 1000]))
    assert ch["cl"].iloc[0] == pytest.approx(3.0)


def test_special_cause_outside_limits():
    ch = pd.DataFrame({"value": [1, 1, 9, 1], "cl": 1.0, "ucl": 3.0, "lcl": 0.0})
    assert spc.special_cause_flags(ch).iloc[2] == "Outside limits"


def test_special_cause_shift_and_trend():
    v = np.array([1.1] * 8 + [0.9, 0.95])
    ch = pd.DataFrame({"value": v, "cl": 1.0, "ucl": 5.0, "lcl": -5.0})
    f = spc.special_cause_flags(ch)
    assert (f.iloc[:8] == "Shift").all()
    ch2 = pd.DataFrame({"value": [1, 2, 3, 4, 5, 6, 3], "cl": 3.5, "ucl": 50.0, "lcl": -50.0})
    assert "Trend" in set(spc.special_cause_flags(ch2))


def test_rca_markdown():
    fb = rca.empty_fishbone("Test problem")
    md = rca.fishbone_to_markdown(fb)
    assert "Test problem" in md and all(c in md for c in rca.FISHBONE_CATEGORIES)


def test_report_exports(data):
    agg = aggregate_monthly(data["monthly"])
    sc = report.scorecard(agg.iloc[-1], agg.iloc[-2])
    assert set(sc["Status"]) <= {"Met", "Not met"}
    xlsx = report.to_excel(sc, agg, data["incidents"].head(20))
    assert xlsx[:2] == b"PK"  # zip container
    assert "Monthly Quality" in report.to_markdown("2025-06", sc, data["incidents"].head(20))


def test_charts_build(data):
    agg = aggregate_monthly(data["monthly"])
    ch = spc.u_chart(agg["falls"], agg["patient_days"])
    assert charts.spc_chart(agg["month"], ch, spc.special_cause_flags(ch), "t", "y", 2.5).data
    assert charts.severity_stack(data["incidents"]).data
    assert charts.category_pareto(data["incidents"]).data
    assert charts.fishbone_figure(rca.empty_fishbone("x")).layout.shapes


def test_falls_impact_scales_with_adoption():
    from hq_tracker import whatif
    lo = whatif.falls_impact(100, 20, 30, 50, 10000, 3)
    hi = whatif.falls_impact(100, 20, 30, 100, 10000, 3)
    assert hi["falls_avoided"] == pytest.approx(2 * lo["falls_avoided"])
    assert hi["falls_avoided"] == pytest.approx(30)
    assert hi["cost_avoided_sar"] == pytest.approx(6 * 10000)
    assert whatif.falls_impact(100, 20, 0, 100, 1, 1)["falls_avoided"] == 0


def test_hai_impact_is_capped():
    from hq_tracker import whatif
    r = whatif.hai_impact(10, 10, 100, 50, 1, 1)
    assert r["relative_reduction_pct"] == pytest.approx(80)
    assert r["clabsi_avoided"] == pytest.approx(8)


def test_annualise_scales_partial_year(data):
    from hq_tracker import whatif
    agg = aggregate_monthly(data["monthly"])
    six = whatif.annualise(agg, 6)
    assert six["falls"] == pytest.approx(agg.tail(6)["falls"].sum() * 2)


def test_new_quality_charts_build(data):
    from hq_tracker.data import add_rates
    charts.incident_treemap(data["incidents"])
    fig = charts.unit_bubble_animation(add_rates(data["monthly"]))
    assert len(fig.frames) == data["monthly"]["month"].nunique()
    charts.impact_waterfall(50, 10, "Falls")
