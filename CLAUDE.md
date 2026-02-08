# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Is This

SquishFile is a full-stack file compression app with ML-based quality prediction. Users upload images/PDFs, set a target size, and download compressed results. The backend uses binary search over quality settings (and resolution scaling as fallback) to hit target sizes. A pre-trained scikit-learn model predicts optimal initial quality.

## Commands

### Backend (from repo root)
```bash
pip install -e .              # Install package in dev mode
squishfile                    # Run the app (auto-detects port 8000-8100, opens browser)
uvicorn squishfile.main:app   # Run backend directly
pytest                        # Run all tests
pytest tests/test_engine.py   # Run a single test file
pytest -k "test_name"         # Run a single test by name
```

### Frontend (from `frontend/`)
```bash
npm install                   # Install dependencies
npm run dev                   # Dev server on :3000 (proxies /api to :8000)
npm run build                 # TypeScript check + Vite production build
npm run lint                  # ESLint
```

### Full-stack development
Run `uvicorn squishfile.main:app --reload` in one terminal and `npm run dev` in `frontend/` in another. The Vite dev server proxies `/api` requests to the backend at `http://127.0.0.1:8000`.

For production, build the frontend (`npm run build` in `frontend/`), then run `squishfile` — FastAPI serves the built frontend from `squishfile/frontend/dist/`.

## Architecture

**Backend:** FastAPI (Python 3.10+) — `squishfile/`
- `main.py` — App setup, CORS, static file serving, SPA fallback
- `cli.py` — CLI entry point with port auto-detection (8000-8100)
- `detector.py` — MIME type detection via libmagic
- `routes/upload.py` — Upload endpoint, in-memory file store (`file_store` dict)
- `routes/compress.py` — Compress + download endpoints (single file and ZIP batch)
- `compressor/engine.py` — Orchestrator: calls predictor, then binary-searches quality
- `compressor/image.py` — JPEG/WebP quality tuning, PNG/GIF convert-to-JPEG, resolution fallback
- `compressor/pdf.py` — Extracts embedded images from PDF, compresses them, rebuilds PDF
- `compressor/predictor.py` — Loads `models/quality_model.pkl`, predicts quality from file features

**Frontend:** React 19 + TypeScript + Vite + Tailwind CSS 4 — `frontend/`
- 3-step pipeline UI: Upload → Compress → Download
- `api/client.ts` — REST client (`uploadFile`, `compressFile`, `downloadUrl`)
- `App.tsx` — Main state machine managing `FileEntry[]` through status transitions

**API endpoints:**
- `POST /api/upload` — FormData file → `{id, mime, category, size, ...}`
- `POST /api/compress` — `{file_id, target_size_kb}` → `{compressed_size, skipped, ...}`
- `GET /api/download/{file_id}` — Binary stream with Content-Disposition
- `GET /api/download-all?ids=...` — ZIP archive of multiple files

**Key design decisions:**
- Files are stored in-memory (no database) — lost on server restart
- Compression uses binary search over quality (tolerance: 5%), with resolution scaling fallback
- ML predictor provides initial quality guess; heuristic fallback if model unavailable
- Frontend built assets are bundled into the Python package (`squishfile/frontend/dist/`)

## Tech Stack

- **Backend:** FastAPI, Uvicorn, Pillow, PyMuPDF (fitz), scikit-learn, python-magic-bin
- **Frontend:** React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4 (via `@tailwindcss/vite`)
- **Tests:** pytest (configured in `pyproject.toml`, test files in `tests/`)
