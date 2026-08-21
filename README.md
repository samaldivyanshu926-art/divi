# Divyanshu Samal — Portfolio Projects

Three CV projects from my Mechanical Engineering / AI portfolio, each as a runnable Streamlit app.

| Project | What it does | Run |
|---------|--------------|-----|
| [Smart Waste Classifier](projects/smart-waste-classifier/) | MobileNetV2 CNN + OpenCV → plastic / paper / metal / glass (+ cardboard, organic) | `streamlit run app.py` |
| [Text-to-Image AI](projects/text-to-image-ai/) | Stable Diffusion (Stability / Hugging Face) with parameter tuning | `streamlit run app.py` |
| [Air Quality Dashboard](projects/aqi-dashboard/) | Indian-city AQI explorer (OpenAQ + Plotly), offline sample included | `streamlit run app.py` |

## Quick start

```bash
cd projects/<project-name>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

See each project’s README for API keys, training, and data notes.

`JetX_Portfolio_Package.zip` on `main` is a separate earlier package (engine performance portfolio).
