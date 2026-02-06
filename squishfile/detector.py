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

SUPPORTED = {**SUPPORTED_IMAGES, **SUPPORTED_PDFS}


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
