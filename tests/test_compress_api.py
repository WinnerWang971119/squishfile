# tests/test_compress_api.py
import io
from PIL import Image
from fastapi.testclient import TestClient
from squishfile.main import app

client = TestClient(app)


def _upload_jpeg(width=800, height=600):
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = ((x * 7) % 256, (y * 3) % 256, 128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    resp = client.post("/api/upload", files={"file": ("test.jpg", buf, "image/jpeg")})
    return resp.json()


def test_compress_endpoint():
    uploaded = _upload_jpeg()
    file_id = uploaded["id"]
    target_kb = uploaded["size"] // 1024 // 3  # 1/3 of original in KB

    resp = client.post("/api/compress", json={
        "file_id": file_id,
        "target_size_kb": target_kb,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["compressed_size"] <= target_kb * 1024 * 1.05


def test_download_endpoint():
    uploaded = _upload_jpeg()
    file_id = uploaded["id"]
    target_kb = uploaded["size"] // 1024 // 2

    client.post("/api/compress", json={
        "file_id": file_id,
        "target_size_kb": target_kb,
    })

    resp = client.get(f"/api/download/{file_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/octet-stream"
