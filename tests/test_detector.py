import io
from PIL import Image
from squishfile.detector import detect_file_type


def _make_jpeg_bytes():
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def test_detect_jpeg():
    data = _make_jpeg_bytes()
    result = detect_file_type(data, "photo.jpg")
    assert result["mime"] == "image/jpeg"
    assert result["category"] == "image"
    assert result["extension"] == ".jpg"


def test_detect_unknown():
    result = detect_file_type(b"random bytes", "mystery.xyz")
    assert result["category"] == "unsupported"
