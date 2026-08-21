"""Data loading for the AQI dashboard: OpenAQ v3 fetch with CSV fallback."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_aqi_india.csv"

OPENAQ_BASE = "https://api.openaq.org/v3"
DEFAULT_CITIES = [
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Kolkata",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
]

# OpenAQ v3 parameter name aliases -> dashboard keys
PARAM_ALIASES = {
    "pm25": "pm25",
    "pm2.5": "pm25",
    "pm10": "pm10",
    "o3": "o3",
    "no2": "no2",
    "co": "co",
    "so2": "so2",
}

PARAM_LABELS = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "o3": "O₃",
    "no2": "NO₂",
    "co": "CO",
    "so2": "SO₂",
}

# Approximate India CPCB breakpoints for a simple AQI estimate from PM2.5 (µg/m³)
PM25_BREAKPOINTS = [
    (0, 30, 0, 50),
    (30, 60, 51, 100),
    (60, 90, 101, 200),
    (90, 120, 201, 300),
    (120, 250, 301, 400),
    (250, 500, 401, 500),
]


def get_api_key() -> Optional[str]:
    key = os.getenv("OPENAQ_API_KEY", "").strip()
    if not key or key.startswith("your_"):
        return None
    return key


def _headers() -> dict:
    headers = {"Accept": "application/json"}
    key = get_api_key()
    if key:
        headers["X-API-Key"] = key
    return headers


def load_sample_data(path: Optional[Path] = None) -> pd.DataFrame:
    """Load bundled offline sample measurements for Indian cities."""
    csv_path = Path(path) if path else SAMPLE_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"Sample data not found: {csv_path}")
    df = pd.read_csv(csv_path)
    return normalize_dataframe(df)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names / types used across the dashboard."""
    out = df.copy()
    rename = {
        "date": "datetime",
        "local": "datetime",
        "utc": "datetime",
        "parameter": "parameter",
        "city": "city",
        "location": "location",
        "value": "value",
        "unit": "unit",
        "latitude": "latitude",
        "longitude": "longitude",
        "source": "source",
    }
    out.columns = [c.strip().lower() for c in out.columns]
    for old, new in rename.items():
        if old in out.columns and new not in out.columns:
            out = out.rename(columns={old: new})

    if "datetime" not in out.columns:
        raise ValueError("DataFrame must contain a datetime column")

    out["datetime"] = pd.to_datetime(out["datetime"], utc=True, errors="coerce")
    out = out.dropna(subset=["datetime", "value", "parameter"])
    out["parameter"] = (
        out["parameter"]
        .astype(str)
        .str.lower()
        .str.replace(".", "", regex=False)
        .map(lambda x: PARAM_ALIASES.get(x, x))
    )
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["value"])
    if "city" not in out.columns:
        out["city"] = "Unknown"
    if "location" not in out.columns:
        out["location"] = out["city"]
    if "source" not in out.columns:
        out["source"] = "unknown"
    if "unit" not in out.columns:
        out["unit"] = ""
    for col in ("latitude", "longitude"):
        if col not in out.columns:
            out[col] = pd.NA
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    cols = [
        "datetime",
        "city",
        "location",
        "latitude",
        "longitude",
        "parameter",
        "value",
        "unit",
        "source",
    ]
    return out[cols].sort_values("datetime").reset_index(drop=True)


def _fetch_locations_india(cities: list[str], limit: int = 100) -> list[dict]:
    """Fetch OpenAQ v3 locations in India, optionally filtered by city name."""
    locations: list[dict] = []
    for city in cities:
        params = {
            "countries_id": 9,  # India (OpenAQ country id; may vary — also try iso)
            "iso": "IN",
            "limit": limit,
            "page": 1,
            "name": city,
        }
        # Prefer iso filter; drop countries_id if both used
        try_params = [
            {"iso": "IN", "limit": limit, "page": 1, "name": city},
            {"countries_id": 9, "limit": limit, "page": 1, "name": city},
            {"iso": "IN", "limit": limit, "page": 1},
        ]
        found = False
        for p in try_params:
            try:
                r = requests.get(
                    f"{OPENAQ_BASE}/locations",
                    headers=_headers(),
                    params=p,
                    timeout=25,
                )
                if r.status_code == 401:
                    raise PermissionError(
                        "OpenAQ API key required (set OPENAQ_API_KEY). "
                        "Get a free key at https://explore.openaq.org/"
                    )
                if r.status_code != 200:
                    continue
                data = r.json().get("results", [])
                if not data:
                    continue
                for loc in data:
                    loc_name = (loc.get("name") or "").lower()
                    locality = ""
                    if isinstance(loc.get("locality"), str):
                        locality = loc["locality"].lower()
                    elif isinstance(loc.get("locality"), dict):
                        locality = str(loc["locality"].get("name", "")).lower()
                    city_l = city.lower()
                    if city_l in loc_name or city_l in locality or "name" not in p:
                        enriched = dict(loc)
                        enriched["_city"] = city
                        locations.append(enriched)
                        found = True
                if found and "name" in p:
                    break
            except PermissionError:
                raise
            except requests.RequestException:
                continue
        if found:
            continue
    # Deduplicate by id
    seen = set()
    unique = []
    for loc in locations:
        lid = loc.get("id")
        if lid in seen:
            continue
        seen.add(lid)
        unique.append(loc)
    return unique


def _parse_latest_rows(location: dict, latest_payload: dict) -> list[dict]:
    rows = []
    city = location.get("_city") or location.get("locality") or "India"
    if isinstance(city, dict):
        city = city.get("name", "India")
    loc_name = location.get("name", "Unknown")
    coords = location.get("coordinates") or {}
    lat = coords.get("latitude")
    lon = coords.get("longitude")
    for item in latest_payload.get("results", []):
        param_obj = item.get("parameter") or {}
        pname = (param_obj.get("name") or param_obj.get("displayName") or "").lower()
        pname = PARAM_ALIASES.get(pname.replace(".", ""), pname.replace(".", ""))
        if pname not in PARAM_LABELS:
            continue
        value = item.get("value")
        if value is None:
            continue
        dt = None
        for key in ("datetime", "date"):
            blob = item.get(key)
            if isinstance(blob, dict):
                dt = blob.get("utc") or blob.get("local")
            elif isinstance(blob, str):
                dt = blob
            if dt:
                break
        rows.append(
            {
                "datetime": dt,
                "city": city,
                "location": loc_name,
                "latitude": lat,
                "longitude": lon,
                "parameter": pname,
                "value": value,
                "unit": (param_obj.get("units") or param_obj.get("unit") or ""),
                "source": "openaq",
            }
        )
    return rows


def fetch_openaq_latest(cities: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Fetch latest measurements for major Indian cities via OpenAQ API v3.

    Requires OPENAQ_API_KEY in the environment (v3). Raises on auth/network
    failure so callers can fall back to sample data.
    """
    if get_api_key() is None:
        raise PermissionError(
            "OPENAQ_API_KEY not set. OpenAQ v3 requires an API key "
            "(https://explore.openaq.org/). Falling back to sample data."
        )

    cities = cities or DEFAULT_CITIES
    locations = _fetch_locations_india(cities)
    if not locations:
        raise RuntimeError("No OpenAQ locations found for requested Indian cities.")

    all_rows: list[dict] = []
    # Cap API calls for responsiveness
    for loc in locations[:24]:
        lid = loc.get("id")
        if lid is None:
            continue
        try:
            r = requests.get(
                f"{OPENAQ_BASE}/locations/{lid}/latest",
                headers=_headers(),
                params={"limit": 100},
                timeout=20,
            )
            if r.status_code == 401:
                raise PermissionError("Invalid or missing OPENAQ_API_KEY.")
            if r.status_code != 200:
                continue
            all_rows.extend(_parse_latest_rows(loc, r.json()))
        except PermissionError:
            raise
        except requests.RequestException:
            continue

    if not all_rows:
        raise RuntimeError("OpenAQ returned no usable measurements.")

    return normalize_dataframe(pd.DataFrame(all_rows))


def load_aqi_data(
    prefer_live: bool = True,
    cities: Optional[list[str]] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Load AQI data. Tries OpenAQ when prefer_live=True and a key is present;
    always falls back to sample CSV so the dashboard works offline.

    Returns (dataframe, source_label).
    """
    if prefer_live and get_api_key():
        try:
            df = fetch_openaq_latest(cities=cities)
            if not df.empty:
                return df, "OpenAQ API v3 (latest)"
        except Exception as exc:  # noqa: BLE001 — intentional soft-fail to sample
            sample = load_sample_data()
            return sample, f"Sample CSV (OpenAQ unavailable: {exc})"

    sample = load_sample_data()
    if prefer_live and not get_api_key():
        return sample, "Sample CSV (set OPENAQ_API_KEY for live OpenAQ v3 data)"
    return sample, "Sample CSV"


def filter_data(
    df: pd.DataFrame,
    cities: Optional[list[str]] = None,
    parameters: Optional[list[str]] = None,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Apply city / pollutant / time-range filters."""
    out = df
    if cities:
        out = out[out["city"].isin(cities)]
    if parameters:
        params = [p.lower().replace(".", "") for p in parameters]
        params = [PARAM_ALIASES.get(p, p) for p in params]
        out = out[out["parameter"].isin(params)]
    if start is not None:
        start = pd.to_datetime(start, utc=True)
        out = out[out["datetime"] >= start]
    if end is not None:
        end = pd.to_datetime(end, utc=True)
        out = out[out["datetime"] <= end]
    return out.copy()


def estimate_aqi_from_pm25(pm25: float) -> float:
    """Linear interpolate India-style AQI from PM2.5 concentration."""
    if pd.isna(pm25) or pm25 < 0:
        return float("nan")
    for c_lo, c_hi, i_lo, i_hi in PM25_BREAKPOINTS:
        if pm25 <= c_hi:
            return round(
                ((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo,
                1,
            )
    return 500.0


def aqi_category(aqi: float) -> str:
    if pd.isna(aqi):
        return "Unknown"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Satisfactory"
    if aqi <= 200:
        return "Moderate"
    if aqi <= 300:
        return "Poor"
    if aqi <= 400:
        return "Very Poor"
    return "Severe"


def compute_kpis(df: pd.DataFrame) -> dict:
    """Storytelling KPIs from filtered measurements."""
    empty = {
        "n_rows": 0,
        "n_cities": 0,
        "worst_city": "—",
        "worst_pm25": None,
        "best_city": "—",
        "best_pm25": None,
        "avg_pm25": None,
        "avg_aqi": None,
        "aqi_category": "Unknown",
        "dominant_pollutant": "—",
        "trend_pct": None,
        "date_min": None,
        "date_max": None,
    }
    if df.empty:
        return empty

    pm = df[df["parameter"] == "pm25"]
    city_pm = (
        pm.groupby("city")["value"].mean().sort_values(ascending=False)
        if not pm.empty
        else pd.Series(dtype=float)
    )
    worst_city = city_pm.index[0] if len(city_pm) else "—"
    best_city = city_pm.index[-1] if len(city_pm) else "—"
    avg_pm25 = float(pm["value"].mean()) if not pm.empty else None
    avg_aqi = estimate_aqi_from_pm25(avg_pm25) if avg_pm25 is not None else None

    # Dominant pollutant by mean relative to sample means (simple ranking by z-ish)
    param_means = df.groupby("parameter")["value"].mean()
    dominant = param_means.idxmax() if len(param_means) else "—"

    # Trend: last 7d vs previous 7d mean for PM2.5
    trend_pct = None
    if not pm.empty:
        pm_ts = pm.set_index("datetime").sort_index()
        end = pm_ts.index.max()
        recent = pm_ts.loc[end - pd.Timedelta(days=7) : end, "value"].mean()
        prior = pm_ts.loc[
            end - pd.Timedelta(days=14) : end - pd.Timedelta(days=7), "value"
        ].mean()
        if pd.notna(recent) and pd.notna(prior) and prior != 0:
            trend_pct = round(100.0 * (recent - prior) / prior, 1)

    return {
        "n_rows": int(len(df)),
        "n_cities": int(df["city"].nunique()),
        "worst_city": worst_city,
        "worst_pm25": float(city_pm.iloc[0]) if len(city_pm) else None,
        "best_city": best_city,
        "best_pm25": float(city_pm.iloc[-1]) if len(city_pm) else None,
        "avg_pm25": avg_pm25,
        "avg_aqi": avg_aqi,
        "aqi_category": aqi_category(avg_aqi) if avg_aqi is not None else "Unknown",
        "dominant_pollutant": PARAM_LABELS.get(str(dominant), str(dominant)),
        "trend_pct": trend_pct,
        "date_min": df["datetime"].min(),
        "date_max": df["datetime"].max(),
    }


def city_comparison(df: pd.DataFrame, parameter: str = "pm25") -> pd.DataFrame:
    """Mean / max / min by city for one pollutant."""
    subset = df[df["parameter"] == parameter]
    if subset.empty:
        return pd.DataFrame(columns=["city", "mean", "max", "min", "count"])
    g = (
        subset.groupby("city")["value"]
        .agg(mean="mean", max="max", min="min", count="count")
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    return g


def daily_timeseries(df: pd.DataFrame, parameter: str = "pm25") -> pd.DataFrame:
    """Daily mean by city for plotting."""
    subset = df[df["parameter"] == parameter].copy()
    if subset.empty:
        return pd.DataFrame(columns=["date", "city", "value"])
    subset["date"] = subset["datetime"].dt.floor("D")
    return (
        subset.groupby(["date", "city"], as_index=False)["value"]
        .mean()
        .sort_values("date")
    )
