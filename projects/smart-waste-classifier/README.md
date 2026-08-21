# Smart Waste Classification System

Portfolio computer-vision project by **Divyanshu Samal**.

Upload a photo of waste → **predicted class**, **confidence**, **top-k probabilities**, and an optional **Grad-CAM-lite** heatmap. Built with **PyTorch MobileNetV2** transfer learning and **OpenCV** preprocessing.

Classes: `plastic`, `paper`, `metal`, `glass`, `cardboard`, `organic`.

> TensorFlow/Keras is the usual portfolio default; this repo uses **torchvision MobileNetV2** so it installs cleanly on Python 3.13 Linux boxes (TF wheels are often missing). The architecture, training loop, and Streamlit UX are the same idea.

## Project layout

```
smart-waste-classifier/
├── app.py                  # Streamlit UI
├── train.py                # Fine-tune on real TrashNet-style folders
├── train_demo.py           # Fast synthetic bootstrap (recommended first run)
├── download_sample_data.py # data/raw layout + optional TrashNet clone
├── requirements.txt
├── .env.example
├── src/
│   ├── preprocess.py       # OpenCV load / CLAHE / letterbox / tensors
│   ├── model.py            # MobileNetV2 + custom head
│   └── predict.py          # Inference helpers
├── models/                 # waste_mobilenetv2.pt (created by train_demo.py)
├── sample_images/          # demo PNGs (created by train_demo.py)
└── data/raw/<class>/       # real dataset root for train.py
```

## Setup

```bash
cd smart-waste-classifier
python3 -m venv .venv
source .venv/bin/activate

# CPU torch (Linux / no GPU)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

GPU: install the CUDA build of torch from pytorch.org, then `pip install -r requirements.txt`.

## Train (demo — works without a dataset)

Creates `models/waste_mobilenetv2.pt` in a few minutes:

```bash
python train_demo.py
# optional knobs
python train_demo.py --epochs 3 --samples-per-class 80
```

This paints noisy colored patches per class, trains the **classifier head** of ImageNet MobileNetV2, and writes sample images.

## Train on real images (TrashNet-style)

```bash
python download_sample_data.py
# put photos in data/raw/{plastic,paper,metal,glass,cardboard,organic}/

python train.py --data-dir data/raw --epochs 10 --unfreeze-epoch 5
```

See `data/DATASET.md` (written by the download script) for TrashNet / Kaggle pointers.

## Run the app

```bash
streamlit run app.py
```

Open the URL Streamlit prints (default http://localhost:8501). Upload an image or pick a sample from the sidebar.

## Inference from Python

```python
from src.predict import predict_image

result = predict_image("sample_images/plastic_1.png")
print(result["class"], result["confidence"], result["top_k"])
```

## Notes

- **Demo weights** are *not* a real-world waste model — they prove the pipeline. Fine-tune with `train.py` on TrashNet or your own photos for a CV-ready accuracy story.
- Checkpoint: PyTorch dict with `state_dict`, `class_names`, `num_classes`.
- Preprocessing: bilateral denoise + CLAHE + letterbox to 224×224 + ImageNet normalize.
- Grad-CAM-lite uses the last `Conv2d` feature map (no extra libraries).
