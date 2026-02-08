"""Tests for audio compression via FFmpeg."""
import struct
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
