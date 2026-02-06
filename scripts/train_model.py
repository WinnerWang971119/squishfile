"""
Generate training data and train quality prediction model.
Run once: python scripts/train_model.py
Outputs: squishfile/models/quality_model.pkl
"""
import io
import random
import numpy as np
from PIL import Image
from sklearn.linear_model import Ridge
import joblib
import os

random.seed(42)
np.random.seed(42)


def generate_training_data(n_samples=500):
    X = []
    y = []

    widths = [640, 800, 1024, 1280, 1920, 2560, 3840]
    heights = [480, 600, 768, 720, 1080, 1440, 2160]

    for i in range(n_samples):
        width = random.choice(widths)
        height = random.choice(heights)
        quality = random.randint(10, 95)

        # Use numpy for fast image generation instead of pixel-by-pixel
        seed_val = random.randint(0, 1000)
        rows = np.arange(height).reshape(-1, 1)
        cols = np.arange(width).reshape(1, -1)

        r = ((cols * 7 + rows * 3 + seed_val) % 256).astype(np.uint8)
        g = ((cols * 3 + rows * 7 + seed_val) % 256).astype(np.uint8)
        b = ((cols * 5 + rows * 5 + seed_val) % 256).astype(np.uint8)

        img_array = np.stack([r, g, b], axis=-1)
        img = Image.fromarray(img_array, "RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        result_size = buf.tell()

        # Also get original (q=95) size for ratio
        buf95 = io.BytesIO()
        img.save(buf95, format="JPEG", quality=95, optimize=True)
        original_size = buf95.tell()

        pixel_count = width * height
        size_ratio = result_size / original_size if original_size > 0 else 1.0

        X.append([
            original_size,
            result_size,  # this is the "target"
            pixel_count,
            size_ratio,
        ])
        y.append(quality)

        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{n_samples} samples...")

    return np.array(X), np.array(y)


def main():
    print("Generating training data...")
    X, y = generate_training_data(500)

    print(f"Training on {len(X)} samples...")
    model = Ridge(alpha=1.0)
    model.fit(X, y)

    score = model.score(X, y)
    print(f"R² score: {score:.4f}")

    os.makedirs("squishfile/models", exist_ok=True)
    joblib.dump(model, "squishfile/models/quality_model.pkl")
    print("Model saved to squishfile/models/quality_model.pkl")


if __name__ == "__main__":
    main()
