import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.config import OUTPUT_DIR, PORT
from src.routers.generate import router as generate_router

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="ArXiv Crosstalk", version="0.2.0")

app.include_router(generate_router)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (_STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=False)
