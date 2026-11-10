"""Plotly figures for the quality tracker."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from . import config
from .ui import AMBER, NAVY, PALETTE, RED, SKY, TEAL

pio.templates["navy"] = go.layout.Template(pio.templates["plotly_white"])
pio.templates["navy"].layout.colorway = PALETTE
pio.templates["navy"].layout.font = dict(family="Inter, Segoe UI, sans-serif", color=NAVY)
TEMPLATE = "navy"

SEVERITY_COLORS = dict(zip(config.SEVERITIES, [SKY, TEAL, AMBER, "#f4a261", RED]))


def spc_chart(x, chart: pd.DataFrame, flags: pd.Series, title: str, y_title: str,
              target: float | None = None, pct: bool = False) -> go.Figure:
    k = 100 if pct else 1
    fig = go.Figure()
    fig.add_scatter(x=x, y=chart["ucl"] * k, name="UCL (3σ)", line=dict(color=RED, dash="dash", shape="hv"))
    fig.add_scatter(x=x, y=chart["lcl"] * k, name="LCL (3σ)", line=dict(color=RED, dash="dash", shape="hv"))
    fig.add_scatter(x=x, y=chart["cl"] * k, name="Centre line", line=dict(color=SKY, width=2))
    fig.add_scatter(x=x, y=chart["value"] * k, name="Observed", mode="lines+markers",
                    line=dict(color=NAVY, width=2.5), marker=dict(size=7))
    sig = flags != ""
    if sig.any():
        fig.add_scatter(x=pd.Series(x)[sig.values], y=chart["value"][sig] * k, mode="markers", name="Special cause",
                        marker=dict(color=AMBER, size=13, symbol="diamond", line=dict(color=NAVY, width=1)),
                        text=flags[sig], hovertemplate="%{text}<extra></extra>")
    if target is not None:
        fig.add_hline(y=target, line_color=TEAL, line_dash="dot", annotation_text=f"Target {target}")
    fig.update_layout(template=TEMPLATE, title=title, yaxis_title=y_title, height=400, margin=dict(t=60),
                      legend=dict(orientation="h", y=-0.18))
    return fig


def severity_stack(incidents: pd.DataFrame) -> go.Figure:
    t = incidents.assign(month=incidents["reported"].dt.to_period("M").dt.to_timestamp()) \
        .groupby(["month", "severity"]).size().reset_index(name="count")
    fig = px.bar(t, x="month", y="count", color="severity", color_discrete_map=SEVERITY_COLORS,
                 category_orders={"severity": config.SEVERITIES})
    fig.update_layout(template=TEMPLATE, title="Incidents reported per month by harm severity",
                      yaxis_title="Incidents", xaxis_title="", height=400, margin=dict(t=60),
                      legend=dict(orientation="h", y=-0.18))
    return fig


def category_pareto(incidents: pd.DataFrame) -> go.Figure:
    c = incidents["category"].value_counts()
    cum = c.cumsum() / c.sum() * 100
    fig = go.Figure()
    fig.add_bar(x=c.index, y=c.values, name="Incidents", marker_color=NAVY)
    fig.add_scatter(x=c.index, y=cum.values, name="Cumulative %", yaxis="y2", mode="lines+markers",
                    line=dict(color=AMBER, width=3))
    fig.update_layout(template=TEMPLATE, title="Pareto of incident categories", height=400, margin=dict(t=60),
                      yaxis=dict(title="Incidents"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right",
                                                                 range=[0, 105], tickmode="linear", dtick=25, showgrid=False),
                      legend=dict(orientation="h", y=-0.25))
    return fig


def unit_heatmap(table: pd.DataFrame, metrics: list[str], labels: list[str]) -> go.Figure:
    z = table.set_index("unit")[metrics]
    fig = px.imshow(z, x=labels, y=z.index, color_continuous_scale="RdYlGn_r", aspect="auto", text_auto=".2f")
    fig.update_layout(template=TEMPLATE, title="Unit comparison (red = worse relative performance)", height=380,
                      margin=dict(t=60), coloraxis_showscale=False)
    return fig


def fishbone_figure(fb: dict) -> go.Figure:
    """Draw an Ishikawa diagram with Plotly shapes."""
    cats = list(fb["causes"].keys())
    fig = go.Figure()
    fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=0, line=dict(color=NAVY, width=4))
    import textwrap
    label = "<br>".join(textwrap.wrap(fb["problem"], 24)) or "Problem"
    fig.add_annotation(x=10.15, y=0, text=f"<b>{label}</b>", showarrow=False, xanchor="left",
                       font=dict(size=13, color="#fff"), bgcolor=NAVY, borderpad=10, align="left")
    xs = [2.0, 5.0, 8.0]
    for i, cat in enumerate(cats):
        x = xs[i % 3]
        up = i < 3
        y_end = 3.2 if up else -3.2
        fig.add_shape(type="line", x0=x - 1.6, y0=y_end, x1=x, y1=0, line=dict(color=TEAL, width=3))
        fig.add_annotation(x=x - 1.6, y=y_end + (0.45 if up else -0.45), text=f"<b>{cat}</b>", showarrow=False,
                           font=dict(color=NAVY, size=12))
        for j, cause in enumerate(fb["causes"][cat][:4]):
            frac = (j + 1) / 5
            cx, cy = x - 1.6 * (1 - frac), y_end * (1 - frac)
            fig.add_annotation(x=cx - 0.1, y=cy, text=cause, showarrow=False, xanchor="right", font=dict(size=10))
    fig.update_xaxes(visible=False, range=[-1.2, 13.6])
    fig.update_yaxes(visible=False, range=[-4.2, 4.2])
    fig.update_layout(template=TEMPLATE, height=460, margin=dict(l=10, r=10, t=30, b=10), title="Fishbone (Ishikawa) diagram")
    return fig


def severity_by_unit(incidents: pd.DataFrame) -> go.Figure:
    t = incidents.groupby(["unit", "severity"]).size().reset_index(name="count")
    fig = px.bar(t, y="unit", x="count", color="severity", orientation="h", color_discrete_map=SEVERITY_COLORS,
                 category_orders={"severity": config.SEVERITIES})
    fig.update_layout(template=TEMPLATE, title="Incidents by unit and harm severity", xaxis_title="Incidents",
                      yaxis_title="", height=400, margin=dict(t=60), legend=dict(orientation="h", y=-0.2))
    return fig


def incident_treemap(incidents: pd.DataFrame) -> go.Figure:
    """Click a unit or category to drill down; click the centre to go back up."""
    t = incidents.groupby(["unit", "category", "severity"]).size().reset_index(name="incidents")
    fig = px.treemap(t, path=[px.Constant("All units"), "unit", "category", "severity"], values="incidents",
                     color="severity", color_discrete_map={**SEVERITY_COLORS, "(?)": "#dfe7f1"})
    fig.update_traces(root_color="#eef2f7", textinfo="label+value", maxdepth=3,
                      hovertemplate="%{label}<br>%{value} incidents")
    fig.update_layout(template=TEMPLATE, title="Incident drill-down · click a unit, then a category",
                      height=520, margin=dict(t=60, l=5, r=5, b=5))
    return fig


def unit_bubble_animation(unit_month: pd.DataFrame) -> go.Figure:
    """Animated unit trajectories: hand hygiene vs fall rate per month."""
    d = unit_month.copy()
    d["month_label"] = d["month"].dt.strftime("%Y-%m")
    d = d.sort_values("month")
    fig = px.scatter(d, x="hand_hygiene_pct", y="fall_rate", size="patient_days", color="unit",
                     animation_frame="month_label", animation_group="unit", size_max=46, text="unit",
                     color_discrete_sequence=PALETTE,
                     range_x=[d["hand_hygiene_pct"].min() - 3, 100], range_y=[0, d["fall_rate"].quantile(0.98) * 1.2],
                     labels={"hand_hygiene_pct": "Hand hygiene compliance %", "fall_rate": "Falls / 1,000 patient days",
                             "month_label": "Month"})
    fig.add_vline(x=config.TARGETS["hand_hygiene_pct"], line_dash="dot", line_color=TEAL)
    fig.add_hline(y=config.TARGETS["fall_rate"], line_dash="dot", line_color=RED)
    fig.update_traces(textposition="top center", textfont=dict(size=10))
    fig.update_layout(template=TEMPLATE, height=520, margin=dict(t=60), showlegend=False,
                      title="Unit trajectories month by month · press ▶ (target zone: right of teal, below red)")
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 700
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 400
    return fig


def impact_waterfall(baseline: float, avoided: float, label: str, unit: str = "events / year") -> go.Figure:
    fig = go.Figure(go.Waterfall(x=["Current", "Avoided", "Scenario"], measure=["absolute", "relative", "total"],
                                 y=[baseline, -avoided, 0], text=[f"{baseline:.1f}", f"-{avoided:.1f}",
                                                                  f"{baseline - avoided:.1f}"],
                                 textposition="outside", connector=dict(line=dict(color=SKY)),
                                 decreasing=dict(marker=dict(color=TEAL)), totals=dict(marker=dict(color=NAVY)),
                                 increasing=dict(marker=dict(color=RED))))
    fig.update_layout(template=TEMPLATE, title=f"{label} ({unit})", height=340, margin=dict(t=60),
                      yaxis=dict(range=[0, baseline * 1.25 if baseline else 1]))
    return fig
