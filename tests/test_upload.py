import io
from PIL import Image
from fastapi.testclient import TestClient
from squishfile.main import app

client = TestClient(app)


def _make_jpeg_file():
    img = Image.new("RGB", (200, 200), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_upload_jpeg():
    buf = _make_jpeg_file()
    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "image"
    assert data["mime"] == "image/jpeg"
    assert "id" in data
    assert data["width"] == 200
    assert data["height"] == 200


def test_upload_unsupported():
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
