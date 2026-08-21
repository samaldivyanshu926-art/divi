#!/usr/bin/env python3
"""
Prepare data/ layout and optionally download / point to TrashNet-style datasets.

This script:
  1. Creates data/raw/{plastic,paper,metal,glass,cardboard,organic}
  2. Writes a DATASET.md with download instructions
  3. Optionally copies synthetic samples from sample_images into data/raw
     so `train.py` has a minimal real-folder smoke path
  4. Attempts to fetch TrashNet if network + git are available (best-effort)

TrashNet (garythung/trashnet) is a common public waste dataset.
Kaggle "Garbage Classification" is another option.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.model import CLASS_NAMES

DATASET_MD = """# Dataset setup

## Folder layout (required by `train.py`)

```
data/raw/
  plastic/
  paper/
  metal/
  glass/
  cardboard/   # optional
  organic/     # optional
```

Each subfolder should contain `.jpg` / `.png` images of that material.

## Recommended public datasets

1. **TrashNet** — https://github.com/garythung/trashnet  
   Classes overlap: cardboard, glass, metal, paper, plastic, trash.

2. **Kaggle Garbage Classification** — search “Garbage Classification” on Kaggle.  
   Often includes organic / biological classes useful for the `organic` label.

## Quick start without downloads

```bash
python train_demo.py          # synthetic demo weights + sample_images/
python download_sample_data.py --seed-from-samples
python train.py --data-dir data/raw --epochs 2   # tiny smoke on copies
```

## Mapping tips

| Dataset label | Our class   |
|---------------|-------------|
| plastic       | plastic     |
| paper         | paper       |
| metal         | metal       |
| glass         | glass       |
| cardboard     | cardboard   |
| organic / biological / food | organic |
| trash / other | skip or map carefully |
"""


def ensure_dirs(raw_root: Path) -> None:
    for name in CLASS_NAMES:
        (raw_root / name).mkdir(parents=True, exist_ok=True)


def seed_from_samples(raw_root: Path, sample_dir: Path) -> int:
    """Copy sample_images/{class}_*.png into data/raw/{class}/."""
    count = 0
    for name in CLASS_NAMES:
        for src in sample_dir.glob(f"{name}_*"):
            dst = raw_root / name / src.name
            shutil.copy2(src, dst)
            count += 1
    return count


def try_clone_trashnet(dest: Path) -> bool:
    """Best-effort clone of TrashNet repo (dataset may still need manual extract)."""
    if dest.exists():
        print(f"TrashNet path already exists: {dest}")
        return True
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/garythung/trashnet.git", str(dest)],
            check=True,
            timeout=120,
        )
        print(f"Cloned TrashNet metadata/repo to {dest}")
        print("Note: image archives may need separate download — see the repo README.")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Could not clone TrashNet ({exc}). Use manual download instructions in DATASET.md.")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare waste dataset folders / downloads")
    parser.add_argument("--data-dir", type=str, default=str(ROOT / "data" / "raw"))
    parser.add_argument("--seed-from-samples", action="store_true", help="Copy sample_images into data/raw")
    parser.add_argument("--clone-trashnet", action="store_true", help="Try git clone TrashNet")
    args = parser.parse_args()

    raw = Path(args.data_dir)
    ensure_dirs(raw)
    (ROOT / "data" / "DATASET.md").write_text(DATASET_MD)
    print(f"Created class folders under {raw}")
    print(f"Wrote {ROOT / 'data' / 'DATASET.md'}")

    if args.seed_from_samples:
        sample_dir = ROOT / "sample_images"
        if not any(sample_dir.glob("*")):
            print("sample_images/ empty — run train_demo.py first to generate samples.")
        else:
            n = seed_from_samples(raw, sample_dir)
            print(f"Copied {n} sample images into {raw}")

    if args.clone_trashnet:
        try_clone_trashnet(ROOT / "data" / "trashnet_repo")

    print("\nNext:")
    print("  python train_demo.py     # recommended for portfolio demo")
    print("  python train.py --data-dir data/raw")


if __name__ == "__main__":
    main()
