# SquishFile UI Redesign: 3-Step Wizard

## Overview

Redesign the single-page app into a 3-step wizard: Upload → Compress → Download. Decouple the upload and compression steps so users can tune target size before compression starts.

## Navigation

- Stepper bar at top with clickable completed steps
- Next/Back buttons at bottom
- State-driven page switching (no client-side router)
- Step 1 always accessible; Step 2 after files uploaded; Step 3 after compression starts

## Page 1: Upload (Left-Right Split)

- **Left:** DropZone (drag-and-drop + click to browse)
- **Right:** Scrollable file queue with remove buttons, file count, total size
- Files uploaded to server on drop but NOT compressed
- "Next" enabled when >= 1 file queued

## Page 2: Compress (Left 60% / Right 40%)

- **Left (larger):** Target size controls - preset buttons (50%, 25%, 1MB, 500KB, 200KB), slider, custom KB input
- **Right:** Compact file list with names and original sizes
- "Compress" button replaces "Next" - starts compression and navigates to page 3
- One global target size for all files

## Page 3: Download (Left 60% / Right 40%)

- **Left:** Summary stats (files count, original/compressed size, savings %), "Download All (ZIP)" button, "Start Over" button
- **Right:** Individual file results with progress bars, size reduction, individual download buttons
- ZIP download bundles all compressed files

## Technical Changes

### Frontend (New Components)
- `Stepper.tsx` - Step indicator bar
- `UploadPage.tsx` - Upload page layout
- `CompressPage.tsx` - Compression config page
- `DownloadPage.tsx` - Results and download page

### Frontend (Modified)
- `App.tsx` - Step-based page switching, state machine
- `FileCard.tsx` - Simplified for queue display
- `types.ts` - Updated types if needed

### Frontend (Unchanged)
- `DropZone.tsx`, `SizeControl.tsx`, `theme.ts`, `api/client.ts`

### Backend
- New endpoint: `GET /api/download-all` - ZIP archive of all compressed files
- All other endpoints unchanged

### Unchanged
- Compression engine, ML predictor, file detection, dark theme
