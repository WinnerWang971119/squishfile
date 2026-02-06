# tests/test_predictor.py
from squishfile.compressor.predictor import predict_quality


def test_predict_quality_jpeg():
    quality = predict_quality(
        file_type="image/jpeg",
        original_size=4_000_000,  # 4MB
        target_size=500_000,      # 500KB
        width=1920,
        height=1080,
    )
    assert 5 <= quality <= 95
    assert isinstance(quality, int)


def test_predict_smaller_target_gives_lower_quality():
    q_big = predict_quality("image/jpeg", 4_000_000, 1_000_000, 1920, 1080)
    q_small = predict_quality("image/jpeg", 4_000_000, 200_000, 1920, 1080)
    assert q_small < q_big
