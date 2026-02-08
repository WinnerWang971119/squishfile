# squishfile/routes/compress.py
import io
import os
import zipfile
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
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

    # Update filename/mime if output format changed (e.g. webm -> mp4)
    if "output_ext" in result and not result.get("skipped"):
        old_name = entry["original_filename"]
        stem, _ = os.path.splitext(old_name)
        entry["original_filename"] = stem + result["output_ext"]
        entry["mime"] = result["output_mime"]

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

    ascii_filename = filename.encode("ascii", errors="replace").decode("ascii")
    encoded_filename = quote(filename)

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{encoded_filename}"
            )
        },
    )


@router.get("/download-all")
async def download_all(ids: str = Query(..., description="Comma-separated file IDs")):
    file_ids = [fid.strip() for fid in ids.split(",") if fid.strip()]
    if not file_ids:
        raise HTTPException(status_code=400, detail="No file IDs provided")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_id in file_ids:
            entry = file_store.get(file_id)
            if not entry:
                continue
            data = entry.get("compressed_data", entry["data"])
            filename = entry["original_filename"]
            zf.writestr(filename, data)

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="squishfile-compressed.zip"'
        },
    )
