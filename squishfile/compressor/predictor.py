# squishfile/compressor/predictor.py
import os
import joblib
import numpy as np

_model = None
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "quality_model.pkl")


def _load_model():
    global _model
    if _model is None:
        if os.path.exists(_MODEL_PATH):
            _model = joblib.load(_MODEL_PATH)
    return _model


def predict_quality(
    file_type: str,
    original_size: int,
    target_size: int,
    width: int = 1920,
    height: int = 1080,
) -> int:
    model = _load_model()

    pixel_count = width * height
    size_ratio = target_size / original_size if original_size > 0 else 1.0

    if model is not None:
        features = np.array([[original_size, target_size, pixel_count, size_ratio]])
        quality = int(model.predict(features)[0])
    else:
        # Fallback heuristic if model not found
        quality = int(size_ratio * 85)

    return max(5, min(95, quality))
