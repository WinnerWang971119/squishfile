# SquishFile Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local file compressor web app with Kanban-style UI, ML-predicted compression, supporting images and PDFs.

**Architecture:** Python FastAPI backend handles file detection, ML-predicted compression (Pillow for images, PyMuPDF for PDFs), and serves a bundled React frontend. Single `pip install squishfile && squishfile` launches everything.

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, Pillow, PyMuPDF, scikit-learn, React 18, TypeScript, Vite, Tailwind CSS

---

## Phase 1: Project Scaffolding

### Task 1: Initialize Python project structure

**Files:**
- Create: `pyproject.toml`
- Create: `squishfile/__init__.py`
- Create: `squishfile/cli.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "squishfile"
version = "0.1.0"
description = "Local file compressor with smart ML-predicted compression"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pillow>=10.0.0",
    "pymupdf>=1.23.0",
    "scikit-learn>=1.3.0",
    "python-magic-bin>=0.4.14",
    "python-multipart>=0.0.6",
    "numpy>=1.24.0",
    "joblib>=1.3.0",
]

[project.scripts]
squishfile = "squishfile.cli:main"

[tool.setuptools.packages.find]
include = ["squishfile*"]

[tool.setuptools.package-data]
squishfile = ["models/*.pkl", "frontend/dist/**/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

**Step 2: Create squishfile/__init__.py**

```python
"""SquishFile - Local file compressor with smart ML-predicted compression."""
__version__ = "0.1.0"
```

**Step 3: Create squishfile/cli.py**

```python
import webbrowser
import uvicorn


def main():
    host = "127.0.0.1"
    port = 8000
    print(f"\n  SquishFile is running at http://{host}:{port}\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run("squishfile.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
```

**Step 4: Install in dev mode**

Run: `pip install -e ".[dev]"` from project root
Expected: Installs successfully, `squishfile` command available

**Step 5: Commit**

```bash
git init
git add pyproject.toml squishfile/__init__.py squishfile/cli.py
git commit -m "chore: initialize project structure with pyproject.toml and CLI entry point"
```

---

### Task 2: Initialize FastAPI app with health check

**Files:**
- Create: `squishfile/main.py`
- Create: `tests/__init__.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing test**

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from squishfile.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_health_check -v`
Expected: FAIL (squishfile.main doesn't exist)

**Step 3: Write minimal implementation**

```python
# squishfile/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from squishfile import __version__

app = FastAPI(title="SquishFile", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": __version__}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_health_check -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/main.py tests/
git commit -m "feat: add FastAPI app with health check endpoint"
```

---

## Phase 2: File Detection & Upload

### Task 3: Build file type detector

**Files:**
- Create: `squishfile/detector.py`
- Create: `tests/test_detector.py`

**Step 1: Write the failing test**

```python
# tests/test_detector.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_detector.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# squishfile/detector.py
import magic

SUPPORTED_IMAGES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}

SUPPORTED_PDFS = {
    "application/pdf": ".pdf",
}

SUPPORTED = {**SUPPORTED_IMAGES, **SUPPORTED_PDFS}


def detect_file_type(data: bytes, filename: str) -> dict:
    mime = magic.from_buffer(data, mime=True)

    if mime in SUPPORTED_IMAGES:
        category = "image"
    elif mime in SUPPORTED_PDFS:
        category = "pdf"
    else:
        category = "unsupported"

    extension = SUPPORTED.get(mime, "")

    return {
        "mime": mime,
        "category": category,
        "extension": extension,
        "original_filename": filename,
        "size": len(data),
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_detector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/detector.py tests/test_detector.py
git commit -m "feat: add MIME-based file type detector"
```

---

### Task 4: Build upload endpoint

**Files:**
- Create: `squishfile/routes/__init__.py`
- Create: `squishfile/routes/upload.py`
- Create: `tests/test_upload.py`
- Modify: `squishfile/main.py` (add router)

**Step 1: Write the failing test**

```python
# tests/test_upload.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_upload.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# squishfile/routes/__init__.py
```

```python
# squishfile/routes/upload.py
import uuid
import io
from fastapi import APIRouter, UploadFile, HTTPException
from PIL import Image
from squishfile.detector import detect_file_type

router = APIRouter(prefix="/api")

# In-memory store for uploaded files (per session)
file_store: dict[str, dict] = {}


@router.post("/upload")
async def upload_file(file: UploadFile):
    data = await file.read()

    if len(data) > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit")

    info = detect_file_type(data, file.filename or "unknown")

    if info["category"] == "unsupported":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {info['mime']}",
        )

    file_id = str(uuid.uuid4())[:8]
    entry = {
        "id": file_id,
        "data": data,
        **info,
    }

    # Extract image dimensions
    if info["category"] == "image" and info["mime"] != "image/svg+xml":
        img = Image.open(io.BytesIO(data))
        entry["width"] = img.width
        entry["height"] = img.height

    file_store[file_id] = entry

    # Return info without raw data
    return {k: v for k, v in entry.items() if k != "data"}
```

**Step 4: Add router to main.py**

Add to `squishfile/main.py` after middleware:

```python
from squishfile.routes.upload import router as upload_router
app.include_router(upload_router)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_upload.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add squishfile/routes/ tests/test_upload.py squishfile/main.py
git commit -m "feat: add file upload endpoint with type detection"
```

---

## Phase 3: Compression Engine

### Task 5: Build image compressor (JPEG/WebP)

**Files:**
- Create: `squishfile/compressor/__init__.py`
- Create: `squishfile/compressor/image.py`
- Create: `tests/test_image_compressor.py`

**Step 1: Write the failing test**

```python
# tests/test_image_compressor.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_image_compressor.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# squishfile/compressor/__init__.py
```

```python
# squishfile/compressor/image.py
import io
from PIL import Image

QUALITY_FORMATS = {"image/jpeg", "image/webp"}


def compress_image(
    data: bytes,
    mime: str,
    target_size: int,
) -> dict:
    original_size = len(data)

    if original_size <= target_size:
        return {"data": data, "size": original_size, "skipped": True}

    if mime in QUALITY_FORMATS:
        return _compress_with_quality(data, mime, target_size)

    if mime == "image/png":
        return _compress_png(data, target_size)

    if mime == "image/gif":
        return _compress_gif(data, target_size)

    # Fallback: return original
    return {"data": data, "size": original_size, "skipped": True}


def _compress_with_quality(
    data: bytes, mime: str, target_size: int
) -> dict:
    fmt = "JPEG" if mime == "image/jpeg" else "WEBP"
    img = Image.open(io.BytesIO(data))

    if img.mode == "RGBA" and fmt == "JPEG":
        img = img.convert("RGB")

    # Estimate starting quality from size ratio
    ratio = target_size / len(data)
    quality = max(5, min(95, int(ratio * 85)))

    lo, hi = 5, 95
    best_data = None
    best_size = float("inf")

    # Binary search for optimal quality (max 10 iterations)
    for _ in range(10):
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=quality, optimize=True)
        result_size = buf.tell()

        if abs(result_size - target_size) / target_size <= 0.05:
            return {"data": buf.getvalue(), "size": result_size, "skipped": False}

        if result_size <= target_size and (
            best_data is None or result_size > best_size
        ):
            best_data = buf.getvalue()
            best_size = result_size

        if result_size > target_size:
            hi = quality - 1
        else:
            lo = quality + 1

        if lo > hi:
            break
        quality = (lo + hi) // 2

    # Fallback: reduce resolution if quality alone isn't enough
    if best_data is None or best_size > target_size * 1.05:
        return _compress_with_resize(img, fmt, target_size)

    return {"data": best_data, "size": best_size, "skipped": False}


def _compress_with_resize(
    img: Image.Image, fmt: str, target_size: int
) -> dict:
    scale = 0.9
    for _ in range(10):
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format=fmt, quality=60, optimize=True)
        result_size = buf.tell()

        if result_size <= target_size * 1.05:
            return {"data": buf.getvalue(), "size": result_size, "skipped": False}

        scale *= 0.8

    # Return best effort
    return {"data": buf.getvalue(), "size": buf.tell(), "skipped": False}


def _compress_png(data: bytes, target_size: int) -> dict:
    img = Image.open(io.BytesIO(data))

    # Try converting to JPEG (lossy) to hit target
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    else:
        img = img.convert("RGB")

    return _compress_with_quality(
        _image_to_bytes(img, "JPEG", 95), "image/jpeg", target_size
    )


def _compress_gif(data: bytes, target_size: int) -> dict:
    img = Image.open(io.BytesIO(data))
    # Convert first frame to JPEG
    rgb = img.convert("RGB")
    return _compress_with_quality(
        _image_to_bytes(rgb, "JPEG", 95), "image/jpeg", target_size
    )


def _image_to_bytes(img: Image.Image, fmt: str, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality)
    buf.seek(0)
    return buf.read()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_image_compressor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/ tests/test_image_compressor.py
git commit -m "feat: add image compressor with binary search quality optimization"
```

---

### Task 6: Build PDF compressor

**Files:**
- Create: `squishfile/compressor/pdf.py`
- Create: `tests/test_pdf_compressor.py`

**Step 1: Write the failing test**

```python
# tests/test_pdf_compressor.py
import io
import fitz  # PyMuPDF
from PIL import Image
from squishfile.compressor.pdf import compress_pdf


def _make_test_pdf_with_image() -> bytes:
    """Create a PDF with an embedded large image."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Create a large image and embed it
    img = Image.new("RGB", (800, 600), color="blue")
    for y in range(600):
        for x in range(800):
            img.putpixel((x, y), ((x * 7) % 256, (y * 3) % 256, 128))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG", quality=95)
    img_buf.seek(0)

    rect = fitz.Rect(50, 50, 550, 450)
    page.insert_image(rect, stream=img_buf.getvalue())

    pdf_bytes = doc.tobytes(deflate=True)
    doc.close()
    return pdf_bytes


def test_compress_pdf():
    original = _make_test_pdf_with_image()
    target_size = len(original) // 2
    result = compress_pdf(original, target_size)
    assert len(result["data"]) <= target_size * 1.10  # 10% tolerance for PDFs
    assert result["data"][:5] == b"%PDF-"


def test_skip_small_pdf():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    result = compress_pdf(pdf_bytes, len(pdf_bytes) * 2)
    assert result["skipped"] is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pdf_compressor.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# squishfile/compressor/pdf.py
import io
import fitz  # PyMuPDF
from PIL import Image
from squishfile.compressor.image import compress_image


def compress_pdf(data: bytes, target_size: int) -> dict:
    original_size = len(data)

    if original_size <= target_size:
        return {"data": data, "size": original_size, "skipped": True}

    ratio = target_size / original_size
    doc = fitz.open(stream=data, filetype="pdf")

    # Extract and compress embedded images
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                img_data = base_image["image"]
                img_mime = f"image/{base_image['ext']}"

                img_target = max(1024, int(len(img_data) * ratio))
                compressed = compress_image(img_data, img_mime, img_target)

                if not compressed["skipped"]:
                    # Replace image in PDF
                    new_img = fitz.open(
                        stream=compressed["data"],
                        filetype=base_image["ext"],
                    )
                    pix = fitz.Pixmap(new_img, 0)
                    doc._setImage(xref, pixmap=pix)
                    new_img.close()
            except Exception:
                continue  # Skip images that can't be processed

    result_bytes = doc.tobytes(deflate=True, garbage=4)
    doc.close()

    return {
        "data": result_bytes,
        "size": len(result_bytes),
        "skipped": False,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pdf_compressor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/pdf.py tests/test_pdf_compressor.py
git commit -m "feat: add PDF compressor with embedded image compression"
```

---

### Task 7: Build ML quality predictor

**Files:**
- Create: `squishfile/compressor/predictor.py`
- Create: `squishfile/models/` (directory)
- Create: `scripts/train_model.py`
- Create: `tests/test_predictor.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_predictor.py -v`
Expected: FAIL

**Step 3: Write the training script**

```python
# scripts/train_model.py
"""
Generate training data and train quality prediction model.
Run once: python scripts/train_model.py
Outputs: squishfile/models/quality_model.pkl
"""
import io
import random
import numpy as np
from PIL import Image
from sklearn.linear_model import Ridge
import joblib
import os

random.seed(42)
np.random.seed(42)


def generate_training_data(n_samples=2000):
    X = []
    y = []

    for _ in range(n_samples):
        width = random.choice([640, 800, 1024, 1280, 1920, 2560, 3840])
        height = random.choice([480, 600, 768, 720, 1080, 1440, 2160])
        quality = random.randint(10, 95)

        # Create image with varied content
        img = Image.new("RGB", (width, height))
        pixels = img.load()
        seed_val = random.randint(0, 1000)
        for row in range(0, height, 4):
            for col in range(0, width, 4):
                r = (col * 7 + row * 3 + seed_val) % 256
                g = (col * 3 + row * 7 + seed_val) % 256
                b = (col * 5 + row * 5 + seed_val) % 256
                for dy in range(min(4, height - row)):
                    for dx in range(min(4, width - col)):
                        pixels[col + dx, row + dy] = (r, g, b)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        result_size = buf.tell()

        # Also get original (q=95) size for ratio
        buf95 = io.BytesIO()
        img.save(buf95, format="JPEG", quality=95, optimize=True)
        original_size = buf95.tell()

        pixel_count = width * height
        size_ratio = result_size / original_size if original_size > 0 else 1.0

        X.append([
            original_size,
            result_size,  # this is the "target"
            pixel_count,
            size_ratio,
        ])
        y.append(quality)

    return np.array(X), np.array(y)


def main():
    print("Generating training data...")
    X, y = generate_training_data(2000)

    print(f"Training on {len(X)} samples...")
    model = Ridge(alpha=1.0)
    model.fit(X, y)

    score = model.score(X, y)
    print(f"R² score: {score:.4f}")

    os.makedirs("squishfile/models", exist_ok=True)
    joblib.dump(model, "squishfile/models/quality_model.pkl")
    print("Model saved to squishfile/models/quality_model.pkl")


if __name__ == "__main__":
    main()
```

**Step 4: Run training script**

Run: `python scripts/train_model.py`
Expected: Model saved to squishfile/models/quality_model.pkl

**Step 5: Write predictor implementation**

```python
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
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_predictor.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add squishfile/compressor/predictor.py squishfile/models/ scripts/train_model.py tests/test_predictor.py
git commit -m "feat: add ML quality predictor with pre-trained model"
```

---

### Task 8: Build compression engine (orchestrator)

**Files:**
- Create: `squishfile/compressor/engine.py`
- Create: `tests/test_engine.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_engine.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# squishfile/compressor/engine.py
from squishfile.compressor.image import compress_image
from squishfile.compressor.pdf import compress_pdf
from squishfile.compressor.predictor import predict_quality


def compress_file(
    data: bytes,
    mime: str,
    category: str,
    target_size: int,
    width: int = 0,
    height: int = 0,
) -> dict:
    original_size = len(data)

    if original_size <= target_size:
        return {
            "data": data,
            "size": original_size,
            "original_size": original_size,
            "skipped": True,
            "message": "File is already smaller than target!",
        }

    # Get ML-predicted quality for logging/future use
    if category == "image":
        predicted_q = predict_quality(
            file_type=mime,
            original_size=original_size,
            target_size=target_size,
            width=width or 1920,
            height=height or 1080,
        )

    if category == "image":
        result = compress_image(data, mime, target_size)
    elif category == "pdf":
        result = compress_pdf(data, target_size)
    else:
        return {
            "data": data,
            "size": original_size,
            "original_size": original_size,
            "skipped": True,
            "message": "Unsupported file type",
        }

    result["original_size"] = original_size

    if result["size"] > target_size * 1.05 and not result["skipped"]:
        result["message"] = (
            f"Best we could do: {result['size'] // 1024}KB "
            f"(target was {target_size // 1024}KB)"
        )

    return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_engine.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/engine.py tests/test_engine.py
git commit -m "feat: add compression engine orchestrator with ML prediction"
```

---

## Phase 4: Compress & Download API

### Task 9: Build compress and download endpoints

**Files:**
- Create: `squishfile/routes/compress.py`
- Create: `tests/test_compress_api.py`
- Modify: `squishfile/main.py` (add router)

**Step 1: Write the failing test**

```python
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

    resp = client.post(f"/api/compress", json={
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_compress_api.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# squishfile/routes/compress.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from squishfile.routes.upload import file_store
from squishfile.compressor.engine import compress_file

router = APIRouter(prefix="/api")


class CompressRequest(BaseModel):
    file_id: str
    target_size_kb: int


@router.post("/compress")
async def compress(req: CompressRequest):
    entry = file_store.get(req.file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")

    target_bytes = req.target_size_kb * 1024

    result = compress_file(
        data=entry["data"],
        mime=entry["mime"],
        category=entry["category"],
        target_size=target_bytes,
        width=entry.get("width", 0),
        height=entry.get("height", 0),
    )

    # Store compressed data
    entry["compressed_data"] = result["data"]
    entry["compressed_size"] = result["size"]

    return {
        "file_id": req.file_id,
        "original_size": result["original_size"],
        "compressed_size": result["size"],
        "skipped": result["skipped"],
        "message": result.get("message"),
    }


@router.get("/download/{file_id}")
async def download(file_id: str):
    entry = file_store.get(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")

    data = entry.get("compressed_data", entry["data"])
    filename = entry["original_filename"]

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

**Step 4: Add router to main.py**

Add to `squishfile/main.py`:

```python
from squishfile.routes.compress import router as compress_router
app.include_router(compress_router)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_compress_api.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add squishfile/routes/compress.py tests/test_compress_api.py squishfile/main.py
git commit -m "feat: add compress and download API endpoints"
```

---

## Phase 5: React Frontend

### Task 10: Initialize React project with Vite + Tailwind

**Files:**
- Create: `frontend/` (via Vite scaffold)
- Create: `frontend/src/styles/theme.ts`
- Create: `frontend/tailwind.config.js`

**Step 1: Scaffold React project**

Run from project root:
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss @tailwindcss/vite
```

**Step 2: Configure Tailwind**

```typescript
// frontend/src/styles/theme.ts
export const theme = {
  colors: {
    bg: "#0D0D0D",
    bgCard: "#1A1A1A",
    bgHover: "#252525",
    accent: "#FFD60A",
    accentHover: "#FFE44D",
    text: "#FAFAFA",
    textMuted: "#888888",
    border: "#333333",
    success: "#22C55E",
    error: "#EF4444",
  },
} as const;
```

**Step 3: Configure Vite proxy to backend**

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
```

**Step 4: Verify dev server starts**

Run: `npm run dev`
Expected: Vite dev server on localhost:3000

**Step 5: Commit**

```bash
git add frontend/
git commit -m "chore: scaffold React frontend with Vite, TypeScript, and Tailwind"
```

---

### Task 11: Build API client and types

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/types.ts`

**Step 1: Define TypeScript types**

```typescript
// frontend/src/types.ts
export type FileStatus = "uploading" | "queued" | "compressing" | "done" | "error";

export interface FileEntry {
  id: string;
  originalFilename: string;
  mime: string;
  category: "image" | "pdf";
  size: number;
  width?: number;
  height?: number;
  status: FileStatus;
  progress: number;
  compressedSize?: number;
  message?: string;
  previewUrl?: string;
}

export interface UploadResponse {
  id: string;
  mime: string;
  category: string;
  size: number;
  width?: number;
  height?: number;
  original_filename: string;
}

export interface CompressResponse {
  file_id: string;
  original_size: number;
  compressed_size: number;
  skipped: boolean;
  message?: string;
}
```

**Step 2: Build API client**

```typescript
// frontend/src/api/client.ts
import { UploadResponse, CompressResponse } from "../types";

const BASE = "/api";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
  return res.json();
}

export async function compressFile(
  fileId: string,
  targetSizeKb: number
): Promise<CompressResponse> {
  const res = await fetch(`${BASE}/compress`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, target_size_kb: targetSizeKb }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Compression failed");
  return res.json();
}

export function downloadUrl(fileId: string): string {
  return `${BASE}/download/${fileId}`;
}
```

**Step 3: Commit**

```bash
git add frontend/src/api/ frontend/src/types.ts
git commit -m "feat: add API client and TypeScript types"
```

---

### Task 12: Build DropZone component

**Files:**
- Create: `frontend/src/components/DropZone.tsx`

**Step 1: Write DropZone component**

```tsx
// frontend/src/components/DropZone.tsx
import { useCallback, useState } from "react";

interface DropZoneProps {
  onFiles: (files: File[]) => void;
}

export function DropZone({ onFiles }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) onFiles(files);
    },
    [onFiles]
  );

  const handleClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.accept = "image/*,.pdf";
    input.onchange = (e) => {
      const files = Array.from((e.target as HTMLInputElement).files || []);
      if (files.length > 0) onFiles(files);
    };
    input.click();
  };

  return (
    <div
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        flex flex-col items-center justify-center
        h-full min-h-[200px] rounded-xl border-2 border-dashed
        cursor-pointer transition-all duration-200
        ${
          isDragging
            ? "border-[#FFD60A] bg-[#FFD60A]/10"
            : "border-[#333] hover:border-[#FFD60A]/50 hover:bg-[#1A1A1A]"
        }
      `}
    >
      <div className="text-4xl mb-3">+</div>
      <p className="text-[#FAFAFA] font-medium">Drop files here</p>
      <p className="text-[#888] text-sm mt-1">or click to browse</p>
      <p className="text-[#555] text-xs mt-3">Images & PDFs up to 100MB</p>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/DropZone.tsx
git commit -m "feat: add DropZone component with drag-and-drop"
```

---

### Task 13: Build FileCard component

**Files:**
- Create: `frontend/src/components/FileCard.tsx`

**Step 1: Write FileCard component**

```tsx
// frontend/src/components/FileCard.tsx
import { FileEntry } from "../types";
import { downloadUrl } from "../api/client";

interface FileCardProps {
  file: FileEntry;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileCard({ file }: FileCardProps) {
  const isCompressing = file.status === "compressing";
  const isDone = file.status === "done";
  const isError = file.status === "error";

  return (
    <div
      className={`
        bg-[#1A1A1A] rounded-lg p-3 border-l-3
        transition-all duration-300 ease-in-out
        ${isDone ? "border-l-[#22C55E]" : isError ? "border-l-[#EF4444]" : "border-l-[#FFD60A]"}
      `}
    >
      {/* Filename + type badge */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-[#FAFAFA] text-sm font-medium truncate max-w-[140px]">
          {file.originalFilename}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#333] text-[#888] uppercase">
          {file.mime.split("/")[1]}
        </span>
      </div>

      {/* Size info */}
      <div className="text-xs text-[#888] mb-2">
        {formatSize(file.size)}
        {file.compressedSize != null && (
          <>
            <span className="text-[#FFD60A] mx-1">&rarr;</span>
            <span className="text-[#FAFAFA]">{formatSize(file.compressedSize)}</span>
          </>
        )}
      </div>

      {/* Progress bar */}
      {isCompressing && (
        <div className="w-full h-1.5 bg-[#333] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#FFD60A] rounded-full transition-all duration-300"
            style={{ width: `${file.progress}%` }}
          />
        </div>
      )}

      {/* Done state */}
      {isDone && (
        <a
          href={downloadUrl(file.id)}
          className="
            inline-block mt-1 text-xs px-3 py-1 rounded
            bg-[#FFD60A] text-[#0D0D0D] font-medium
            hover:bg-[#FFE44D] transition-colors
          "
        >
          Download
        </a>
      )}

      {/* Error state */}
      {isError && (
        <p className="text-xs text-[#EF4444] mt-1">{file.message}</p>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/FileCard.tsx
git commit -m "feat: add FileCard component with progress and download"
```

---

### Task 14: Build SizeControl component

**Files:**
- Create: `frontend/src/components/SizeControl.tsx`

**Step 1: Write SizeControl component**

```tsx
// frontend/src/components/SizeControl.tsx
import { useState } from "react";

interface SizeControlProps {
  maxSizeKb: number;
  value: number;
  onChange: (kb: number) => void;
}

const PRESETS = [
  { label: "50%", factor: 0.5 },
  { label: "25%", factor: 0.25 },
  { label: "1 MB", kb: 1024 },
  { label: "500 KB", kb: 500 },
  { label: "200 KB", kb: 200 },
];

export function SizeControl({ maxSizeKb, value, onChange }: SizeControlProps) {
  const [customInput, setCustomInput] = useState("");

  const handlePreset = (preset: (typeof PRESETS)[number]) => {
    const kb = preset.kb ?? Math.round(maxSizeKb * preset.factor!);
    onChange(Math.max(10, Math.min(kb, maxSizeKb)));
  };

  const handleCustom = () => {
    const num = parseInt(customInput, 10);
    if (!isNaN(num) && num > 0) {
      onChange(Math.max(10, Math.min(num, maxSizeKb)));
    }
  };

  return (
    <div className="space-y-3">
      {/* Slider */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-[#888] w-12">10 KB</span>
        <input
          type="range"
          min={10}
          max={maxSizeKb}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-[#FFD60A] h-2 cursor-pointer"
        />
        <span className="text-xs text-[#888] w-16 text-right">
          {maxSizeKb >= 1024
            ? `${(maxSizeKb / 1024).toFixed(1)} MB`
            : `${maxSizeKb} KB`}
        </span>
      </div>

      {/* Current value */}
      <div className="text-center">
        <span className="text-[#FFD60A] font-bold text-lg">
          {value >= 1024
            ? `${(value / 1024).toFixed(1)} MB`
            : `${value} KB`}
        </span>
      </div>

      {/* Presets */}
      <div className="flex flex-wrap gap-2 justify-center">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => handlePreset(preset)}
            className="
              px-3 py-1 text-xs rounded-full
              bg-[#252525] text-[#FAFAFA] border border-[#333]
              hover:border-[#FFD60A] hover:text-[#FFD60A]
              transition-colors
            "
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Custom input */}
      <div className="flex gap-2 justify-center">
        <input
          type="number"
          placeholder="Custom KB"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCustom()}
          className="
            w-28 px-3 py-1.5 text-xs rounded-lg
            bg-[#1A1A1A] text-[#FAFAFA] border border-[#333]
            focus:border-[#FFD60A] focus:outline-none
            placeholder:text-[#555]
          "
        />
        <button
          onClick={handleCustom}
          className="
            px-3 py-1.5 text-xs rounded-lg
            bg-[#FFD60A] text-[#0D0D0D] font-medium
            hover:bg-[#FFE44D] transition-colors
          "
        >
          Set
        </button>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/SizeControl.tsx
git commit -m "feat: add SizeControl component with slider, presets, and custom input"
```

---

### Task 15: Build Pipeline (Kanban) layout

**Files:**
- Create: `frontend/src/components/Pipeline.tsx`

**Step 1: Write Pipeline component**

```tsx
// frontend/src/components/Pipeline.tsx
import { FileEntry } from "../types";
import { FileCard } from "./FileCard";

interface PipelineProps {
  files: FileEntry[];
}

export function Pipeline({ files }: PipelineProps) {
  const queued = files.filter(
    (f) => f.status === "uploading" || f.status === "queued"
  );
  const compressing = files.filter((f) => f.status === "compressing");
  const done = files.filter((f) => f.status === "done" || f.status === "error");

  return (
    <div className="grid grid-cols-3 gap-4 h-full">
      {/* Drop Zone / Queued column */}
      <Column title="QUEUED" count={queued.length} accent="text-[#FFD60A]">
        {queued.map((f) => (
          <FileCard key={f.id} file={f} />
        ))}
      </Column>

      {/* Compressing column */}
      <Column title="COMPRESSING" count={compressing.length} accent="text-[#FFD60A]">
        {compressing.map((f) => (
          <FileCard key={f.id} file={f} />
        ))}
      </Column>

      {/* Done column */}
      <Column title="DONE" count={done.length} accent="text-[#22C55E]">
        {done.map((f) => (
          <FileCard key={f.id} file={f} />
        ))}
      </Column>
    </div>
  );
}

function Column({
  title,
  count,
  accent,
  children,
}: {
  title: string;
  count: number;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-2 mb-3 px-1">
        <h2 className={`text-xs font-bold tracking-wider ${accent}`}>
          {title}
        </h2>
        {count > 0 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#252525] text-[#888]">
            {count}
          </span>
        )}
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto pr-1">{children}</div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/Pipeline.tsx
git commit -m "feat: add Pipeline Kanban layout with 3 columns"
```

---

### Task 16: Wire up App.tsx with full flow

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css`

**Step 1: Write main App component**

```tsx
// frontend/src/App.tsx
import { useState, useCallback } from "react";
import { DropZone } from "./components/DropZone";
import { Pipeline } from "./components/Pipeline";
import { SizeControl } from "./components/SizeControl";
import { uploadFile, compressFile, downloadUrl } from "./api/client";
import { FileEntry } from "./types";

export default function App() {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [targetKb, setTargetKb] = useState(500);
  const [maxKb, setMaxKb] = useState(10240); // 10MB default max

  const updateFile = useCallback((id: string, updates: Partial<FileEntry>) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, ...updates } : f))
    );
  }, []);

  const handleFiles = useCallback(
    async (newFiles: File[]) => {
      for (const file of newFiles) {
        // Create placeholder entry
        const tempId = `temp-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const entry: FileEntry = {
          id: tempId,
          originalFilename: file.name,
          mime: file.type || "application/octet-stream",
          category: "image",
          size: file.size,
          status: "uploading",
          progress: 0,
        };
        setFiles((prev) => [...prev, entry]);

        try {
          // Upload
          const uploaded = await uploadFile(file);
          const realId = uploaded.id;

          setFiles((prev) =>
            prev.map((f) =>
              f.id === tempId
                ? {
                    ...f,
                    id: realId,
                    mime: uploaded.mime,
                    category: uploaded.category as "image" | "pdf",
                    size: uploaded.size,
                    width: uploaded.width,
                    height: uploaded.height,
                    status: "compressing",
                    progress: 10,
                  }
                : f
            )
          );

          // Update max slider based on largest file
          const fileSizeKb = Math.ceil(uploaded.size / 1024);
          setMaxKb((prev) => Math.max(prev, fileSizeKb));

          // Simulate progress
          const progressInterval = setInterval(() => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === realId && f.status === "compressing"
                  ? { ...f, progress: Math.min(f.progress + 15, 90) }
                  : f
              )
            );
          }, 300);

          // Compress
          const result = await compressFile(realId, targetKb);

          clearInterval(progressInterval);

          setFiles((prev) =>
            prev.map((f) =>
              f.id === realId
                ? {
                    ...f,
                    status: "done",
                    progress: 100,
                    compressedSize: result.compressed_size,
                    message: result.message || undefined,
                  }
                : f
            )
          );
        } catch (err: any) {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === tempId || f.status === "uploading" || f.status === "compressing"
                ? { ...f, status: "error", message: err.message }
                : f
            )
          );
        }
      }
    },
    [targetKb]
  );

  const doneFiles = files.filter((f) => f.status === "done");

  const handleDownloadAll = () => {
    doneFiles.forEach((f) => {
      const a = document.createElement("a");
      a.href = downloadUrl(f.id);
      a.download = f.originalFilename;
      a.click();
    });
  };

  return (
    <div className="min-h-screen bg-[#0D0D0D] text-[#FAFAFA] flex flex-col">
      {/* Header */}
      <header className="px-6 py-4 border-b border-[#222]">
        <h1 className="text-xl font-bold">
          <span className="text-[#FFD60A]">Squish</span>File
        </h1>
      </header>

      {/* Main content */}
      <main className="flex-1 p-6 flex flex-col gap-6 max-w-6xl mx-auto w-full">
        {/* Drop zone + Kanban */}
        <div className="grid grid-cols-[280px_1fr] gap-6 flex-1 min-h-[400px]">
          <DropZone onFiles={handleFiles} />
          <Pipeline files={files} />
        </div>

        {/* Bottom controls */}
        <div className="bg-[#141414] rounded-xl p-4 border border-[#222]">
          <div className="flex items-center gap-8">
            <div className="flex-1">
              <p className="text-xs text-[#888] mb-2 font-medium">TARGET SIZE</p>
              <SizeControl
                maxSizeKb={maxKb}
                value={targetKb}
                onChange={setTargetKb}
              />
            </div>
            {doneFiles.length > 1 && (
              <button
                onClick={handleDownloadAll}
                className="
                  px-6 py-3 rounded-xl
                  bg-[#FFD60A] text-[#0D0D0D] font-bold
                  hover:bg-[#FFE44D] transition-colors
                  whitespace-nowrap
                "
              >
                Download All ({doneFiles.length})
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
```

**Step 2: Update index.css for Tailwind**

```css
/* frontend/src/index.css */
@import "tailwindcss";

body {
  margin: 0;
  background: #0D0D0D;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: #1A1A1A;
}
::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

/* Slider styling */
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  background: #333;
  border-radius: 3px;
  outline: none;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: #FFD60A;
  border-radius: 50%;
  cursor: pointer;
}
```

**Step 3: Verify frontend runs**

Run: `cd frontend && npm run dev`
Expected: App renders on localhost:3000 with dark theme

**Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: wire up App with full upload-compress-download flow"
```

---

## Phase 6: Bundle & Ship

### Task 17: Build frontend and serve from FastAPI

**Files:**
- Modify: `squishfile/main.py` (add static file serving)
- Modify: `squishfile/cli.py` (add port fallback)

**Step 1: Build frontend**

Run: `cd frontend && npm run build`
Expected: `frontend/dist/` created

**Step 2: Copy dist into Python package**

Run: `cp -r frontend/dist squishfile/frontend/dist`

**Step 3: Update main.py to serve static files**

Add to `squishfile/main.py`:

```python
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Mount static files (after API routes)
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
```

**Step 4: Update cli.py with port fallback**

```python
# squishfile/cli.py
import socket
import webbrowser
import uvicorn


def _find_port(start=8000, end=8100) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def main():
    host = "127.0.0.1"
    port = _find_port()
    print(f"\n  SquishFile is running at http://{host}:{port}\n")
    webbrowser.open(f"http://{host}:{port}")
    uvicorn.run("squishfile.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
```

**Step 5: Test full stack locally**

Run: `python -m squishfile.cli`
Expected: Opens browser, full Kanban UI works end-to-end

**Step 6: Commit**

```bash
git add squishfile/ frontend/dist/
git commit -m "feat: bundle frontend and serve from FastAPI with port fallback"
```

---

### Task 18: Final integration test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
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
```

**Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add full pipeline integration test"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1. Scaffolding | 1-2 | Project structure, FastAPI app |
| 2. Detection & Upload | 3-4 | File type detector, upload API |
| 3. Compression | 5-8 | Image, PDF, ML predictor, engine |
| 4. API | 9 | Compress + download endpoints |
| 5. Frontend | 10-16 | React Kanban UI with all components |
| 6. Ship | 17-18 | Bundle, serve, integration test |

**Total: 18 tasks, ~3-5 minutes each**
