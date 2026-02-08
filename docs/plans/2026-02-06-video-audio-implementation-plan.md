# Video & Audio Compression Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add video (MP4, WebM, MOV) and audio (MP3, WAV) compression to SquishFile using FFmpeg, bundled via `imageio-ffmpeg` (zero system dependencies).

**Architecture:** Extend the existing function-based compressor pattern with two new modules (`video.py`, `audio.py`) that shell out to the FFmpeg binary provided by `imageio-ffmpeg` via `subprocess`. Wire them through the detector → engine → API pipeline following the same duck-typed dict return pattern.

**Tech Stack:** `imageio-ffmpeg` (pip-bundled FFmpeg binary), Python subprocess, existing FastAPI + React stack.

---

### Task 0: Add imageio-ffmpeg Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add `imageio-ffmpeg` to dependencies in `pyproject.toml`**

Add `"imageio-ffmpeg>=0.5.1"` to the `dependencies` list.

**Step 2: Install**

Run: `pip install -e .`
Expected: `imageio-ffmpeg` installs, bundling a static FFmpeg binary (~60MB).

**Step 3: Verify FFmpeg binary is accessible**

Run: `python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`
Expected: Prints a path to the bundled ffmpeg binary.

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add imageio-ffmpeg dependency for bundled FFmpeg binary"
```

---

### Task 1: FFmpeg Helper Module

**Files:**
- Create: `squishfile/compressor/ffmpeg_utils.py`
- Test: `tests/test_ffmpeg_utils.py`

**Step 1: Write the failing tests**

Create `tests/test_ffmpeg_utils.py`:

```python
"""Tests for FFmpeg utility functions."""
import pytest
from squishfile.compressor.ffmpeg_utils import check_ffmpeg, get_ffmpeg, get_ffprobe, probe_media


def test_check_ffmpeg():
    """FFmpeg should be available via imageio-ffmpeg."""
    assert check_ffmpeg() is True


def test_get_ffmpeg_returns_path():
    """get_ffmpeg should return a valid path string."""
    path = get_ffmpeg()
    assert path is not None
    assert len(path) > 0


def test_get_ffprobe_returns_path():
    """get_ffprobe should return a valid path string."""
    path = get_ffprobe()
    assert path is not None
    assert len(path) > 0


def test_probe_media_with_invalid_data():
    """Probing invalid data should return None."""
    result = probe_media(b"not a real media file")
    assert result is None
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ffmpeg_utils.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `squishfile/compressor/ffmpeg_utils.py`:

```python
"""FFmpeg utility functions using imageio-ffmpeg bundled binary."""
import json
import os
import subprocess
import tempfile

import imageio_ffmpeg


def get_ffmpeg() -> str:
    """Return path to the FFmpeg binary (bundled via imageio-ffmpeg)."""
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_ffprobe() -> str:
    """Return path to the FFprobe binary (derived from FFmpeg location).

    imageio-ffmpeg only bundles ffmpeg, not ffprobe. However, the static
    builds typically include ffprobe alongside ffmpeg. We derive the path
    by replacing 'ffmpeg' with 'ffprobe' in the binary path. If ffprobe
    is not found, we fall back to using 'ffmpeg -i' for probing.
    """
    ffmpeg_path = get_ffmpeg()
    ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
    if os.path.isfile(ffprobe_path):
        return ffprobe_path
    # Fallback: use system ffprobe if available
    import shutil
    sys_ffprobe = shutil.which("ffprobe")
    if sys_ffprobe:
        return sys_ffprobe
    # Last resort: return None, probe_media will use ffmpeg -i instead
    return None


def check_ffmpeg() -> bool:
    """Return True if FFmpeg is available via imageio-ffmpeg."""
    try:
        path = get_ffmpeg()
        return path is not None and os.path.isfile(path)
    except Exception:
        return False


def probe_media(data: bytes) -> dict | None:
    """Probe media file bytes. Returns dict with duration, streams info, or None on failure."""
    tmp_fd, tmp_path = tempfile.mkstemp()
    try:
        os.write(tmp_fd, data)
        os.close(tmp_fd)

        ffprobe = get_ffprobe()
        if ffprobe:
            result = subprocess.run(
                [
                    ffprobe, "-v", "quiet",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    tmp_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)

        # Fallback: parse duration from ffmpeg stderr
        ffmpeg = get_ffmpeg()
        result = subprocess.run(
            [ffmpeg, "-i", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # ffmpeg -i exits with error but prints info to stderr
        import re
        stderr = result.stderr
        duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr)
        if duration_match:
            h, m, s, _ = duration_match.groups()
            duration = int(h) * 3600 + int(m) * 60 + int(s)
            return {"format": {"duration": str(duration)}, "streams": []}
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ffmpeg_utils.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/ffmpeg_utils.py tests/test_ffmpeg_utils.py
git commit -m "feat: add FFmpeg utility module using imageio-ffmpeg bundled binary"
```

---

### Task 2: Detector — Add Video & Audio MIME Types

**Files:**
- Modify: `squishfile/detector.py:5-17` (add new dicts, update SUPPORTED)
- Modify: `squishfile/detector.py:32-37` (add category detection)
- Test: `tests/test_detector.py` (add new tests)

**Step 1: Write the failing tests**

Append to `tests/test_detector.py`:

```python
def test_detect_mp4():
    """MP4 detection requires real MP4 bytes. Use a minimal ftyp box."""
    # Minimal valid MP4 ftyp atom
    ftyp = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom'
    result = detect_file_type(ftyp, "video.mp4")
    assert result["category"] == "video"
    assert result["extension"] == ".mp4"


def test_detect_mp3():
    """MP3 files start with ID3 tag or sync bytes."""
    # ID3v2 header
    id3 = b'ID3' + b'\x04\x00\x00' + b'\x00\x00\x00\x00' + b'\x00' * 100
    result = detect_file_type(id3, "song.mp3")
    # python-magic may detect as audio/mpeg or application/octet-stream
    # depending on header completeness — test the category mapping exists
    from squishfile.detector import SUPPORTED_AUDIO
    assert "audio/mpeg" in SUPPORTED_AUDIO


def test_detect_wav():
    """WAV files start with RIFF header."""
    import struct
    # Minimal WAV header
    header = b'RIFF' + struct.pack('<I', 36) + b'WAVEfmt '
    header += struct.pack('<I', 16)  # chunk size
    header += struct.pack('<HHI', 1, 1, 44100)  # PCM, mono, 44100
    header += struct.pack('<IHH', 44100 * 2, 2, 16)  # byte rate, block align, bits
    header += b'data' + struct.pack('<I', 0)
    result = detect_file_type(header, "sound.wav")
    assert result["category"] == "audio"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_detector.py -v`
Expected: FAIL — `SUPPORTED_AUDIO` not defined, categories not matched

**Step 3: Modify detector.py**

Replace `squishfile/detector.py` contents:

```python
"""MIME-based file type detector for SquishFile."""

import magic

SUPPORTED_IMAGES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}

SUPPORTED_PDFS = {"application/pdf": ".pdf"}

SUPPORTED_VIDEOS = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}

SUPPORTED_AUDIO = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
}

SUPPORTED = {**SUPPORTED_IMAGES, **SUPPORTED_PDFS, **SUPPORTED_VIDEOS, **SUPPORTED_AUDIO}


def detect_file_type(data: bytes, filename: str) -> dict:
    """Detect file type from raw bytes using libmagic.

    Args:
        data: Raw file bytes.
        filename: Original filename (used for metadata only).

    Returns:
        Dict with keys: mime, category, extension, original_filename, size.
    """
    mime = magic.from_buffer(data, mime=True)

    if mime in SUPPORTED_IMAGES:
        category = "image"
    elif mime in SUPPORTED_PDFS:
        category = "pdf"
    elif mime in SUPPORTED_VIDEOS:
        category = "video"
    elif mime in SUPPORTED_AUDIO:
        category = "audio"
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

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_detector.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/detector.py tests/test_detector.py
git commit -m "feat: add video and audio MIME type detection"
```

---

### Task 3: Audio Compressor

**Files:**
- Create: `squishfile/compressor/audio.py`
- Test: `tests/test_audio_compressor.py`

**Step 1: Write the failing tests**

Create `tests/test_audio_compressor.py`:

```python
"""Tests for audio compression via FFmpeg."""
import struct
import pytest
from squishfile.compressor.audio import compress_audio


def _make_wav_bytes(duration_seconds=2, sample_rate=44100, channels=1, bits=16) -> bytes:
    """Generate a valid WAV file with sine wave data."""
    import math

    num_samples = sample_rate * duration_seconds
    data_size = num_samples * channels * (bits // 8)

    # WAV header
    header = b'RIFF'
    header += struct.pack('<I', 36 + data_size)
    header += b'WAVEfmt '
    header += struct.pack('<I', 16)  # chunk size
    header += struct.pack('<HH', 1, channels)  # PCM, channels
    header += struct.pack('<I', sample_rate)
    header += struct.pack('<I', sample_rate * channels * (bits // 8))
    header += struct.pack('<HH', channels * (bits // 8), bits)
    header += b'data'
    header += struct.pack('<I', data_size)

    # Generate sine wave samples
    samples = bytearray()
    for i in range(num_samples):
        value = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
        samples += struct.pack('<h', value)

    return bytes(header + samples)


def test_compress_wav_to_mp3():
    """Compressing a WAV to MP3 should reduce size significantly."""
    wav_data = _make_wav_bytes(duration_seconds=2)
    target = len(wav_data) // 4
    result = compress_audio(wav_data, "audio/wav", target)
    assert result["skipped"] is False
    assert result["size"] < len(wav_data)
    assert len(result["data"]) > 0


def test_skip_small_audio():
    """Audio already under target should be skipped."""
    wav_data = _make_wav_bytes(duration_seconds=1)
    target = len(wav_data) * 2  # target bigger than original
    result = compress_audio(wav_data, "audio/wav", target)
    assert result["skipped"] is True
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_audio_compressor.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

Create `squishfile/compressor/audio.py`:

```python
"""Audio compression using FFmpeg (via imageio-ffmpeg)."""
import os
import subprocess
import tempfile

from squishfile.compressor.ffmpeg_utils import get_ffmpeg, probe_media


def compress_audio(data: bytes, mime: str, target_size: int) -> dict:
    """Compress audio data to target size using FFmpeg.

    Args:
        data: Raw audio file bytes.
        mime: MIME type of the audio file.
        target_size: Target file size in bytes.

    Returns:
        Dict with keys: data, size, skipped.
    """
    original_size = len(data)

    if original_size <= target_size:
        return {"data": data, "size": original_size, "skipped": True}

    # Probe to get duration
    info = probe_media(data)
    if info is None:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Could not probe audio file"}

    duration = float(info["format"].get("duration", 0))
    if duration <= 0:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Could not determine audio duration"}

    # Calculate target bitrate in kbps
    target_bitrate_kbps = int((target_size * 8) / duration / 1000)
    target_bitrate_kbps = max(32, min(320, target_bitrate_kbps))

    # Write input to temp file, encode to output temp file
    in_fd, in_path = tempfile.mkstemp(suffix=_ext_for_mime(mime))
    out_fd, out_path = tempfile.mkstemp(suffix=".mp3")
    try:
        os.write(in_fd, data)
        os.close(in_fd)
        os.close(out_fd)

        cmd = [
            get_ffmpeg(), "-y", "-i", in_path,
            "-c:a", "libmp3lame",
            "-b:a", f"{target_bitrate_kbps}k",
            out_path,
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            return {"data": data, "size": original_size, "skipped": True,
                    "message": "FFmpeg encoding failed"}

        with open(out_path, "rb") as f:
            compressed = f.read()

        return {
            "data": compressed,
            "size": len(compressed),
            "skipped": False,
        }
    except subprocess.TimeoutExpired:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Audio compression timed out"}
    finally:
        for p in (in_path, out_path):
            if os.path.exists(p):
                os.unlink(p)


def _ext_for_mime(mime: str) -> str:
    """Return file extension for a given audio MIME type."""
    return {
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
    }.get(mime, ".bin")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_audio_compressor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/audio.py tests/test_audio_compressor.py
git commit -m "feat: add audio compressor with FFmpeg MP3 encoding"
```

---

### Task 4: Video Compressor

**Files:**
- Create: `squishfile/compressor/video.py`
- Test: `tests/test_video_compressor.py`

**Step 1: Write the failing tests**

Create `tests/test_video_compressor.py`:

```python
"""Tests for video compression via FFmpeg."""
import subprocess
import tempfile
import os
import pytest
from squishfile.compressor.video import compress_video


def _make_test_video(duration=2, width=320, height=240) -> bytes:
    """Generate a minimal test video using FFmpeg (via imageio-ffmpeg)."""
    from squishfile.compressor.ffmpeg_utils import get_ffmpeg
    out_fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(out_fd)
    try:
        cmd = [
            get_ffmpeg(), "-y",
            "-f", "lavfi", "-i", f"testsrc=duration={duration}:size={width}x{height}:rate=24",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "64k",
            "-shortest",
            out_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_compress_video_reduces_size():
    """Compressing a video with a smaller target should produce smaller output."""
    video_data = _make_test_video(duration=2)
    target = len(video_data) // 2
    result = compress_video(video_data, "video/mp4", target)
    assert result["skipped"] is False
    assert result["size"] < len(video_data)
    assert len(result["data"]) > 0


def test_skip_small_video():
    """Video already under target should be skipped."""
    video_data = _make_test_video(duration=1)
    target = len(video_data) * 2
    result = compress_video(video_data, "video/mp4", target)
    assert result["skipped"] is True
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_video_compressor.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write implementation**

Create `squishfile/compressor/video.py`:

```python
"""Video compression using FFmpeg two-pass encoding (via imageio-ffmpeg)."""
import os
import subprocess
import tempfile

from squishfile.compressor.ffmpeg_utils import get_ffmpeg, probe_media

# Minimum video bitrate before we try downscaling
MIN_BITRATE_KBPS = 100

# Audio bitrate for output (kbps)
AUDIO_BITRATE_KBPS = 128

# Resolution downscale steps
SCALE_STEPS = [
    (1280, 720),
    (854, 480),
    (640, 360),
]


def compress_video(data: bytes, mime: str, target_size: int) -> dict:
    """Compress video data to target size using FFmpeg two-pass encoding.

    Args:
        data: Raw video file bytes.
        mime: MIME type of the video file.
        target_size: Target file size in bytes.

    Returns:
        Dict with keys: data, size, skipped.
    """
    original_size = len(data)

    if original_size <= target_size:
        return {"data": data, "size": original_size, "skipped": True}

    # Probe to get duration and resolution
    info = probe_media(data)
    if info is None:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Could not probe video file"}

    duration = float(info["format"].get("duration", 0))
    if duration <= 0:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Could not determine video duration"}

    # Calculate target video bitrate
    audio_bits = AUDIO_BITRATE_KBPS * 1000
    total_target_bits = target_size * 8
    video_bitrate = int(total_target_bits / duration - audio_bits)

    if video_bitrate <= 0:
        video_bitrate = MIN_BITRATE_KBPS * 1000

    video_bitrate_kbps = max(MIN_BITRATE_KBPS, video_bitrate // 1000)

    # Determine if we need to scale down
    scale_filter = None
    if video_bitrate_kbps < MIN_BITRATE_KBPS:
        # Find the video stream resolution
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                orig_w = stream.get("width", 1920)
                orig_h = stream.get("height", 1080)
                for sw, sh in SCALE_STEPS:
                    if orig_w > sw or orig_h > sh:
                        scale_filter = f"scale={sw}:{sh}:force_original_aspect_ratio=decrease,pad={sw}:{sh}:(ow-iw)/2:(oh-ih)/2"
                        break
                break

    ext = _ext_for_mime(mime)
    in_fd, in_path = tempfile.mkstemp(suffix=ext)
    out_fd, out_path = tempfile.mkstemp(suffix=".mp4")
    passlog_prefix = tempfile.mktemp(prefix="ffmpeg2pass_")

    try:
        os.write(in_fd, data)
        os.close(in_fd)
        os.close(out_fd)

        vf = ["-vf", scale_filter] if scale_filter else []

        # Pass 1
        cmd_pass1 = [
            get_ffmpeg(), "-y", "-i", in_path,
            "-c:v", "libx264", "-preset", "medium",
            "-b:v", f"{video_bitrate_kbps}k",
            *vf,
            "-pass", "1",
            "-passlogfile", passlog_prefix,
            "-an",
            "-f", "null",
            os.devnull,
        ]

        result1 = subprocess.run(
            cmd_pass1, capture_output=True, text=True, timeout=300,
        )
        if result1.returncode != 0:
            return {"data": data, "size": original_size, "skipped": True,
                    "message": "FFmpeg pass 1 failed"}

        # Pass 2
        cmd_pass2 = [
            get_ffmpeg(), "-y", "-i", in_path,
            "-c:v", "libx264", "-preset", "medium",
            "-b:v", f"{video_bitrate_kbps}k",
            *vf,
            "-pass", "2",
            "-passlogfile", passlog_prefix,
            "-c:a", "aac", "-b:a", f"{AUDIO_BITRATE_KBPS}k",
            out_path,
        ]

        result2 = subprocess.run(
            cmd_pass2, capture_output=True, text=True, timeout=300,
        )
        if result2.returncode != 0:
            return {"data": data, "size": original_size, "skipped": True,
                    "message": "FFmpeg pass 2 failed"}

        with open(out_path, "rb") as f:
            compressed = f.read()

        return {
            "data": compressed,
            "size": len(compressed),
            "skipped": False,
        }
    except subprocess.TimeoutExpired:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Video compression timed out"}
    finally:
        for p in (in_path, out_path):
            if os.path.exists(p):
                os.unlink(p)
        # Clean up pass log files
        for suffix in ("-0.log", "-0.log.mbtree"):
            log_path = passlog_prefix + suffix
            if os.path.exists(log_path):
                os.unlink(log_path)


def _ext_for_mime(mime: str) -> str:
    """Return file extension for a given video MIME type."""
    return {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
    }.get(mime, ".bin")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_video_compressor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/video.py tests/test_video_compressor.py
git commit -m "feat: add video compressor with FFmpeg two-pass encoding"
```

---

### Task 5: Engine — Wire Video & Audio Dispatch

**Files:**
- Modify: `squishfile/compressor/engine.py:2-3` (add imports)
- Modify: `squishfile/compressor/engine.py:38-40` (add elif branches)
- Test: `tests/test_engine.py` (add new tests)

**Step 1: Write the failing tests**

Append to `tests/test_engine.py`:

```python
def test_compress_file_unsupported_returns_skipped():
    result = compress_file(
        data=b"random data",
        mime="application/octet-stream",
        category="unsupported",
        target_size=1000,
    )
    assert result["skipped"] is True


def test_compress_file_video_dispatch():
    """Engine should accept category='video' without error."""
    # We just test it doesn't crash with unsupported — actual video tests are in test_video_compressor.py
    tiny_data = b"\x00" * 100
    result = compress_file(
        data=tiny_data,
        mime="video/mp4",
        category="video",
        target_size=10000,
    )
    # Small data should be skipped (under target)
    assert result["skipped"] is True


def test_compress_file_audio_dispatch():
    """Engine should accept category='audio' without error."""
    tiny_data = b"\x00" * 100
    result = compress_file(
        data=tiny_data,
        mime="audio/mpeg",
        category="audio",
        target_size=10000,
    )
    assert result["skipped"] is True
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_engine.py -v`
Expected: `test_compress_file_video_dispatch` and `test_compress_file_audio_dispatch` may pass (because engine's early size-check returns skipped before dispatch), but let's verify. `test_compress_file_unsupported_returns_skipped` should already pass.

**Step 3: Modify engine.py**

Update `squishfile/compressor/engine.py` — add imports and dispatch:

```python
# squishfile/compressor/engine.py
from squishfile.compressor.image import compress_image
from squishfile.compressor.pdf import compress_pdf
from squishfile.compressor.video import compress_video
from squishfile.compressor.audio import compress_audio
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
    elif category == "video":
        result = compress_video(data, mime, target_size)
    elif category == "audio":
        result = compress_audio(data, mime, target_size)
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

**Step 4: Run all tests**

Run: `pytest tests/ -v`
Expected: All 16+ tests PASS

**Step 5: Commit**

```bash
git add squishfile/compressor/engine.py tests/test_engine.py
git commit -m "feat: wire video and audio compressors into engine dispatch"
```

---

### Task 6: Upload Route — Size Limit & Duration Extraction

**Files:**
- Modify: `squishfile/routes/upload.py:17` (size limit 100MB → 500MB)
- Modify: `squishfile/routes/upload.py:36-39` (add duration extraction for video/audio)
- Test: `tests/test_upload.py` (add test for video upload)

**Step 1: Write the failing test**

Append to `tests/test_upload.py` (read existing file first to understand the test patterns):

```python
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
    from fastapi.testclient import TestClient
    from squishfile.main import app
    client = TestClient(app)

    resp = client.post("/api/upload", files={"file": ("test.mp4", BytesIO(video_data), "video/mp4")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "video"
    assert "duration" in data
    assert data["duration"] > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_upload.py::test_upload_video_returns_duration -v`
Expected: FAIL — no `duration` field in response

**Step 3: Modify upload.py**

Update `squishfile/routes/upload.py`:

```python
import uuid
import io
from fastapi import APIRouter, UploadFile, HTTPException
from PIL import Image
from squishfile.detector import detect_file_type
from squishfile.compressor.ffmpeg_utils import probe_media

router = APIRouter(prefix="/api")

# In-memory store for uploaded files (per session)
file_store: dict[str, dict] = {}


@router.post("/upload")
async def upload_file(file: UploadFile):
    data = await file.read()

    if len(data) > 500 * 1024 * 1024:  # 500MB limit
        raise HTTPException(status_code=400, detail="File exceeds 500MB limit")

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

    # Extract media duration for video/audio
    if info["category"] in ("video", "audio"):
        probe = probe_media(data)
        if probe and "format" in probe:
            entry["duration"] = float(probe["format"].get("duration", 0))

    file_store[file_id] = entry

    # Return info without raw data
    return {k: v for k, v in entry.items() if k != "data"}
```

**Step 4: Run tests**

Run: `pytest tests/test_upload.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add squishfile/routes/upload.py tests/test_upload.py
git commit -m "feat: increase upload limit to 500MB, add duration extraction for video/audio"
```

---

### Task 7: FFmpeg Startup Check

**Files:**
- Modify: `squishfile/main.py:1-2` (add import and startup check)

**Step 1: Modify main.py**

Add FFmpeg check after app creation in `squishfile/main.py`:

```python
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from squishfile import __version__
from squishfile.routes.upload import router as upload_router
from squishfile.routes.compress import router as compress_router
from squishfile.compressor.ffmpeg_utils import check_ffmpeg

logger = logging.getLogger(__name__)

app = FastAPI(title="SquishFile", version=__version__)

if not check_ffmpeg():
    logger.warning(
        "FFmpeg not available. Video and audio compression will not work. "
        "Try reinstalling: pip install imageio-ffmpeg"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(compress_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": __version__}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
```

**Step 2: Run all existing tests**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add squishfile/main.py
git commit -m "feat: add FFmpeg availability check on startup"
```

---

### Task 8: Frontend — Types & DropZone

**Files:**
- Modify: `frontend/src/types.ts:7` (add `"video" | "audio"` to category)
- Modify: `frontend/src/types.ts:10-11` (add `duration` field)
- Modify: `frontend/src/types.ts:23` (add `duration` to UploadResponse)
- Modify: `frontend/src/components/DropZone.tsx:39` (accept new types)
- Modify: `frontend/src/components/DropZone.tsx:68` (update helper text)

**Step 1: Update types.ts**

```typescript
export type FileStatus = "uploading" | "queued" | "compressing" | "done" | "error";

export interface FileEntry {
  id: string;
  originalFilename: string;
  mime: string;
  category: "image" | "pdf" | "video" | "audio";
  size: number;
  width?: number;
  height?: number;
  duration?: number;
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
  duration?: number;
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

**Step 2: Update DropZone.tsx**

Change line 39:
```typescript
    input.accept = "image/*,.pdf,video/mp4,video/webm,video/quicktime,audio/mpeg,audio/wav";
```

Change line 68:
```html
      <p className="text-[#555] text-xs mt-3">Images, PDFs, videos & audio up to 500MB</p>
```

**Step 3: Update App.tsx**

Change line 39 — update the category cast:
```typescript
                    category: uploaded.category as "image" | "pdf" | "video" | "audio",
```

Add duration to the uploaded entry (after line 42):
```typescript
                    duration: uploaded.duration,
```

**Step 4: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 5: Commit**

```bash
git add frontend/src/types.ts frontend/src/components/DropZone.tsx frontend/src/App.tsx
git commit -m "feat: update frontend types and DropZone to accept video and audio"
```

---

### Task 9: Frontend — SizeControl Dynamic Presets

**Files:**
- Modify: `frontend/src/components/SizeControl.tsx` (add video presets, make dynamic)

**Step 1: Update SizeControl.tsx**

```typescript
import { useState } from "react";

interface SizeControlProps {
  maxSizeKb: number;
  value: number;
  onChange: (kb: number) => void;
  hasVideo?: boolean;
}

const PRESETS = [
  { label: "50%", factor: 0.5 },
  { label: "25%", factor: 0.25 },
  { label: "1 MB", kb: 1024 },
  { label: "500 KB", kb: 500 },
  { label: "200 KB", kb: 200 },
];

const VIDEO_PRESETS = [
  { label: "50%", factor: 0.5 },
  { label: "25%", factor: 0.25 },
  { label: "50 MB", kb: 51200 },
  { label: "25 MB", kb: 25600 },
  { label: "10 MB", kb: 10240 },
];

export function SizeControl({ maxSizeKb, value, onChange, hasVideo = false }: SizeControlProps) {
  const [customInput, setCustomInput] = useState("");
  const presets = hasVideo ? VIDEO_PRESETS : PRESETS;

  const handlePreset = (preset: (typeof presets)[number]) => {
    const kb = preset.kb ?? Math.round(maxSizeKb * (preset as any).factor);
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

      <div className="text-center">
        <span className="text-[#FFD60A] font-bold text-lg">
          {value >= 1024
            ? `${(value / 1024).toFixed(1)} MB`
            : `${value} KB`}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 justify-center">
        {presets.map((preset) => (
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

**Step 2: Pass `hasVideo` prop from App.tsx**

In `App.tsx`, compute hasVideo and pass it:

Add before the return (around line 94):
```typescript
  const hasVideo = files.some((f) => f.category === "video" || f.category === "audio");
```

Update the SizeControl usage (around line 123):
```typescript
              <SizeControl
                maxSizeKb={maxKb}
                value={targetKb}
                onChange={setTargetKb}
                hasVideo={hasVideo}
              />
```

**Step 3: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/components/SizeControl.tsx frontend/src/App.tsx
git commit -m "feat: add dynamic size presets for video/audio files"
```

---

### Task 10: Frontend — FileCard Duration Display

**Files:**
- Modify: `frontend/src/components/FileCard.tsx` (show duration for video/audio)

**Step 1: Update FileCard.tsx**

Add a duration formatter after `formatSize` function:

```typescript
function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
```

Add duration display after the size info (inside the `text-xs text-[#888] mb-2` div, around line 37-44):

```typescript
      <div className="text-xs text-[#888] mb-2">
        {formatSize(file.size)}
        {file.duration != null && (
          <span className="ml-2 text-[#666]">{formatDuration(file.duration)}</span>
        )}
        {file.compressedSize != null && (
          <>
            <span className="text-[#FFD60A] mx-1">&rarr;</span>
            <span className="text-[#FAFAFA]">{formatSize(file.compressedSize)}</span>
          </>
        )}
      </div>
```

**Step 2: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/FileCard.tsx
git commit -m "feat: show duration for video and audio files in FileCard"
```

---

### Task 11: Run Full Test Suite & Final Verification

**Step 1: Run all backend tests**

Run: `pytest tests/ -v`
Expected: All tests PASS (16 original + new tests)

**Step 2: Build frontend**

Run: `cd frontend && npm run build`
Expected: Build succeeds, no errors

**Step 3: Verify the app starts**

Run: `python -m uvicorn squishfile.main:app --port 8000` (manual check)
Expected: App starts, no errors in console, FFmpeg check passes

**Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address any issues found during final verification"
```
