# Models

Expected checkpoint for the Streamlit app:

```
models/waste_mobilenetv2.pt
```

## Create demo weights (recommended)

```bash
source .venv/bin/activate
python train_demo.py
```

This fine-tunes a MobileNetV2 head on synthetic colored patches for a few epochs
and writes `waste_mobilenetv2.pt` plus sample images.

## Real-data fine-tuning

```bash
python download_sample_data.py
# place images into data/raw/<class>/
python train.py --data-dir data/raw --epochs 10
```

Checkpoint format: PyTorch dict with `state_dict`, `class_names`, `num_classes`.
