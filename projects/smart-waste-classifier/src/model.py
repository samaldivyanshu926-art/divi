"""MobileNetV2 transfer-learning model for waste classification."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

import torch
import torch.nn as nn
from torchvision import models

# Portfolio-friendly class set (TrashNet-style + organic)
CLASS_NAMES: List[str] = [
    "plastic",
    "paper",
    "metal",
    "glass",
    "cardboard",
    "organic",
]
NUM_CLASSES = len(CLASS_NAMES)

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parents[1] / "models" / "waste_mobilenetv2.pt"


class WasteMobileNetV2(nn.Module):
    """MobileNetV2 backbone with a custom classification head."""

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        pretrained: bool = True,
        freeze_backbone: bool = True,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = models.mobilenet_v2(weights=weights)
        in_features = backbone.classifier[1].in_features
        backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )
        self.backbone = backbone
        if freeze_backbone:
            self.freeze_backbone()

    def freeze_backbone(self) -> None:
        for name, param in self.backbone.named_parameters():
            if "classifier" not in name:
                param.requires_grad = False

    def unfreeze_backbone(self) -> None:
        for param in self.backbone.parameters():
            param.requires_grad = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def build_model(
    num_classes: int = NUM_CLASSES,
    pretrained: bool = True,
    freeze_backbone: bool = True,
    dropout: float = 0.3,
) -> WasteMobileNetV2:
    """Factory for a MobileNetV2 waste classifier."""
    return WasteMobileNetV2(
        num_classes=num_classes,
        pretrained=pretrained,
        freeze_backbone=freeze_backbone,
        dropout=dropout,
    )


def load_model(
    weights_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
    num_classes: int = NUM_CLASSES,
) -> WasteMobileNetV2:
    """
    Load architecture + checkpoint for inference.

    Checkpoint may be a full ``state_dict`` or a dict with keys
    ``state_dict``, ``class_names``, ``num_classes``.
    """
    path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device)

    model = build_model(num_classes=num_classes, pretrained=False, freeze_backbone=False)
    if not path.exists():
        raise FileNotFoundError(
            f"Model weights not found at {path}. "
            "Run `python train_demo.py` first to create demo weights."
        )

    ckpt = torch.load(path, map_location=device, weights_only=False)
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        state = ckpt["state_dict"]
        if "num_classes" in ckpt and ckpt["num_classes"] != num_classes:
            model = build_model(
                num_classes=ckpt["num_classes"],
                pretrained=False,
                freeze_backbone=False,
            )
    else:
        state = ckpt
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


def save_checkpoint(
    model: nn.Module,
    path: Union[str, Path],
    class_names: Optional[List[str]] = None,
    extra: Optional[dict] = None,
) -> Path:
    """Save model state_dict plus metadata."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    names = class_names or CLASS_NAMES
    payload = {
        "state_dict": model.state_dict(),
        "class_names": names,
        "num_classes": len(names),
    }
    if extra:
        payload.update(extra)
    torch.save(payload, path)
    return path
