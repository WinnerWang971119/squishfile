"""MIME-based file type detector for SquishFile."""

import magic

SUPPORTED_IMAGES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}

SUPPORTED_PDFS = {
    "application/pdf": ".pdf",
}

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
