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
            "output_mime": "audio/mpeg",
            "output_ext": ".mp3",
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
