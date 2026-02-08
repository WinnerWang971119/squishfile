"""Video compression using FFmpeg two-pass encoding (via imageio-ffmpeg)."""
import os
import shutil
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

    video_bitrate_raw_kbps = video_bitrate // 1000
    video_bitrate_kbps = max(MIN_BITRATE_KBPS, video_bitrate_raw_kbps)

    # Determine if we need to scale down based on unclamped bitrate
    scale_filter = None
    if video_bitrate_raw_kbps < MIN_BITRATE_KBPS:
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
    passlog_dir = tempfile.mkdtemp(prefix="ffmpeg2pass_")
    passlog_prefix = os.path.join(passlog_dir, "passlog")

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
            "output_mime": "video/mp4",
            "output_ext": ".mp4",
        }
    except subprocess.TimeoutExpired:
        return {"data": data, "size": original_size, "skipped": True,
                "message": "Video compression timed out"}
    finally:
        for p in (in_path, out_path):
            if os.path.exists(p):
                os.unlink(p)
        # Clean up pass log directory
        if os.path.exists(passlog_dir):
            shutil.rmtree(passlog_dir, ignore_errors=True)


def _ext_for_mime(mime: str) -> str:
    """Return file extension for a given video MIME type."""
    return {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
    }.get(mime, ".bin")
