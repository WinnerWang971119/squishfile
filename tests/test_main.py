import importlib
import os

from fastapi.testclient import TestClient
from squishfile import main


client = TestClient(main.app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_app_setup_with_dist_without_assets(monkeypatch, tmp_path):
    dist_dir = tmp_path / "frontend" / "dist"
    dist_dir.mkdir(parents=True)

    real_dirname = os.path.dirname

    def fake_dirname(path):
        if path == main.__file__:
            return str(tmp_path)
        return real_dirname(path)

    try:
        with monkeypatch.context() as patched:
            patched.setattr(os.path, "dirname", fake_dirname)
            reloaded_main = importlib.reload(main)

            assert reloaded_main.FRONTEND_DIR == str(dist_dir)
            assert not reloaded_main.os.path.isdir(reloaded_main.FRONTEND_ASSETS_DIR)

            response = TestClient(reloaded_main.app).get("/api/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok", "version": "0.1.0"}
    finally:
        importlib.reload(main)
