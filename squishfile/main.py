import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from squishfile import __version__
from squishfile.routes.upload import router as upload_router
from squishfile.routes.compress import router as compress_router
from squishfile.compressor.ffmpeg_utils import check_ffmpeg

logger = logging.getLogger(__name__)

app = FastAPI(title="SquishFile", version=__version__)

if not check_ffmpeg():
    logger.warning(
        "FFmpeg not available. Video and audio compression will not work. "
        "Try reinstalling: pip install imageio-ffmpeg"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(compress_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": __version__}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
FRONTEND_INDEX = os.path.join(FRONTEND_DIR, "index.html")
FRONTEND_ASSETS_DIR = os.path.join(FRONTEND_DIR, "assets")

if os.path.isdir(FRONTEND_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="assets")

if os.path.isfile(FRONTEND_INDEX):
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(FRONTEND_INDEX)
