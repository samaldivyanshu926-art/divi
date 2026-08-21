"""
Text-to-Image AI — Streamlit portfolio demo for Divyanshu Samal.

Stable Diffusion via Stability AI REST API, with Hugging Face Inference
API as fallback, plus a PIL mock mode when no keys are configured.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from PIL import Image

from src.generator import (
    GenerationError,
    available_backend,
    generate_image,
    get_api_status,
    list_gallery,
)

PAGE_TITLE = "Text-to-Image AI"
PAGE_ICON = "🎨"

PROMPT_TIPS = """
### Prompt engineering tips

1. **Be specific** — subject, setting, lighting, mood, camera angle.
2. **Add style cues** — e.g. `oil painting`, `cinematic`, `isometric 3D`, `watercolor`.
3. **Quality boosters** — `highly detailed`, `sharp focus`, `8k`, `masterpiece`.
4. **Use negative prompts** — exclude blur, watermark, extra limbs, text overlays.
5. **Iterate** — change one knob at a time (guidance, steps, or seed).
6. **Seeds** — reuse a seed to refine composition while editing the prompt.
7. **Guidance scale** — lower ≈ more creative / freer; higher ≈ closer to the prompt.
8. **Steps** — more steps often = cleaner detail (slower / costlier on APIs).

**Example prompt**
```
A serene mountain lake at dawn, mist over water,
pine forest reflection, soft golden light,
cinematic wide shot, highly detailed
```

**Example negative prompt**
```
blurry, low quality, watermark, text, deformed, oversaturated
```
"""


def _init_page() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.caption(
        "Stable Diffusion text-to-image · portfolio project by **Divyanshu Samal**"
    )


def _render_setup_banner(status: dict[str, bool], backend: str) -> None:
    if backend == "mock":
        st.warning(
            "**No API keys detected** — running in **mock / placeholder mode**. "
            "Images are simple PIL drawings of your prompt so the UI stays demoable. "
            "Add keys in a local `.env` (see `.env.example`) to call real models."
        )
        with st.expander("How to enable real generation", expanded=False):
            st.markdown(
                """
1. Copy `.env.example` → `.env`
2. Set **one** of:
   - `STABILITY_API_KEY` — [Stability AI](https://platform.stability.ai/) (preferred)
   - `HF_TOKEN` — [Hugging Face](https://huggingface.co/settings/tokens) (fallback)
3. Restart the Streamlit app

Never commit `.env` or real secrets.
                """
            )
    else:
        label = "Stability AI" if backend == "stability" else "Hugging Face Inference"
        st.success(f"Backend ready: **{label}**")
        bits = []
        if status["stability"]:
            bits.append("Stability AI key set")
        if status["huggingface"]:
            bits.append("HF token set")
        st.caption(" · ".join(bits))


def _sidebar_controls() -> dict:
    st.sidebar.header("Parameters")
    status = get_api_status()
    auto = available_backend()

    backend_options = ["auto", "stability", "huggingface", "mock"]
    backend_choice = st.sidebar.selectbox(
        "Backend",
        backend_options,
        index=0,
        help="auto = Stability → Hugging Face → mock",
    )
    backend = auto if backend_choice == "auto" else backend_choice

    guidance = st.sidebar.slider(
        "Creativity / guidance scale (CFG)",
        min_value=1.0,
        max_value=20.0,
        value=7.5,
        step=0.5,
        help="Lower = freer / more creative; higher = stick closer to the prompt.",
    )
    steps = st.sidebar.slider(
        "Style strength / steps",
        min_value=10,
        max_value=50,
        value=30,
        step=1,
        help="Diffusion steps — more usually means finer detail (slower).",
    )

    col_w, col_h = st.sidebar.columns(2)
    with col_w:
        width = st.number_input("Width", min_value=512, max_value=1024, value=768, step=64)
    with col_h:
        height = st.number_input("Height", min_value=512, max_value=1024, value=768, step=64)

    use_seed = st.sidebar.checkbox("Use fixed seed", value=False)
    seed = None
    if use_seed:
        seed = int(
            st.sidebar.number_input(
                "Seed",
                min_value=0,
                max_value=2_147_483_647,
                value=42,
                step=1,
            )
        )

    st.sidebar.divider()
    st.sidebar.markdown(PROMPT_TIPS)

    return {
        "backend": backend,
        "guidance": float(guidance),
        "steps": int(steps),
        "width": int(width),
        "height": int(height),
        "seed": seed,
        "status": status,
    }


def _render_gallery() -> None:
    st.subheader("Gallery")
    files = list_gallery(limit=24)
    if not files:
        st.info("No images in `outputs/` yet — generate one above.")
        return

    cols = st.columns(4)
    for i, path in enumerate(files):
        with cols[i % 4]:
            try:
                img = Image.open(path)
                st.image(img, caption=path.name, use_container_width=True)
            except OSError:
                st.caption(f"Could not load {path.name}")


def main() -> None:
    _init_page()
    params = _sidebar_controls()
    _render_setup_banner(params["status"], params["backend"])

    st.subheader("Generate")
    prompt = st.text_area(
        "Prompt",
        height=100,
        placeholder="A cozy cabin in a snowy forest at night, warm window light, cinematic...",
    )
    negative = st.text_area(
        "Negative prompt (optional)",
        height=70,
        placeholder="blurry, low quality, watermark, text, deformed...",
    )

    generate = st.button("Generate image", type="primary", use_container_width=False)

    if generate:
        if not prompt.strip():
            st.error("Please enter a prompt.")
        else:
            with st.spinner(f"Generating via **{params['backend']}**..."):
                try:
                    image, path, used = generate_image(
                        prompt,
                        negative_prompt=negative,
                        guidance_scale=params["guidance"],
                        steps=params["steps"],
                        seed=params["seed"],
                        width=params["width"],
                        height=params["height"],
                        backend=params["backend"],
                        save=True,
                    )
                    st.success(
                        f"Done via **{used}**"
                        + (f" · saved `{path.name}`" if path else "")
                    )
                    st.image(image, caption=prompt[:120], use_container_width=True)
                    if path:
                        st.caption(f"Saved to `{path}`")
                except GenerationError as exc:
                    st.error(f"Generation failed: {exc}")
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:  # noqa: BLE001 — surface unexpected errors in UI
                    st.error(f"Unexpected error: {exc}")

    st.divider()
    _render_gallery()

    st.markdown("---")
    st.caption(
        "Local portfolio demo · keys stay in `.env` (never committed) · "
        f"outputs → `{Path('outputs').resolve()}`"
    )


if __name__ == "__main__":
    main()
