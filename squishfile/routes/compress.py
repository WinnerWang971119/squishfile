# squishfile/routes/compress.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from squishfile.routes.upload import file_store
from squishfile.compressor.engine import compress_file

router = APIRouter(prefix="/api")


class CompressRequest(BaseModel):
    file_id: str
    target_size_kb: int


@router.post("/compress")
async def compress(req: CompressRequest):
    entry = file_store.get(req.file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")

    target_bytes = req.target_size_kb * 1024

    result = compress_file(
        data=entry["data"],
        mime=entry["mime"],
        category=entry["category"],
        target_size=target_bytes,
        width=entry.get("width", 0),
        height=entry.get("height", 0),
    )

    # Store compressed data
    entry["compressed_data"] = result["data"]
    entry["compressed_size"] = result["size"]

    return {
        "file_id": req.file_id,
        "original_size": result["original_size"],
        "compressed_size": result["size"],
        "skipped": result["skipped"],
        "message": result.get("message"),
    }


@router.get("/download/{file_id}")
async def download(file_id: str):
    entry = file_store.get(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")

    data = entry.get("compressed_data", entry["data"])
    filename = entry["original_filename"]

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
