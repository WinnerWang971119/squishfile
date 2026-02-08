import uuid
import io
from fastapi import APIRouter, UploadFile, HTTPException
from PIL import Image
from squishfile.detector import detect_file_type
from squishfile.compressor.ffmpeg_utils import probe_media

router = APIRouter(prefix="/api")

# In-memory store for uploaded files (per session)
file_store: dict[str, dict] = {}


@router.post("/upload")
async def upload_file(file: UploadFile):
    data = await file.read()

    info = detect_file_type(data, file.filename or "unknown")

    if info["category"] == "unsupported":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {info['mime']}",
        )

    file_id = str(uuid.uuid4())[:8]
    entry = {
        "id": file_id,
        "data": data,
        **info,
    }

    # Extract image dimensions
    if info["category"] == "image" and info["mime"] != "image/svg+xml":
        img = Image.open(io.BytesIO(data))
        entry["width"] = img.width
        entry["height"] = img.height

    # Extract media duration for video/audio
    if info["category"] in ("video", "audio"):
        probe = probe_media(data)
        if probe and "format" in probe:
            entry["duration"] = float(probe["format"].get("duration", 0))

    file_store[file_id] = entry

    # Return info without raw data
    return {k: v for k, v in entry.items() if k != "data"}
