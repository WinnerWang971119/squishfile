# squishfile/compressor/engine.py
from squishfile.compressor.image import compress_image
from squishfile.compressor.pdf import compress_pdf
from squishfile.compressor.video import compress_video
from squishfile.compressor.audio import compress_audio
from squishfile.compressor.predictor import predict_quality


def compress_file(
    data: bytes,
    mime: str,
    category: str,
    target_size: int,
    width: int = 0,
    height: int = 0,
) -> dict:
    original_size = len(data)

    if original_size <= target_size:
        return {
            "data": data,
            "size": original_size,
            "original_size": original_size,
            "skipped": True,
            "message": "File is already smaller than target!",
        }

    # Get ML-predicted quality for logging/future use
    if category == "image":
        predicted_q = predict_quality(
            file_type=mime,
            original_size=original_size,
            target_size=target_size,
            width=width or 1920,
            height=height or 1080,
        )

    if category == "image":
        result = compress_image(data, mime, target_size)
    elif category == "pdf":
        result = compress_pdf(data, target_size)
    elif category == "video":
        result = compress_video(data, mime, target_size)
    elif category == "audio":
        result = compress_audio(data, mime, target_size)
    else:
        return {
            "data": data,
            "size": original_size,
            "original_size": original_size,
            "skipped": True,
            "message": "Unsupported file type",
        }

    result["original_size"] = original_size

    if result["size"] > target_size * 1.05 and not result["skipped"]:
        result["message"] = (
            f"Best we could do: {result['size'] // 1024}KB "
            f"(target was {target_size // 1024}KB)"
        )

    return result
