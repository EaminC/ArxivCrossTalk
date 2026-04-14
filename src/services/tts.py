import asyncio
import os
import tempfile
from pathlib import Path

import edge_tts
from pydub import AudioSegment
from pydub.effects import normalize

from src.config import OUTPUT_BITRATE

VOICE_MAP: dict[str, dict[str, str]] = {
    "zh": {"male": "zh-CN-YunxiNeural",  "female": "zh-CN-XiaoxiaoNeural"},
    "en": {"male": "en-US-GuyNeural",    "female": "en-US-JennyNeural"},
}


def _speed_to_rate(speed: float) -> str:
    """Convert a multiplier (e.g. 1.5) to edge-tts rate string (e.g. '+50%')."""
    pct = int(round((speed - 1.0) * 100))
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


async def _tts_save(text: str, voice: str, path: Path, rate_str: str = "+0%") -> None:
    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate_str)
    await comm.save(str(path))


def _reverb(audio: AudioSegment, amount: float) -> AudioSegment:
    """Lightweight reverb via attenuated echo overlays."""
    amount = max(0.0, min(1.0, amount))
    if amount < 0.01:
        return audio
    result = audio
    for delay_ms, base_atten in [(70, 8), (140, 13), (230, 18)]:
        extra = (1.0 - amount) * 8
        result = result.overlay(audio - (base_atten + extra), position=delay_ms)
    return result


def _build_audio(
    script_data: dict,
    language: str,
    speech_rate: float = 1.0,
) -> AudioSegment:
    segments = script_data.get("segments", [])
    voice_set = VOICE_MAP.get(language, VOICE_MAP["en"])
    rate_str = _speed_to_rate(speech_rate)
    final = AudioSegment.silent(duration=300)

    async def _run_all(pairs: list[tuple[str, str, Path]]) -> None:
        for text, voice, path in pairs:
            await _tts_save(text, voice, path, rate_str)

    with tempfile.TemporaryDirectory() as tmp:
        pairs: list[tuple[str, str, Path]] = []
        valid_segs: list[tuple[dict, Path]] = []
        for i, seg in enumerate(segments):
            text = seg.get("text", "").strip()
            if not text:
                continue
            voice = voice_set.get(seg.get("role", "male"), voice_set["male"])
            p = Path(tmp) / f"seg_{i}.mp3"
            pairs.append((text, voice, p))
            valid_segs.append((seg, p))

        asyncio.run(_run_all(pairs))

        for seg, p in valid_segs:
            chunk = AudioSegment.from_file(p, format="mp3")
            pause_ms = int(float(seg.get("pause_in_seconds", 0.35)) * 1000)
            final += chunk + AudioSegment.silent(duration=pause_ms)

    return final


def script_to_speech(
    script_data: dict,
    language: str,
    output_path: str,
    bgm_path: str | None = None,
    bgm_mix_ratio: float = 0.2,
    reverb_amount: float = 0.15,
    speech_rate: float = 1.0,
) -> str:
    speech = _build_audio(script_data, language, speech_rate)

    if bgm_path and Path(bgm_path).exists():
        bgm = AudioSegment.from_file(bgm_path)
        if len(bgm) < len(speech):
            bgm = bgm * ((len(speech) // len(bgm)) + 1)
        bgm = bgm[: len(speech)]
        # Raise BGM baseline so default mixes sound less quiet.
        gain_db = -20 + max(0.0, min(1.0, bgm_mix_ratio)) * 20
        speech = speech.overlay(bgm + gain_db)

    speech = _reverb(speech, reverb_amount)
    speech = normalize(speech)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    speech.export(str(out), format="mp3", bitrate=OUTPUT_BITRATE)
    return str(out)
