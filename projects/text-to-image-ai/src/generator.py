"""
Image generation via Stability AI REST API, Hugging Face Inference API,
or a local PIL mock when no API keys are configured.
"""

from __future__ import annotations

import base64
import io
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

STABILITY_API_HOST = "https://api.stability.ai"
STABILITY_ENGINE = "stable-diffusion-xl-1024-v1-0"
HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "stabilityai/stable-diffusion-xl-base-1.0"
)


class GenerationError(Exception):
    """Raised when an upstream API call fails in a recoverable way."""


def _load_env() -> None:
    """Load .env if python-dotenv is available (optional)."""
    try:
        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass


def get_api_status() -> dict[str, bool]:
    """Return which backends have credentials configured."""
    _load_env()
    return {
        "stability": bool(os.getenv("STABILITY_API_KEY", "").strip()),
        "huggingface": bool(os.getenv("HF_TOKEN", "").strip()),
        "mock_available": True,
    }


def available_backend() -> str:
    """
    Prefer Stability AI, then Hugging Face, else mock.
    Returns one of: 'stability' | 'huggingface' | 'mock'.
    """
    status = get_api_status()
    if status["stability"]:
        return "stability"
    if status["huggingface"]:
        return "huggingface"
    return "mock"


def _ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def _safe_filename(prompt: str, seed: Optional[int] = None) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
    seed_part = f"_s{seed}" if seed is not None else ""
    return f"img_{stamp}_{digest}{seed_part}.png"


def save_image(image: Image.Image, prompt: str, seed: Optional[int] = None) -> Path:
    """Save a PIL image under outputs/ and return its path."""
    out_dir = _ensure_outputs_dir()
    path = out_dir / _safe_filename(prompt, seed)
    image.save(path, format="PNG")
    return path


def list_gallery(limit: int = 24) -> list[Path]:
    """Newest-first list of generated PNGs in outputs/."""
    out_dir = _ensure_outputs_dir()
    files = sorted(out_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def generate_mock_image(
    prompt: str,
    width: int = 768,
    height: int = 768,
    seed: Optional[int] = None,
) -> Image.Image:
    """
    Draw a simple placeholder so the UI is demoable without API keys.
    Color scheme is derived from the prompt (+ optional seed) for variety.
    """
    material = f"{prompt}|{seed if seed is not None else ''}"
    digest = hashlib.md5(material.encode("utf-8")).hexdigest()
    r = int(digest[0:2], 16)
    g = int(digest[2:4], 16)
    b = int(digest[4:6], 16)
    # Keep backgrounds readable (muted)
    bg = ((r % 120) + 40, (g % 120) + 40, (b % 120) + 40)
    accent = ((r + 80) % 200 + 55, (g + 40) % 200 + 55, (b + 20) % 200 + 55)

    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    # Decorative frame
    margin = 24
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=accent,
        width=4,
    )
    draw.rectangle(
        [margin + 12, margin + 12, width - margin - 12, height - margin - 12],
        outline=(255, 255, 255, 180),
        width=1,
    )

    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
        font_body = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
        )
    except OSError:
        font_title = ImageFont.load_default()
        font_body = font_title
        font_small = font_title

    draw.text((margin + 28, margin + 36), "MOCK MODE", fill=accent, font=font_title)
    draw.text(
        (margin + 28, margin + 76),
        "No API key — placeholder image",
        fill=(230, 230, 230),
        font=font_small,
    )

    # Word-wrap prompt into the canvas
    max_chars = max(28, (width - 2 * margin - 56) // 10)
    words = (prompt or "(empty prompt)").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:12]

    y = margin + 120
    for line in lines:
        draw.text((margin + 28, y), line, fill=(255, 255, 255), font=font_body)
        y += 28

    if seed is not None:
        draw.text(
            (margin + 28, height - margin - 40),
            f"seed: {seed}",
            fill=(200, 200, 200),
            font=font_small,
        )

    return img


def _generate_stability(
    prompt: str,
    negative_prompt: str,
    guidance_scale: float,
    steps: int,
    seed: Optional[int],
    width: int,
    height: int,
) -> Image.Image:
    _load_env()
    api_key = os.getenv("STABILITY_API_KEY", "").strip()
    if not api_key:
        raise GenerationError("STABILITY_API_KEY is not set.")

    # SDXL engines typically require multiples of 64; clamp common sizes
    width = max(512, min(width, 1536))
    height = max(512, min(height, 1536))
    width -= width % 64
    height -= height % 64

    url = f"{STABILITY_API_HOST}/v1/generation/{STABILITY_ENGINE}/text-to-image"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    text_prompts: list[dict[str, Any]] = [{"text": prompt, "weight": 1.0}]
    if negative_prompt.strip():
        text_prompts.append({"text": negative_prompt, "weight": -1.0})

    body: dict[str, Any] = {
        "text_prompts": text_prompts,
        "cfg_scale": float(guidance_scale),
        "steps": int(steps),
        "width": width,
        "height": height,
        "samples": 1,
    }
    if seed is not None and seed >= 0:
        body["seed"] = int(seed)

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=120)
    except requests.RequestException as exc:
        raise GenerationError(f"Stability AI request failed: {exc}") from exc

    if resp.status_code != 200:
        detail = resp.text[:500]
        raise GenerationError(
            f"Stability AI error HTTP {resp.status_code}: {detail}"
        )

    data = resp.json()
    artifacts = data.get("artifacts") or []
    if not artifacts:
        raise GenerationError("Stability AI returned no image artifacts.")

    b64 = artifacts[0].get("base64")
    if not b64:
        raise GenerationError("Stability AI artifact missing base64 payload.")

    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


def _generate_huggingface(
    prompt: str,
    negative_prompt: str,
    guidance_scale: float,
    steps: int,
    seed: Optional[int],
    width: int,
    height: int,
) -> Image.Image:
    _load_env()
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise GenerationError("HF_TOKEN is not set.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "image/png",
    }
    parameters: dict[str, Any] = {
        "guidance_scale": float(guidance_scale),
        "num_inference_steps": int(steps),
        "width": int(width),
        "height": int(height),
    }
    if seed is not None and seed >= 0:
        parameters["seed"] = int(seed)
    if negative_prompt.strip():
        parameters["negative_prompt"] = negative_prompt

    payload = {"inputs": prompt, "parameters": parameters}

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=180)
    except requests.RequestException as exc:
        raise GenerationError(f"Hugging Face request failed: {exc}") from exc

    content_type = resp.headers.get("content-type", "")
    if resp.status_code != 200:
        detail = resp.text[:500]
        raise GenerationError(
            f"Hugging Face error HTTP {resp.status_code}: {detail}"
        )

    if "application/json" in content_type:
        # Model loading / error JSON
        raise GenerationError(f"Hugging Face response: {resp.text[:500]}")

    return Image.open(io.BytesIO(resp.content)).convert("RGB")


def generate_image(
    prompt: str,
    *,
    negative_prompt: str = "",
    guidance_scale: float = 7.5,
    steps: int = 30,
    seed: Optional[int] = None,
    width: int = 768,
    height: int = 768,
    backend: Optional[str] = None,
    save: bool = True,
) -> tuple[Image.Image, Path | None, str]:
    """
    Generate an image and optionally save it to outputs/.

    Returns (image, saved_path_or_None, backend_used).
    """
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt must be a non-empty string.")

    prompt = str(prompt).strip()
    negative_prompt = str(negative_prompt or "")
    backend = (backend or available_backend()).lower()

    if backend == "stability":
        image = _generate_stability(
            prompt, negative_prompt, guidance_scale, steps, seed, width, height
        )
    elif backend in ("huggingface", "hf"):
        image = _generate_huggingface(
            prompt, negative_prompt, guidance_scale, steps, seed, width, height
        )
        backend = "huggingface"
    elif backend == "mock":
        image = generate_mock_image(prompt, width=width, height=height, seed=seed)
    else:
        raise ValueError(f"Unknown backend: {backend}")

    path: Path | None = None
    if save:
        path = save_image(image, prompt, seed)

    return image, path, backend
