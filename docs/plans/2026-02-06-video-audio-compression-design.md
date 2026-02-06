# Video & Audio Compression Support

## Summary

Add video (MP4, WebM, MOV) and audio (MP3, WAV) compression to SquishFile using FFmpeg as the compression backend.

## Decisions

- **Video formats:** MP4, WebM, MOV (common web formats)
- **Audio formats:** MP3, WAV (minimal scope)
- **Compression backend:** FFmpeg (system dependency, called directly via subprocess)
- **Video strategy:** Two-pass encoding with calculated bitrate for accurate size targeting
- **Audio strategy:** Single-pass MP3 encoding with calculated bitrate

## File Detection

Extend `detector.py` with new MIME mappings:

**Video** (category: `"video"`):
- `video/mp4` -> `.mp4`
- `video/webm` -> `.webm`
- `video/quicktime` -> `.mov`

**Audio** (category: `"audio"`):
- `audio/mpeg` -> `.mp3`
- `audio/wav` / `audio/x-wav` -> `.wav`

## Video Compressor

New file: `squishfile/compressor/video.py`

Function: `compress_video(data, mime, target_size) -> dict`

Strategy:
1. Write input bytes to temp file
2. Probe with `ffmpeg -i` to get duration, resolution, audio bitrate
3. Calculate target video bitrate: `(target_size * 8) / duration - audio_bitrate`
4. If bitrate < 100kbps, downscale resolution (720p -> 480p -> 360p)
5. Two-pass FFmpeg encoding:
   - Pass 1: analysis pass (`-pass 1 -f null`)
   - Pass 2: encode with calculated bitrate, H.264 video + AAC audio at 128kbps
6. Output always as MP4 for compatibility
7. Return `{data, size, skipped, message}`

Skip if original size <= target size.

## Audio Compressor

New file: `squishfile/compressor/audio.py`

Function: `compress_audio(data, mime, target_size) -> dict`

Strategy:
1. Write input bytes to temp file
2. Probe with FFmpeg to get duration
3. Calculate target bitrate: `(target_size * 8) / duration`
4. Clamp bitrate: min 32kbps, max 320kbps
5. Encode with libmp3lame to MP3
6. Return `{data, size, skipped, message}`

Skip if original size <= target size.

## Engine Changes

Add two new branches in `compress_file()`:
- `category == "video"` -> `compress_video()`
- `category == "audio"` -> `compress_audio()`

No ML predictor changes (predictor is image-only, used for logging).

## API Changes

- Upload size limit: increase from 100MB to 500MB
- Upload route: extract duration via FFmpeg probe for video/audio (instead of width/height)
- Compress and download endpoints: no changes needed

## Frontend Changes

- DropZone: accept `video/mp4,video/webm,video/quicktime,audio/mpeg,audio/wav`
- FileEntry type: add `"video" | "audio"` to category, add optional `duration` field
- SizeControl: add larger presets for video (10MB, 25MB, 50MB) shown dynamically
- File list: show duration for video/audio instead of dimensions

## FFmpeg Dependency

- Required as system dependency (must be in PATH)
- Add startup check that logs warning if FFmpeg not found
- Document installation instructions

## Files to Create/Modify

**New files:**
- `squishfile/compressor/video.py`
- `squishfile/compressor/audio.py`
- `tests/test_video_compressor.py`
- `tests/test_audio_compressor.py`

**Modified files:**
- `squishfile/detector.py` — add video/audio MIME maps
- `squishfile/compressor/engine.py` — add video/audio dispatch
- `squishfile/routes/upload.py` — size limit, duration extraction
- `squishfile/main.py` — FFmpeg check on startup
- `pyproject.toml` — no new Python deps (FFmpeg is system-level)
- `frontend/src/App.tsx` — FileEntry type update
- `frontend/src/components/DropZone.tsx` — accept new types
- `frontend/src/components/SizeControl.tsx` — dynamic presets
- `frontend/src/components/UploadPage.tsx` — show duration
- `frontend/src/components/CompressPage.tsx` — show duration
- `frontend/src/components/DownloadPage.tsx` — show duration
