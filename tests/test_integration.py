# tests/test_integration.py
import io
from PIL import Image
from fastapi.testclient import TestClient
from squishfile.main import app

client = TestClient(app)


def _make_large_jpeg() -> io.BytesIO:
    img = Image.new("RGB", (1920, 1080))
    pixels = img.load()
    for y in range(1080):
        for x in range(1920):
            pixels[x, y] = ((x * 7 + y) % 256, (y * 3 + x) % 256, 128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf


def test_full_pipeline():
    """Upload -> Compress -> Download end-to-end."""
    # 1. Upload
    buf = _make_large_jpeg()
    original_size = buf.getbuffer().nbytes
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("big_photo.jpg", buf, "image/jpeg")},
    )
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["id"]

    # 2. Compress to 25% of original
    target_kb = original_size // 1024 // 4
    compress_resp = client.post("/api/compress", json={
        "file_id": file_id,
        "target_size_kb": target_kb,
    })
    assert compress_resp.status_code == 200
    assert compress_resp.json()["compressed_size"] <= target_kb * 1024 * 1.05

    # 3. Download
    download_resp = client.get(f"/api/download/{file_id}")
    assert download_resp.status_code == 200
    assert len(download_resp.content) == compress_resp.json()["compressed_size"]
