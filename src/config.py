import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT / ".env")

FORGE_API_KEY: str = os.getenv("FORGE_API_KEY", "")
FORGE_BASE_URL: str = os.getenv("FORGE_BASE_URL", "https://api.openai.com/v1")
MODEL: str = os.getenv("MODEL", "tensorblock/gpt-4.1-mini")
AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
PORT: int = int(os.getenv("PORT", "3344"))
OUTPUT_BITRATE: str = os.getenv("OUTPUT_BITRATE", "192k")

BGM_DIR: Path = ROOT / "data" / "bgm"
UPLOAD_DIR: Path = ROOT / "uploads"
OUTPUT_DIR: Path = ROOT / "outputs"
PROMPT_DIR: Path = ROOT / "data" / "prompt"

for _d in (BGM_DIR, UPLOAD_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

PRESET_PAPERS = [
    ("Attention Is All You Need (2017)", "https://arxiv.org/abs/1706.03762"),
    ("BERT (2018)",                       "https://arxiv.org/abs/1810.04805"),
    ("ResNet (2015)",                     "https://arxiv.org/abs/1512.03385"),
    ("NeRF (2020)",                       "https://arxiv.org/abs/2003.08934"),
    ("GPT-3 (2020)",                      "https://arxiv.org/abs/2005.14165"),
    ("Diffusion Models Beat GANs (2021)", "https://arxiv.org/abs/2105.05233"),
]
