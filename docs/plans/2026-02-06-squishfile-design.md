# SquishFile - Design Document

## Overview

A local file compressor with a Kanban-style web UI. Supports images and PDFs. Uses ML-predicted quality settings for fast, accurate compression to a user-chosen target size.

```bash
pip install squishfile && squishfile
```

## Architecture

```
[Browser UI :8000]  <-->  [FastAPI Backend]  <-->  [Compression Engine]
   React (bundled)          uvicorn               Pillow / PyMuPDF
                                                  ML Predictor
```

- **FastAPI** backend serves the React build as static files
- React frontend is pre-built and bundled inside the Python package — no Node.js at runtime
- All processing happens locally. No data leaves the machine.

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/upload` | POST | Receive file, auto-detect type, return file info + preview |
| `/api/compress` | POST | Compress file to target size, return result |
| `/api/download/{id}` | GET | Download compressed file |
| `/api/download-all` | GET | Download all completed files as ZIP |

## File Type Support (MVP)

- **Images:** JPEG, PNG, WebP, GIF, SVG
- **PDFs:** with embedded image compression

Auto-detection via python-magic (MIME-based, not extension-based).

## Compression Strategy: ML-First with Binary Search Fallback

### What makes this different

Most compressors blindly iterate quality settings. SquishFile **predicts** the right quality parameter in one shot using a pre-trained regression model. Only refines if the prediction misses.

### Pre-trained Model

- Ships as a static ~50KB pickle file inside the package
- Trained on ~10K sample files across common sizes
- Input features: `file_type`, `original_size`, `target_size`, `dimensions`, `color_complexity`
- Output: predicted `quality_parameter`
- No training at install time. Works from the first file.

### Compression Flow

```
1. Detect file type + extract features (dimensions, color depth, etc.)
2. ML model predicts optimal quality parameter -> compress once
3. Check result size:
   - Within 5% of target? -> Done (most cases, single pass)
   - Off by more? -> 2-3 binary search refinements (rare)
4. Return result
```

### Image Compression

- **JPEG/WebP:** Quality parameter 1-100, predicted by model
- **PNG:** Convert to WebP/JPEG if target much smaller than lossless allows, otherwise reduce color palette
- **GIF:** Reduce frame count + colors + dimensions proportionally
- **SVG:** Minify (strip metadata, simplify paths)
- **Fallback:** If quality alone can't hit target, progressively downscale resolution

### PDF Compression

- Extract embedded images -> compress each with image strategy
- Strip metadata, flatten annotations if needed
- Rebuild PDF with compressed images
- **Fallback:** Reduce image DPI progressively (300 -> 150 -> 72)

### Tolerance

Within **5% of target size** (e.g., target 500KB -> result 475-525KB). If original is already smaller than target, skip compression.

## UI Design: Kanban Pipeline

### Layout

Three-column Kanban board. Files flow left to right as they get compressed.

```
+------------------+------------------+----------------------------+
|   DROP ZONE      |  COMPRESSING     |   DONE                     |
|                  |                  |                            |
|  +------------+  |  +------------+  |  +------------+            |
|  |            |  |  | photo.jpg  |  |  | logo.png   |            |
|  | Drop files |  |  | 4.2MB>500K |  |  | 2.1MB>200K |            |
|  |   here     |  |  | [====] 68% |  |  | Done       |            |
|  |            |  |  +------------+  |  | [Download]  |            |
|  +------------+  |                  |  +------------+            |
|                  |  +------------+  |                            |
|                  |  | report.pdf |  |  +------------+            |
|                  |  | 8MB>1MB    |  |  | photo.jpg  |            |
|                  |  | [==] 30%   |  |  | 4.2MB>500K |            |
|                  |  +------------+  |  | Done       |            |
|                  |                  |  | [Download]  |            |
|                  |                  |  +------------+            |
+------------------+------------------+----------------------------+
| Target: [slider] 500KB   [50%] [25%] [1MB] [Custom]             |
|                                        [Download All]            |
+------------------------------------------------------------------+
```

### Visual Style

- **Background:** #0D0D0D (near black)
- **Accent:** #FFD60A (yellow)
- **Text:** #FAFAFA (white)
- **Borders:** subtle gray
- Cards have yellow left border
- Progress bars in yellow
- Done cards get yellow checkmark
- Smooth CSS animations as cards slide between columns

### Size Controls (pinned at bottom)

- **Slider:** from 10KB to original file size
- **Preset chips:** 50%, 25%, 1MB, 500KB
- **Custom input:** type exact target size
- Applies to all new uploads. Click individual cards to override per file.

### Interactions

- Drag & drop or click to upload in Drop Zone
- File type auto-detected, shown as badge on card
- Click any Done card to expand before/after preview (images) or size breakdown (PDFs)
- "Download All" button creates ZIP of all completed files

## Project Structure

```
squishfile/
  backend/
    main.py              # FastAPI app, CORS, static serving
    cli.py               # Entry point: `squishfile` command
    detector.py          # Auto file type detection (python-magic)
    compressor/
      engine.py          # Core compression orchestrator
      predictor.py       # ML quality predictor
      image.py           # JPEG, PNG, WebP, GIF, SVG handlers
      pdf.py             # PDF compression handler
    models/
      quality_model.pkl  # Pre-trained regression model (~50KB)
  frontend/
    src/
      App.tsx
      components/
        DropZone.tsx
        Pipeline.tsx     # Kanban 3-column layout
        FileCard.tsx     # Animated card component
        SizeControl.tsx  # Slider + presets + input
        Preview.tsx      # Before/after comparison
      styles/
        theme.ts         # Dark + yellow design tokens
    dist/                # Built & bundled into Python package
  setup.py
  pyproject.toml
```

## One-Line Install

```bash
pip install squishfile && squishfile
```

1. `pip install` pulls Python deps + bundled React dist
2. `squishfile` command starts uvicorn on localhost:8000
3. FastAPI serves React build as static files
4. Auto-opens browser to http://localhost:8000

### Dependencies

- `fastapi` + `uvicorn` — API server
- `Pillow` — image compression
- `PyMuPDF` — PDF handling
- `scikit-learn` — quality prediction model
- `python-magic` — file type detection

## Error Handling

| Scenario | Behavior |
|---|---|
| File > 100MB | Reject with friendly message |
| Target > original size | "File is already smaller than target!" |
| Target too small to achieve | Compress to minimum, warn: "Best we could do: 120KB (target was 50KB)" |
| Corrupted file | Error on card, don't crash pipeline |
| SVG already tiny | Skip compression, move to Done |
| Unsupported file type | Clear error card in Drop Zone |
| Port 8000 busy | Auto-find next available port |
| Temp files | Auto-cleaned on shutdown + every 30 minutes |
| Ctrl+C | Graceful shutdown, clean temp files |
