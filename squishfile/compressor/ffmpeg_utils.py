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
