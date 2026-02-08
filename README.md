# SquishFile

A full-stack file compression app with ML-based quality prediction. Upload images, PDFs, videos, or audio files, set a target size, and download optimally compressed results.

**Supported formats:** JPEG, PNG, WebP, GIF, PDF, MP4, AVI, MOV, MKV, MP3, WAV, FLAC, AAC, OGG

## Quick Start

```bash
# Install
pip install -e .

# Run (auto-opens browser on port 8000-8100)
squishfile
```

That's it. Upload files, set your target size, and download the compressed output.

---

## Detailed Guide

### Prerequisites

- Python 3.10+
- Node.js 18+ (only needed for frontend development)

### Installation

```bash
# Clone the repo
git clone https://github.com/your-username/squishfile.git
cd squishfile

# Install the Python package
pip install -e .
```

The frontend comes pre-built and bundled with the Python package. No separate frontend build step is needed for normal use.

### Usage

#### One-command launch

```bash
squishfile
```

This starts the server, auto-detects an available port (8000-8100), and opens your browser.

#### Manual server start

```bash
uvicorn squishfile.main:app --host 0.0.0.0 --port 8000
```

Then visit `http://localhost:8000` in your browser.

### How It Works

1. **Upload** — Drag and drop or select files. The app detects the file type automatically.
2. **Set target size** — Choose your desired output size in KB.
3. **Compress & download** — The engine binary-searches over quality settings to hit your target. Download individually or as a ZIP batch.

A pre-trained scikit-learn model predicts the optimal starting quality for images, so compression converges faster. If the model is unavailable, a heuristic fallback kicks in.

### Architecture

```
squishfile/                  # Backend (FastAPI)
├── main.py                  # App setup, CORS, static serving
├── cli.py                   # CLI entry point, port auto-detection
├── detector.py              # MIME type detection
├── routes/
│   ├── upload.py            # Upload endpoint, in-memory file store
│   └── compress.py          # Compress + download endpoints
├── compressor/
│   ├── engine.py            # Orchestrator: predictor → binary search
│   ├── image.py             # JPEG/WebP quality, PNG/GIF conversion, resolution fallback
│   ├── pdf.py               # PDF image extraction & recompression
│   ├── video.py             # Video compression via FFmpeg
│   └── audio.py             # Audio compression via FFmpeg
│   └── predictor.py         # ML quality prediction
└── models/
    └── quality_model.pkl    # Pre-trained model

frontend/                    # Frontend (React + TypeScript + Vite)
├── src/
│   ├── App.tsx              # Main state machine (Upload → Compress → Download)
│   └── api/client.ts        # REST client
└── ...
```

### API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/upload` | POST | Upload a file (FormData) → returns `{id, mime, category, size}` |
| `/api/compress` | POST | Compress a file → `{file_id, target_size_kb}` → returns `{compressed_size, skipped}` |
| `/api/download/{file_id}` | GET | Download a compressed file |
| `/api/download-all?ids=...` | GET | Download multiple files as a ZIP archive |

### Development Setup

Run the backend and frontend dev servers separately for hot-reload:

```bash
# Terminal 1 — Backend
uvicorn squishfile.main:app --reload

# Terminal 2 — Frontend (from frontend/)
cd frontend
npm install
npm run dev
```

The Vite dev server runs on port 3000 and proxies `/api` requests to the backend at `http://127.0.0.1:8000`.

#### Building the frontend for production

```bash
cd frontend
npm run build
```

Built assets go to `squishfile/frontend/dist/`, which FastAPI serves in production mode.

### Running Tests

```bash
pytest                        # All tests
pytest tests/test_engine.py   # Single test file
pytest -k "test_name"         # Single test by name
```

### Tech Stack

- **Backend:** FastAPI, Uvicorn, Pillow, PyMuPDF, scikit-learn, imageio-ffmpeg
- **Frontend:** React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4
- **ML:** scikit-learn model for quality prediction
- **Tests:** pytest

## License

See [LICENSE](LICENSE).
