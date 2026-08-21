# India Air Quality (AQI) Dashboard

Interactive portfolio dashboard for **Divyanshu Samal** — explore AQI / pollutant trends across major Indian cities with Streamlit, Pandas, and Plotly.

## Features

- **Cities:** Delhi, Mumbai, Bengaluru, Kolkata, Chennai, Hyderabad, Pune, Ahmedabad (and any cities present in live OpenAQ responses)
- **Pollutants:** PM2.5, PM10, O₃, NO₂, CO, SO₂
- **Filters:** multi-city select, pollutant type, date range
- **KPIs & storytelling:** worst/best city, estimated AQI from PM2.5, 7-day trend, dominant pollutant
- **Charts:** time series, city comparison bars, box plots, heatmap, map of stations, AQI gauge
- **Offline-first:** bundled `data/sample_aqi_india.csv` so the app always runs without network or API keys

## OpenAQ API (v3)

Live mode uses **OpenAQ API v3** (`https://api.openaq.org/v3`).

| Item | Detail |
|------|--------|
| Auth | Header `X-API-Key: <key>` |
| Env var | `OPENAQ_API_KEY` |
| Free key | [https://explore.openaq.org/](https://explore.openaq.org/) |
| Endpoints used | `/v3/locations`, `/v3/locations/{id}/latest` |

If the key is missing/invalid or the API fails, the dashboard **automatically falls back** to the sample CSV.

```bash
cp .env.example .env
# edit .env and set OPENAQ_API_KEY=...
```

## Project layout

```
aqi-dashboard/
├── app.py                 # Streamlit UI
├── src/
│   ├── data.py            # OpenAQ fetch + sample fallback + KPIs
│   └── charts.py          # Plotly figures + insight copy
├── data/
│   └── sample_aqi_india.csv
├── requirements.txt
├── .env.example
└── README.md
```

## Setup & run

```bash
cd /workspace/cv-projects/aqi-dashboard   # or your local clone path
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

## Sample data

`data/sample_aqi_india.csv` contains realistic synthetic hourly-ish readings (~90 days ending 2026-08-20) for eight Indian cities and six pollutants, generated for demos and interviews so the portfolio works offline.

## Notes

- Estimated AQI uses a simplified India-style PM2.5 breakpoint interpolation for storytelling — not a regulatory CPCB calculation for all pollutants.
- Do not commit real API keys; keep them in `.env` (gitignored if you add one).
