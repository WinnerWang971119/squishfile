import io
from PIL import Image

QUALITY_FORMATS = {"image/jpeg", "image/webp"}


def compress_image(
    data: bytes,
    mime: str,
    target_size: int,
) -> dict:
    original_size = len(data)

    if original_size <= target_size:
        return {"data": data, "size": original_size, "skipped": True}

    if mime in QUALITY_FORMATS:
        return _compress_with_quality(data, mime, target_size)

    if mime == "image/png":
        return _compress_png(data, target_size)

    if mime == "image/gif":
        return _compress_gif(data, target_size)

    # Fallback: return original
    return {"data": data, "size": original_size, "skipped": True}


def _compress_with_quality(
    data: bytes, mime: str, target_size: int
) -> dict:
    fmt = "JPEG" if mime == "image/jpeg" else "WEBP"
    img = Image.open(io.BytesIO(data))

    if img.mode == "RGBA" and fmt == "JPEG":
        img = img.convert("RGB")

    # Estimate starting quality from size ratio
    ratio = target_size / len(data)
    quality = max(5, min(95, int(ratio * 85)))

    lo, hi = 5, 95
    best_data = None
    best_size = float("inf")

    # Binary search for optimal quality (max 10 iterations)
    for _ in range(10):
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=quality, optimize=True)
        result_size = buf.tell()

        if abs(result_size - target_size) / target_size <= 0.05:
            return {"data": buf.getvalue(), "size": result_size, "skipped": False}

        if result_size <= target_size and (
            best_data is None or result_size > best_size
        ):
            best_data = buf.getvalue()
            best_size = result_size

        if result_size > target_size:
            hi = quality - 1
        else:
            lo = quality + 1

        if lo > hi:
            break
        quality = (lo + hi) // 2

    # Fallback: reduce resolution if quality alone isn't enough
    if best_data is None or best_size > target_size * 1.05:
        return _compress_with_resize(img, fmt, target_size)

    return {"data": best_data, "size": best_size, "skipped": False}


def _compress_with_resize(
    img: Image.Image, fmt: str, target_size: int
) -> dict:
    scale = 0.9
    for _ in range(10):
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format=fmt, quality=60, optimize=True)
        result_size = buf.tell()

        if result_size <= target_size * 1.05:
            return {"data": buf.getvalue(), "size": result_size, "skipped": False}

        scale *= 0.8

    # Return best effort
    return {"data": buf.getvalue(), "size": buf.tell(), "skipped": False}


def _compress_png(data: bytes, target_size: int) -> dict:
    img = Image.open(io.BytesIO(data))

    # Try converting to JPEG (lossy) to hit target
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    else:
        img = img.convert("RGB")

    return _compress_with_quality(
        _image_to_bytes(img, "JPEG", 95), "image/jpeg", target_size
    )


def _compress_gif(data: bytes, target_size: int) -> dict:
    img = Image.open(io.BytesIO(data))
    # Convert first frame to JPEG
    rgb = img.convert("RGB")
    return _compress_with_quality(
        _image_to_bytes(rgb, "JPEG", 95), "image/jpeg", target_size
    )


def _image_to_bytes(img: Image.Image, fmt: str, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality)
    buf.seek(0)
    return buf.read()
