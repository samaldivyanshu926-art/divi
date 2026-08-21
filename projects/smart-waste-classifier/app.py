#!/usr/bin/env python3
"""
Smart Waste Classification — Streamlit demo.

Upload an image → predicted class, confidence, top-k probabilities,
and optional Grad-CAM-lite heatmap overlay.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.model import CLASS_NAMES, DEFAULT_WEIGHTS_PATH, load_model
from src.predict import predict_image
from src.preprocess import bytes_to_bgr, preprocess_bgr, preprocess_for_model

st.set_page_config(
    page_title="Smart Waste Classifier",
    page_icon="♻️",
    layout="wide",
)

RECYCLE_TIPS = {
    "plastic": "Rinse containers; check local resin codes (1–7). Caps often go separately.",
    "paper": "Keep dry and clean; remove plastic windows when possible.",
    "metal": "Rinse cans; aluminum & steel are highly recyclable.",
    "glass": "Rinse bottles/jars; separate by color if your city requires it.",
    "cardboard": "Flatten boxes; remove tape/labels when easy.",
    "organic": "Compost food scraps / garden waste where available.",
}


def _find_last_conv(module: torch.nn.Module) -> torch.nn.Module:
    """Locate the last Conv2d for Grad-CAM-lite."""
    last = None
    for m in module.modules():
        if isinstance(m, torch.nn.Conv2d):
            last = m
    if last is None:
        raise RuntimeError("No Conv2d layer found for Grad-CAM")
    return last


def grad_cam_lite(
    model: torch.nn.Module,
    tensor: torch.Tensor,
    class_index: int | None = None,
) -> np.ndarray:
    """
    Lightweight Grad-CAM using the last convolutional feature map.

    Returns a float heatmap in [0, 1] shaped [H, W] matching feature map size.
    """
    model.eval()
    activations = {}
    gradients = {}

    target_layer = _find_last_conv(model)

    def fwd_hook(_mod, _inp, out):
        activations["value"] = out

    def bwd_hook(_mod, _gin, gout):
        gradients["value"] = gout[0]

    h1 = target_layer.register_forward_hook(fwd_hook)
    h2 = target_layer.register_full_backward_hook(bwd_hook)

    device = next(model.parameters()).device
    x = tensor.to(device).requires_grad_(True)
    model.zero_grad(set_to_none=True)
    logits = model(x)
    if class_index is None:
        class_index = int(logits.argmax(dim=1).item())
    score = logits[0, class_index]
    score.backward()

    h1.remove()
    h2.remove()

    acts = activations["value"].detach()  # [1, C, h, w]
    grads = gradients["value"].detach()
    weights = grads.mean(dim=(2, 3), keepdim=True)  # [1, C, 1, 1]
    cam = (weights * acts).sum(dim=1, keepdim=True)
    cam = F.relu(cam)
    cam = cam.squeeze().cpu().numpy()
    cam -= cam.min()
    if cam.max() > 0:
        cam /= cam.max()
    return cam


def overlay_heatmap(rgb: np.ndarray, heatmap: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    """Resize heatmap to image and blend with JET colormap."""
    h, w = rgb.shape[:2]
    heat = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
    heat_u8 = np.uint8(255 * heat)
    colored = cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    blend = (alpha * colored + (1 - alpha) * rgb).astype(np.uint8)
    return blend


@st.cache_resource
def get_model(weights_path: str):
    return load_model(weights_path=weights_path)


def main() -> None:
    st.title("♻️ Smart Waste Classification System")
    st.caption(
        "MobileNetV2 transfer learning · OpenCV preprocessing · "
        "Portfolio project by Divyanshu Samal"
    )

    with st.sidebar:
        st.header("Settings")
        weights = st.text_input("Weights path", value=str(DEFAULT_WEIGHTS_PATH))
        top_k = st.slider("Top-K", 1, len(CLASS_NAMES), 3)
        enhance = st.checkbox("OpenCV enhance (CLAHE + denoise)", value=True)
        show_cam = st.checkbox("Show Grad-CAM-lite heatmap", value=True)
        st.markdown("---")
        st.markdown("**Classes**")
        st.write(", ".join(CLASS_NAMES))
        st.markdown(
            "Train demo weights:\n```bash\npython train_demo.py\n```"
        )

    weights_path = Path(weights)
    if not weights_path.exists():
        st.error(
            f"Model not found at `{weights_path}`.\n\n"
            "Run this first:\n```bash\nsource .venv/bin/activate\n"
            "python train_demo.py\n```"
        )
        st.stop()

    try:
        model = get_model(str(weights_path))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load model: {exc}")
        st.stop()

    # Optional: show sample_images quick-pick
    sample_dir = ROOT / "sample_images"
    samples = sorted(sample_dir.glob("*.png")) + sorted(sample_dir.glob("*.jpg"))
    col_u, col_s = st.columns([2, 1])
    with col_u:
        uploaded = st.file_uploader("Upload a waste image", type=["jpg", "jpeg", "png", "webp", "bmp"])
    with col_s:
        sample_choice = None
        if samples:
            names = ["(none)"] + [p.name for p in samples]
            pick = st.selectbox("Or pick a sample", names)
            if pick != "(none)":
                sample_choice = sample_dir / pick

    bgr = None
    source_label = ""
    if uploaded is not None:
        bgr = bytes_to_bgr(uploaded.getvalue())
        source_label = uploaded.name
    elif sample_choice is not None:
        bgr = cv2.imread(str(sample_choice), cv2.IMREAD_COLOR)
        source_label = sample_choice.name

    if bgr is None:
        st.info("Upload an image or choose a sample to classify.")
        return

    rgb_preview = preprocess_bgr(bgr, enhance=enhance)
    result = predict_image(bgr, model=model, top_k=top_k, enhance=enhance)

    left, right = st.columns(2)
    with left:
        st.subheader("Input")
        st.image(rgb_preview, caption=source_label, use_container_width=True)

        if show_cam:
            try:
                tensor = preprocess_for_model(bgr, enhance=enhance)
                cam = grad_cam_lite(model, tensor, class_index=result["class_index"])
                overlay = overlay_heatmap(rgb_preview, cam)
                st.image(overlay, caption="Grad-CAM-lite overlay", use_container_width=True)
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Grad-CAM unavailable: {exc}")

    with right:
        st.subheader("Prediction")
        st.metric("Class", result["class"].title())
        st.metric("Confidence", f"{result['confidence'] * 100:.1f}%")
        st.progress(min(max(result["confidence"], 0.0), 1.0))

        tip = RECYCLE_TIPS.get(result["class"], "")
        if tip:
            st.info(f"**Recycling tip:** {tip}")

        st.markdown("#### Top-K probabilities")
        for name, prob in result["top_k"]:
            st.write(f"**{name}** — {prob * 100:.1f}%")
            st.progress(min(max(prob, 0.0), 1.0))

        st.markdown("#### All class scores")
        # Bar chart via Streamlit
        chart_data = {
            "class": list(result["probabilities"].keys()),
            "probability": list(result["probabilities"].values()),
        }
        import pandas as pd

        df = pd.DataFrame(chart_data).set_index("class").sort_values("probability", ascending=True)
        st.bar_chart(df)


if __name__ == "__main__":
    main()
