# Text-to-Image AI

Portfolio CV project by **Divyanshu Samal** — a Streamlit app that turns text prompts into images using **Stable Diffusion** via the **Stability AI REST API**, with the **Hugging Face Inference API** as a fallback. When no API keys are present, a **mock / placeholder mode** draws a simple PIL image so the UI stays demoable.

## Features

- Text-to-image generation (Stability AI → Hugging Face → mock)
- Streamlit UI: prompt, negative prompt, optional seed
- Parameter tuning: guidance / CFG scale, steps (style strength), width & height
- Gallery of recent images saved under `outputs/`
- Prompt engineering tips in the sidebar
- Clear setup messaging when keys are missing

## Project layout

```
text-to-image-ai/
├── app.py              # Streamlit UI
├── src/
│   ├── __init__.py
│   └── generator.py    # Stability / HF / mock backends
├── outputs/            # Generated PNGs (gitignored except .gitkeep)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

```bash
cd text-to-image-ai
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set STABILITY_API_KEY and/or HF_TOKEN
```

## Run

```bash
source .venv/bin/activate
streamlit run app.py
```

Without keys, the app runs in **mock mode** automatically.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `STABILITY_API_KEY` | Stability AI REST API (preferred) |
| `HF_TOKEN` | Hugging Face Inference API (fallback) |

Do **not** commit `.env` or any real secrets.

## Backend selection

1. If `STABILITY_API_KEY` is set → Stability AI SDXL text-to-image
2. Else if `HF_TOKEN` is set → HF Inference (`stabilityai/stable-diffusion-xl-base-1.0`)
3. Else → PIL mock placeholder with the prompt text rendered on a colored canvas

You can also force a backend from the sidebar.

## Notes

- API calls require network access and a valid key/token with quota.
- Mock mode never calls external APIs — useful for demos and CI smoke tests.
- Generated files land in `outputs/` and appear in the in-app gallery.
