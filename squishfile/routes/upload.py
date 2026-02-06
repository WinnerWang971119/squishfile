import uuid
import io
from fastapi import APIRouter, UploadFile, HTTPException
from PIL import Image
from squishfile.detector import detect_file_type

router = APIRouter(prefix="/api")

# In-memory store for uploaded files (per session)
file_store: dict[str, dict] = {}


@router.post("/upload")
async def upload_file(file: UploadFile):
    data = await file.read()

    if len(data) > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit")

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

    file_store[file_id] = entry

    # Return info without raw data
    return {k: v for k, v in entry.items() if k != "data"}
