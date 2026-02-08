# tests/test_engine.py
import io
from PIL import Image
from squishfile.compressor.engine import compress_file


def _make_test_jpeg() -> bytes:
    img = Image.new("RGB", (800, 600))
    pixels = img.load()
    for y in range(600):
        for x in range(800):
            pixels[x, y] = ((x * 7) % 256, (y * 3) % 256, 128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf.read()


def test_compress_file_jpeg():
    data = _make_test_jpeg()
    target = len(data) // 3
    result = compress_file(
        data=data,
        mime="image/jpeg",
        category="image",
        target_size=target,
        width=800,
        height=600,
    )
    assert result["size"] <= target * 1.05
    assert result["skipped"] is False


def test_compress_file_skip_small():
    data = b"\xff\xd8" + b"\x00" * 100  # tiny fake
    result = compress_file(
        data=data,
        mime="image/jpeg",
        category="image",
        target_size=10000,
    )
    assert result["skipped"] is True


def test_compress_file_unsupported_returns_skipped():
    result = compress_file(
        data=b"random data",
        mime="application/octet-stream",
        category="unsupported",
        target_size=1000,
    )
    assert result["skipped"] is True


def test_compress_file_video_dispatch():
    """Engine should accept category='video' without error."""
    tiny_data = b"\x00" * 100
    result = compress_file(
        data=tiny_data,
        mime="video/mp4",
        category="video",
        target_size=10000,
    )
    # Small data should be skipped (under target)
    assert result["skipped"] is True


def test_compress_file_audio_dispatch():
    """Engine should accept category='audio' without error."""
    tiny_data = b"\x00" * 100
    result = compress_file(
        data=tiny_data,
        mime="audio/mpeg",
        category="audio",
        target_size=10000,
    )
    assert result["skipped"] is True
