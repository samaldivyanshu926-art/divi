#!/usr/bin/env python3
"""
Bootstrap demo trainer: synthetic colored / textured patches labeled by class.

Trains MobileNetV2 classifier head for a few epochs and saves
models/waste_mobilenetv2.pt so Streamlit works without a real dataset.

Usage:
    python train_demo.py
    python train_demo.py --epochs 3 --samples-per-class 64
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.model import CLASS_NAMES, NUM_CLASSES, build_model, save_checkpoint
from src.preprocess import get_eval_transform, get_train_transform

# Distinct base colors (BGR) so the tiny demo is linearly separable-ish
CLASS_COLORS_BGR = {
    "plastic": (255, 180, 50),    # cyan-ish / light blue plastic vibe
    "paper": (220, 220, 240),     # near-white paper
    "metal": (160, 160, 170),     # gray metal
    "glass": (180, 220, 120),     # green glass tint
    "cardboard": (40, 120, 180),  # brown cardboard
    "organic": (40, 160, 60),     # green/brown organic
}


def make_synthetic_image(class_name: str, size: int = 224, seed: int | None = None) -> np.ndarray:
    """Generate a noisy colored square with optional shapes (OpenCV BGR)."""
    rng = np.random.default_rng(seed)
    base = np.array(CLASS_COLORS_BGR[class_name], dtype=np.float32)
    noise = rng.normal(0, 18, (size, size, 3)).astype(np.float32)
    img = np.clip(base + noise, 0, 255).astype(np.uint8)

    # Add a few random rectangles / circles for texture diversity
    for _ in range(int(rng.integers(2, 6))):
        color = tuple(int(c) for c in np.clip(base + rng.integers(-40, 40, 3), 0, 255))
        if rng.random() < 0.5:
            x1, y1 = int(rng.integers(0, size // 2)), int(rng.integers(0, size // 2))
            x2, y2 = int(rng.integers(x1 + 10, size)), int(rng.integers(y1 + 10, size))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness=-1)
        else:
            cx, cy = int(rng.integers(20, size - 20)), int(rng.integers(20, size - 20))
            r = int(rng.integers(10, size // 5))
            cv2.circle(img, (cx, cy), r, color, thickness=-1)

    # Mild blur sometimes
    if rng.random() < 0.3:
        img = cv2.GaussianBlur(img, (5, 5), 0)
    return img


class SyntheticWasteDataset(Dataset):
    def __init__(self, samples_per_class: int, train: bool = True, size: int = 224):
        self.size = size
        self.transform = get_train_transform(size) if train else get_eval_transform(size)
        self.items: list[tuple[str, int, int]] = []
        for idx, name in enumerate(CLASS_NAMES):
            for i in range(samples_per_class):
                # unique seed per sample for reproducibility
                self.items.append((name, idx, idx * 10000 + i + (0 if train else 50000)))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int):
        name, label, seed = self.items[i]
        bgr = make_synthetic_image(name, size=self.size, seed=seed)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        tensor = self.transform(rgb)
        return tensor, label


def train_one_epoch(model, loader, criterion, optimizer, device) -> float:
    model.train()
    total_loss, correct, n = 0.0, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * x.size(0)
        correct += (logits.argmax(1) == y).sum().item()
        n += x.size(0)
    return total_loss / n, correct / n


@torch.inference_mode()
def evaluate(model, loader, criterion, device) -> tuple[float, float]:
    model.eval()
    total_loss, correct, n = 0.0, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        loss = criterion(logits, y)
        total_loss += loss.item() * x.size(0)
        correct += (logits.argmax(1) == y).sum().item()
        n += x.size(0)
    return total_loss / n, correct / n


def export_sample_images(out_dir: Path, per_class: int = 2) -> None:
    """Write a few synthetic PNGs into sample_images/ for the Streamlit demo."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in CLASS_NAMES:
        for i in range(per_class):
            img = make_synthetic_image(name, seed=hash(name) % 10000 + i)
            cv2.imwrite(str(out_dir / f"{name}_{i+1}.png"), img)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train demo waste classifier on synthetic data")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--samples-per-class", type=int, default=80)
    parser.add_argument("--val-per-class", type=int, default=20)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "models" / "waste_mobilenetv2.pt"),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-pretrained", action="store_true", help="Skip ImageNet weights (faster offline)")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Classes ({NUM_CLASSES}): {CLASS_NAMES}")

    train_ds = SyntheticWasteDataset(args.samples_per_class, train=True)
    val_ds = SyntheticWasteDataset(args.val_per_class, train=False)
    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers
    )

    # Prefer ImageNet backbone; fall back if download fails (air-gapped / rate-limit)
    try:
        model = build_model(
            num_classes=NUM_CLASSES,
            pretrained=not args.no_pretrained,
            freeze_backbone=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: pretrained download failed ({exc}); training from scratch.")
        model = build_model(num_classes=NUM_CLASSES, pretrained=False, freeze_backbone=False)

    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
    )

    best_acc = 0.0
    out_path = Path(args.output)
    for epoch in range(1, args.epochs + 1):
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        va_loss, va_acc = evaluate(model, val_loader, criterion, device)
        print(
            f"Epoch {epoch}/{args.epochs}  "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc:.3f}  "
            f"val_loss={va_loss:.4f} val_acc={va_acc:.3f}"
        )
        if va_acc >= best_acc:
            best_acc = va_acc
            save_checkpoint(
                model,
                out_path,
                class_names=CLASS_NAMES,
                extra={"demo": True, "val_acc": best_acc, "epoch": epoch},
            )
            print(f"  → saved best checkpoint to {out_path} (val_acc={best_acc:.3f})")

    export_sample_images(ROOT / "sample_images", per_class=2)
    print(f"\nDone. Demo weights: {out_path}")
    print(f"Sample images written to {ROOT / 'sample_images'}")
    print("Run:  streamlit run app.py")


if __name__ == "__main__":
    main()
