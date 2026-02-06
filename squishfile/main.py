from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from squishfile import __version__

app = FastAPI(title="SquishFile", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": __version__}
