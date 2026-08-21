# Dataset setup

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
