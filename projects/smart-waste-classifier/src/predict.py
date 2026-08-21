"""Inference helpers: predict class, confidence, top-k probabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn.functional as F

from .model import CLASS_NAMES, load_model
from .preprocess import bytes_to_bgr, load_image, preprocess_for_model


@torch.inference_mode()
def predict_tensor(
    model: torch.nn.Module,
    tensor: torch.Tensor,
    class_names: Optional[List[str]] = None,
    top_k: int = 3,
) -> Dict:
    """Run softmax prediction on a preprocessed batch tensor [1,C,H,W]."""
    names = class_names or CLASS_NAMES
    device = next(model.parameters()).device
    tensor = tensor.to(device)
    logits = model(tensor)
    probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()
    k = min(top_k, len(names))
    top_idx = np.argsort(probs)[::-1][:k]
    top = [(names[i], float(probs[i])) for i in top_idx]
    pred_idx = int(top_idx[0])
    return {
        "class": names[pred_idx],
        "class_index": pred_idx,
        "confidence": float(probs[pred_idx]),
        "probabilities": {names[i]: float(probs[i]) for i in range(len(names))},
        "top_k": top,
    }


def predict_image(
    image: Union[str, Path, bytes, np.ndarray],
    model: Optional[torch.nn.Module] = None,
    weights_path: Optional[Union[str, Path]] = None,
    class_names: Optional[List[str]] = None,
    top_k: int = 3,
    enhance: bool = True,
) -> Dict:
    """
    End-to-end prediction from path, bytes, or BGR ndarray.

    Returns dict with class, confidence, full probabilities, and top_k list.
    """
    if model is None:
        model = load_model(weights_path=weights_path)

    if isinstance(image, (str, Path)):
        bgr = load_image(image)
    elif isinstance(image, bytes):
        bgr = bytes_to_bgr(image)
    elif isinstance(image, np.ndarray):
        bgr = image
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    tensor = preprocess_for_model(bgr, enhance=enhance)
    return predict_tensor(model, tensor, class_names=class_names, top_k=top_k)


def predict_topk(
    image: Union[str, Path, bytes, np.ndarray],
    k: int = 3,
    **kwargs,
) -> List[Tuple[str, float]]:
    """Convenience wrapper returning only top-k (name, prob) pairs."""
    result = predict_image(image, top_k=k, **kwargs)
    return result["top_k"]
