import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from src.config import BGM_DIR, UPLOAD_DIR, OUTPUT_DIR, PRESET_PAPERS
from src.services.ai_script import paper_to_crosstalk_json
from src.services.pdf2text import pdf_to_text
from src.services.tts import script_to_speech

router = APIRouter(prefix="/api")

_ALLOWED_BGM_SUFFIXES = {".mp3", ".wav", ".ogg", ".flac"}


@router.get("/presets")
async def list_presets() -> JSONResponse:
    return JSONResponse({"presets": [{"name": n, "url": u} for n, u in PRESET_PAPERS]})


@router.get("/bgm-files")
async def list_bgm_files() -> JSONResponse:
    preset = sorted(p.name for p in BGM_DIR.glob("*") if p.suffix.lower() in _ALLOWED_BGM_SUFFIXES)
    uploaded = sorted(p.name for p in UPLOAD_DIR.glob("*") if p.suffix.lower() in _ALLOWED_BGM_SUFFIXES)
    return JSONResponse({"preset": preset, "uploaded": uploaded})


@router.post("/upload-bgm")
async def upload_bgm(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="没有收到文件名。")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_BGM_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {suffix}")
    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return JSONResponse({"ok": True, "filename": file.filename})


def _sync_generate(
    arxiv_url: str,
    language: str,
    bgm_path: Optional[str],
    bgm_mix_ratio: float,
    reverb_amount: float,
    speech_rate: float,
) -> dict:
    paper_text = pdf_to_text(arxiv_url)
    script_data = paper_to_crosstalk_json(paper_text=paper_text, language=language)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"crosstalk_{language}_{ts}"
    script_path = OUTPUT_DIR / f"{stem}.json"
    audio_path = OUTPUT_DIR / f"{stem}.mp3"
    script_path.write_text(json.dumps(script_data, ensure_ascii=False, indent=2), encoding="utf-8")
    script_to_speech(
        script_data=script_data,
        language=language,
        output_path=str(audio_path),
        bgm_path=bgm_path,
        bgm_mix_ratio=bgm_mix_ratio,
        reverb_amount=reverb_amount,
        speech_rate=speech_rate,
    )
    return {
        "audio_url": f"/outputs/{audio_path.name}",
        "script_url": f"/outputs/{script_path.name}",
        "script": script_data,
    }


@router.post("/generate")
async def generate(
    arxiv_url: str = Form(default=""),
    preset_url: str = Form(default=""),
    language: str = Form(default="zh"),
    bgm_source: str = Form(default="preset"),
    bgm_preset_file: str = Form(default=""),
    bgm_uploaded_file: str = Form(default=""),
    bgm_mix_ratio: float = Form(default=0.2),
    reverb_amount: float = Form(default=0.15),
    speech_rate: float = Form(default=1.0),
    bgm_file: Optional[UploadFile] = File(default=None),
) -> JSONResponse:
    target_url = arxiv_url.strip() or preset_url.strip()
    if not target_url:
        raise HTTPException(status_code=400, detail="请提供 arXiv 链接。")

    bgm_path: Optional[str] = None
    if bgm_source == "upload" and bgm_file and bgm_file.filename:
        suffix = Path(bgm_file.filename).suffix.lower()
        if suffix not in _ALLOWED_BGM_SUFFIXES:
            raise HTTPException(status_code=400, detail=f"不支持的 BGM 格式: {suffix}")
        dest = UPLOAD_DIR / bgm_file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(bgm_file.file, f)
        bgm_path = str(dest)
    elif bgm_source == "uploaded" and bgm_uploaded_file:
        candidate = UPLOAD_DIR / bgm_uploaded_file
        if candidate.exists():
            bgm_path = str(candidate)
    elif bgm_source == "preset" and bgm_preset_file:
        candidate = BGM_DIR / bgm_preset_file
        if candidate.exists():
            bgm_path = str(candidate)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            _sync_generate,
            target_url,
            language,
            bgm_path,
            bgm_mix_ratio,
            reverb_amount,
            speech_rate,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse(result)


@router.get("/outputs/{filename}")
async def serve_output(filename: str) -> FileResponse:
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在。")
    media = "audio/mpeg" if path.suffix == ".mp3" else "application/octet-stream"
    return FileResponse(str(path), media_type=media, filename=filename)
