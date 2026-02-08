"""Tests for video compression via FFmpeg."""
import subprocess
import tempfile
import os
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
