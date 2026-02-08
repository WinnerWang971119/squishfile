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


def test_upload_video_returns_duration(tmp_path):
    """Uploading a video should return duration instead of width/height."""
    import subprocess, os
    from squishfile.compressor.ffmpeg_utils import get_ffmpeg
    video_path = str(tmp_path / "test.mp4")
    subprocess.run([
        get_ffmpeg(), "-y",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=15",
        "-c:v", "libx264", "-preset", "ultrafast",
        video_path,
    ], capture_output=True, timeout=15, check=True)

    with open(video_path, "rb") as f:
        video_data = f.read()

    from io import BytesIO

    resp = client.post("/api/upload", files={"file": ("test.mp4", BytesIO(video_data), "video/mp4")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "video"
    assert "duration" in data
    assert data["duration"] > 0
