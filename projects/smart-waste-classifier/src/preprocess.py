"""OpenCV-based image preprocessing for waste classification."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

import cv2
import numpy as np
import torch
from torchvision import transforms

# ImageNet normalization (MobileNetV2 pretrained on ImageNet)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
DEFAULT_SIZE = 224


def load_image(path: Union[str, Path]) -> np.ndarray:
    """Load an image from disk as BGR uint8 (OpenCV convention)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to decode image: {path}")
    return img


def resize_letterbox(bgr: np.ndarray, size: int = DEFAULT_SIZE) -> np.ndarray:
    """Resize keeping aspect ratio, pad to square with gray borders."""
    h, w = bgr.shape[:2]
    scale = size / max(h, w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    return canvas


def denoise_and_enhance(bgr: np.ndarray) -> np.ndarray:
    """Light denoise + CLAHE on L-channel for more stable colors."""
    denoised = cv2.bilateralFilter(bgr, d=5, sigmaColor=50, sigmaSpace=50)
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def preprocess_bgr(
    bgr: np.ndarray,
    size: int = DEFAULT_SIZE,
    enhance: bool = True,
) -> np.ndarray:
    """
    Full OpenCV pipeline: enhance → letterbox resize → RGB uint8 [H,W,3].

    Returns RGB image ready for PIL/torchvision transforms or display.
    """
    if bgr is None or bgr.size == 0:
        raise ValueError("Empty image")
    if enhance:
        bgr = denoise_and_enhance(bgr)
    square = resize_letterbox(bgr, size=size)
    rgb = cv2.cvtColor(square, cv2.COLOR_BGR2RGB)
    return rgb


def get_eval_transform(size: int = DEFAULT_SIZE) -> transforms.Compose:
    """Torchvision eval transform matching MobileNetV2 ImageNet prep."""
    return transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((size, size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def get_train_transform(size: int = DEFAULT_SIZE) -> transforms.Compose:
    """Training augmentations for real / synthetic datasets."""
    return transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.RandomResizedCrop(size, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def preprocess_for_model(
    bgr_or_rgb: np.ndarray,
    size: int = DEFAULT_SIZE,
    is_bgr: bool = True,
    enhance: bool = True,
) -> torch.Tensor:
    """
    Convert OpenCV image → model-ready tensor [1, 3, H, W].

    If ``is_bgr`` is True (default), runs the OpenCV pipeline first.
    """
    if is_bgr:
        rgb = preprocess_bgr(bgr_or_rgb, size=size, enhance=enhance)
    else:
        rgb = bgr_or_rgb
        if rgb.shape[0] != size or rgb.shape[1] != size:
            rgb = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA)
    tensor = get_eval_transform(size)(rgb)
    return tensor.unsqueeze(0)


def bytes_to_bgr(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded file bytes (Streamlit) to BGR ndarray."""
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode uploaded image")
    return img
