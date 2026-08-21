"""Plotly chart builders for the AQI dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data import PARAM_LABELS, aqi_category, estimate_aqi_from_pm25

COLORWAY = [
    "#e63946",
    "#457b9d",
    "#2a9d8f",
    "#e9c46a",
    "#9b5de5",
    "#f4a261",
    "#00bbf9",
    "#118ab2",
]

AQI_COLORS = {
    "Good": "#22c55e",
    "Satisfactory": "#84cc16",
    "Moderate": "#eab308",
    "Poor": "#f97316",
    "Very Poor": "#ef4444",
    "Severe": "#7f1d1d",
    "Unknown": "#94a3b8",
}


def _empty_fig(message: str = "No data for current filters") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#64748b"),
    )
    fig.update_layout(
        template="plotly_white",
        height=380,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def timeseries_chart(daily: pd.DataFrame, parameter: str) -> go.Figure:
    label = PARAM_LABELS.get(parameter, parameter.upper())
    if daily is None or daily.empty:
        return _empty_fig(f"No {label} time-series data")
    fig = px.line(
        daily,
        x="date",
        y="value",
        color="city",
        markers=True,
        color_discrete_sequence=COLORWAY,
        title=f"{label} — daily average by city",
        labels={"date": "Date", "value": label, "city": "City"},
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode="x unified",
    )
    return fig


def city_bar_chart(comparison: pd.DataFrame, parameter: str) -> go.Figure:
    label = PARAM_LABELS.get(parameter, parameter.upper())
    if comparison is None or comparison.empty:
        return _empty_fig(f"No {label} city comparison data")
    fig = px.bar(
        comparison,
        x="city",
        y="mean",
        color="mean",
        color_continuous_scale="YlOrRd",
        title=f"Mean {label} by city",
        labels={"city": "City", "mean": f"Mean {label}"},
        text_auto=".1f",
    )
    fig.update_layout(
        template="plotly_white",
        height=400,
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def pollutant_box_chart(df: pd.DataFrame, cities: list[str] | None = None) -> go.Figure:
    subset = df.copy()
    if cities:
        subset = subset[subset["city"].isin(cities)]
    if subset.empty:
        return _empty_fig()
    subset = subset.copy()
    subset["pollutant"] = subset["parameter"].map(lambda p: PARAM_LABELS.get(p, p))
    fig = px.box(
        subset,
        x="pollutant",
        y="value",
        color="city",
        color_discrete_sequence=COLORWAY,
        title="Pollutant distribution by city",
        labels={"pollutant": "Pollutant", "value": "Concentration", "city": "City"},
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def heatmap_chart(df: pd.DataFrame, parameter: str = "pm25") -> go.Figure:
    label = PARAM_LABELS.get(parameter, parameter.upper())
    subset = df[df["parameter"] == parameter].copy()
    if subset.empty:
        return _empty_fig(f"No {label} data for heatmap")
    subset["date"] = subset["datetime"].dt.floor("D")
    pivot = (
        subset.groupby(["city", "date"])["value"]
        .mean()
        .reset_index()
        .pivot(index="city", columns="date", values="value")
    )
    if pivot.empty:
        return _empty_fig()
    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="YlOrRd",
        title=f"{label} heatmap — city × day",
        labels=dict(color=label, x="Date", y="City"),
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=80, r=20, t=60, b=40),
    )
    return fig


def map_chart(df: pd.DataFrame, parameter: str = "pm25") -> go.Figure:
    label = PARAM_LABELS.get(parameter, parameter.upper())
    subset = df[df["parameter"] == parameter].dropna(subset=["latitude", "longitude"])
    if subset.empty:
        return _empty_fig(f"No geo-tagged {label} data")
    agg = (
        subset.groupby(["city", "location"], as_index=False)
        .agg(value=("value", "mean"), latitude=("latitude", "mean"), longitude=("longitude", "mean"))
    )
    fig = px.scatter_mapbox(
        agg,
        lat="latitude",
        lon="longitude",
        size="value",
        color="value",
        hover_name="location",
        hover_data={"city": True, "value": ":.1f", "latitude": False, "longitude": False},
        color_continuous_scale="YlOrRd",
        size_max=28,
        zoom=3.8,
        center={"lat": 22.5, "lon": 80.0},
        title=f"Monitoring locations — mean {label}",
        mapbox_style="open-street-map",
    )
    fig.update_layout(
        height=460,
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar=dict(title=label),
    )
    return fig


def aqi_gauge(avg_pm25: float | None) -> go.Figure:
    if avg_pm25 is None or pd.isna(avg_pm25):
        return _empty_fig("AQI unavailable (need PM2.5)")
    aqi = estimate_aqi_from_pm25(float(avg_pm25))
    cat = aqi_category(aqi)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=aqi,
            number={"suffix": f"  {cat}"},
            title={"text": "Estimated AQI (from mean PM2.5)"},
            gauge={
                "axis": {"range": [0, 500]},
                "bar": {"color": AQI_COLORS.get(cat, "#64748b")},
                "steps": [
                    {"range": [0, 50], "color": "#dcfce7"},
                    {"range": [50, 100], "color": "#ecfccb"},
                    {"range": [100, 200], "color": "#fef9c3"},
                    {"range": [200, 300], "color": "#ffedd5"},
                    {"range": [300, 400], "color": "#fee2e2"},
                    {"range": [400, 500], "color": "#fecaca"},
                ],
                "threshold": {
                    "line": {"color": "#0f172a", "width": 3},
                    "thickness": 0.75,
                    "value": aqi,
                },
            },
        )
    )
    fig.update_layout(template="plotly_white", height=280, margin=dict(l=30, r=30, t=50, b=10))
    return fig


def insight_bullets(kpis: dict, parameter: str) -> list[str]:
    """Short storytelling lines for the dashboard."""
    label = PARAM_LABELS.get(parameter, parameter.upper())
    bullets: list[str] = []
    if kpis.get("worst_city") and kpis.get("worst_city") != "—":
        wp = kpis.get("worst_pm25")
        bp = kpis.get("best_pm25")
        bullets.append(
            f"**{kpis['worst_city']}** shows the highest average PM2.5"
            + (f" (~{wp:.0f} µg/m³)" if wp is not None else "")
            + f", while **{kpis['best_city']}** is relatively cleaner"
            + (f" (~{bp:.0f} µg/m³)." if bp is not None else ".")
        )
    if kpis.get("avg_aqi") is not None:
        bullets.append(
            f"Across selected cities, mean PM2.5 implies an estimated AQI of "
            f"**{kpis['avg_aqi']:.0f}** ({kpis.get('aqi_category', 'Unknown')})."
        )
    trend = kpis.get("trend_pct")
    if trend is not None:
        direction = "worsened" if trend > 0 else "improved"
        bullets.append(
            f"Recent 7-day PM2.5 has **{direction} by {abs(trend):.1f}%** vs the prior week."
        )
    if kpis.get("dominant_pollutant") and kpis["dominant_pollutant"] != "—":
        bullets.append(
            f"Among measured species in this filter window, **{kpis['dominant_pollutant']}** "
            f"has the highest average concentration (raw units; compare like-with-like)."
        )
    if not bullets:
        bullets.append(f"Adjust filters to explore {label} patterns across Indian cities.")
    return bullets
