import io
from PIL import Image
from squishfile.compressor.image import compress_image


def _make_test_jpeg(width=800, height=600) -> bytes:
    """Create a test JPEG with varied pixel data for realistic compression."""
    import random
    random.seed(42)
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (
                (x * 7 + y * 3) % 256,
                (x * 3 + y * 7) % 256,
                (x * 5 + y * 5) % 256,
            )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf.read()


def test_compress_jpeg_to_target():
    original = _make_test_jpeg()
    target_size = len(original) // 4  # 25% of original
    result = compress_image(original, "image/jpeg", target_size)
    assert len(result["data"]) <= target_size * 1.05  # within 5% tolerance
    assert result["data"][:2] == b"\xff\xd8"  # still valid JPEG


def test_skip_if_already_small():
    original = _make_test_jpeg(50, 50)
    target_size = len(original) * 2  # target bigger than original
    result = compress_image(original, "image/jpeg", target_size)
    assert result["skipped"] is True
