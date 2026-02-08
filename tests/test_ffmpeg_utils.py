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


def test_get_ffprobe_returns_path_or_none():
    """get_ffprobe may return a path or None if ffprobe is not bundled."""
    path = get_ffprobe()
    # ffprobe may not be bundled with imageio-ffmpeg; None is acceptable
    # probe_media has a fallback using ffmpeg -i
    assert path is None or len(path) > 0


def test_probe_media_with_invalid_data():
    """Probing invalid data should return None."""
    result = probe_media(b"not a real media file")
    assert result is None
