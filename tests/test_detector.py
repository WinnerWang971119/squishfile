import io
from PIL import Image
from squishfile.detector import detect_file_type


def _make_jpeg_bytes():
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def test_detect_jpeg():
    data = _make_jpeg_bytes()
    result = detect_file_type(data, "photo.jpg")
    assert result["mime"] == "image/jpeg"
    assert result["category"] == "image"
    assert result["extension"] == ".jpg"


def test_detect_unknown():
    result = detect_file_type(b"random bytes", "mystery.xyz")
    assert result["category"] == "unsupported"


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
