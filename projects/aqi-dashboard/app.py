"""
Air Quality Data Dashboard — portfolio project for Divyanshu Samal.

Interactive Streamlit + Plotly dashboard for AQI / pollutant data across
major Indian cities, with OpenAQ API v3 integration and offline sample fallback.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.charts import (
    aqi_gauge,
    city_bar_chart,
    heatmap_chart,
    insight_bullets,
    map_chart,
    pollutant_box_chart,
    timeseries_chart,
)
from src.data import (
    PARAM_LABELS,
    city_comparison,
    compute_kpis,
    daily_timeseries,
    filter_data,
    load_aqi_data,
)

st.set_page_config(
    page_title="India AQI Dashboard | Divyanshu Samal",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PARAM_OPTIONS = {
    "PM2.5": "pm25",
    "PM10": "pm10",
    "O₃": "o3",
    "NO₂": "no2",
    "CO": "co",
    "SO₂": "so2",
}


@st.cache_data(ttl=600, show_spinner="Loading air quality data…")
def cached_load(prefer_live: bool) -> tuple[pd.DataFrame, str]:
    return load_aqi_data(prefer_live=prefer_live)


def main() -> None:
    st.title("🌫️ India Air Quality Dashboard")
    st.caption(
        "Portfolio project · Divyanshu Samal · Pandas · Plotly · Streamlit · OpenAQ"
    )

    with st.sidebar:
        st.header("Filters")
        prefer_live = st.toggle(
            "Try live OpenAQ API",
            value=False,
            help="Requires OPENAQ_API_KEY for API v3. Falls back to sample CSV.",
        )
        df, source_label = cached_load(prefer_live)

        cities_all = sorted(df["city"].dropna().unique().tolist())
        default_cities = [c for c in ["Delhi", "Mumbai", "Bengaluru", "Kolkata"] if c in cities_all]
        if not default_cities:
            default_cities = cities_all[:4]

        selected_cities = st.multiselect(
            "Cities",
            options=cities_all,
            default=default_cities,
        )
        pollutant_label = st.selectbox("Pollutant", list(PARAM_OPTIONS.keys()), index=0)
        parameter = PARAM_OPTIONS[pollutant_label]

        min_d = df["datetime"].min().date() if not df.empty else date(2026, 5, 1)
        max_d = df["datetime"].max().date() if not df.empty else date(2026, 8, 20)
        date_range = st.date_input(
            "Time range",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
        )

        st.divider()
        st.markdown(f"**Data source:** {source_label}")
        st.caption(
            "OpenAQ v3 needs `OPENAQ_API_KEY` (see `.env.example`). "
            "Sample data always available offline."
        )
        if st.button("Clear cache & reload"):
            cached_load.clear()
            st.rerun()

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
    else:
        start_d, end_d = min_d, max_d

    start_ts = pd.Timestamp(start_d, tz="UTC")
    end_ts = pd.Timestamp(end_d, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    filtered = filter_data(
        df,
        cities=selected_cities or cities_all,
        parameters=None,  # keep all pollutants for box/KPIs; charts pick parameter
        start=start_ts,
        end=end_ts,
    )
    filtered_param = filter_data(
        filtered,
        parameters=[parameter],
    )

    kpis = compute_kpis(filtered)
    comparison = city_comparison(filtered, parameter=parameter)
    daily = daily_timeseries(filtered, parameter=parameter)

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cities", kpis["n_cities"])
    c2.metric(
        "Worst city (PM2.5)",
        kpis["worst_city"],
        None if kpis["worst_pm25"] is None else f"{kpis['worst_pm25']:.0f} µg/m³",
    )
    c3.metric(
        "Best city (PM2.5)",
        kpis["best_city"],
        None if kpis["best_pm25"] is None else f"{kpis['best_pm25']:.0f} µg/m³",
    )
    c4.metric(
        "Est. AQI",
        "—" if kpis["avg_aqi"] is None else f"{kpis['avg_aqi']:.0f}",
        kpis["aqi_category"] if kpis["avg_aqi"] is not None else None,
    )
    trend = kpis.get("trend_pct")
    c5.metric(
        "7d PM2.5 trend",
        "—" if trend is None else f"{trend:+.1f}%",
        help="Recent 7 days vs previous 7 days (PM2.5 mean)",
    )

    st.subheader("Storytelling insights")
    for bullet in insight_bullets(kpis, parameter):
        st.markdown(f"- {bullet}")

    left, right = st.columns((1.2, 1))
    with left:
        st.plotly_chart(
            timeseries_chart(daily, parameter),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(aqi_gauge(kpis.get("avg_pm25")), use_container_width=True)
        st.plotly_chart(
            city_bar_chart(comparison, parameter),
            use_container_width=True,
        )

    t1, t2, t3 = st.tabs(["Distributions", "Heatmap", "Map"])
    with t1:
        st.plotly_chart(
            pollutant_box_chart(filtered, cities=selected_cities or cities_all),
            use_container_width=True,
        )
    with t2:
        st.plotly_chart(
            heatmap_chart(filtered, parameter=parameter),
            use_container_width=True,
        )
    with t3:
        st.plotly_chart(
            map_chart(filtered, parameter=parameter),
            use_container_width=True,
        )

    with st.expander("Filtered data preview", expanded=False):
        show = filtered_param.copy()
        show["datetime"] = show["datetime"].dt.strftime("%Y-%m-%d %H:%M UTC")
        show["parameter"] = show["parameter"].map(lambda p: PARAM_LABELS.get(p, p))
        st.dataframe(
            show.head(500),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing up to 500 of {len(filtered_param):,} filtered {pollutant_label} rows.")

    st.divider()
    st.markdown(
        "Built for CV portfolio · Sample data covers Delhi, Mumbai, Bengaluru, "
        "Kolkata, Chennai, Hyderabad, Pune, Ahmedabad · "
        "[OpenAQ](https://openaq.org/) for live feeds"
    )


if __name__ == "__main__":
    main()
