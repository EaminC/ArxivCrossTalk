import json

from openai import OpenAI

from src.config import FORGE_API_KEY, FORGE_BASE_URL, MODEL, AI_TEMPERATURE

_client = OpenAI(base_url=FORGE_BASE_URL, api_key=FORGE_API_KEY)

# ── Base system prompt ────────────────────────────────────────────────────
_BASE_SYSTEM = """
你是一个"科研相声编剧 AI"。
根据给定论文文本，生成严格可解析的 JSON 格式相声脚本。

基本要求：
1. 阶段（stage）必须按顺序包含：opening, intro, background, motivation, innovation, method, experiments, outlook, ending。
2. 风格是双人相声对话，角色固定用 male / female 轮流说话。
3. 开场要有相声式热场白，结尾要有谢幕词。
4. 内容既风趣幽默，又忠实于论文实际内容，不捏造实验数字。
5. 只返回 JSON，不加任何 Markdown 包装或解释文字。

JSON 结构：
{
  "title": "论文标题",
  "language": "zh 或 en",
  "segments": [
    {
      "stage": "opening|intro|background|motivation|innovation|method|experiments|outlook|ending",
      "role": "male|female",
      "text": "...",
      "pause_in_seconds": 0.4
    }
  ]
}
""".strip()

# ── Per-length extra instructions ─────────────────────────────────────────
_LENGTH_EXTRA = {
    "short": """
【长度要求：短版】
- 每个阶段仅 1-2 句对话，总段数不超过 {max_seg} 条。
- 抓住每部分最核心的一句话，快速推进，像精华摘要版相声。
- 语言简洁有力，不展开细节。
""".strip(),

    "medium": """
【长度要求：中版】
- 每个阶段 2-4 句对话，总段数不超过 {max_seg} 条。
- 兼顾广度与深度，每个部分都有清晰的介绍和一两个有趣互动。
- 可以适当加入 1-2 个比喻或类比帮助听众理解。
""".strip(),

    "long": """
【长度要求：长版·深度解析】
- 每个阶段 4-7 句对话，总段数不超过 {max_seg} 条。
- 必须包含以下深度元素：
  a) background：详细讲解领域历史和前人工作的局限性，举 1-2 个具体例子。
  b) motivation：说明为什么现有方案不够好，用生活类比让非专业听众也能理解。
  c) innovation：细致拆解核心创新点，一方追问、另一方补充解释，来回至少 3 轮。
  d) method：逐步讲解技术方案，包含关键公式/模块的直白翻译，允许提问反驳。
  e) experiments：分析主要实验结果，提及与 baseline 对比，讨论消融实验（如有）。
  f) outlook：展望未来方向，讨论局限性，加入对该领域的批判性思考。
- 对话节奏要有变化：可插入反问、惊叹、幽默吐槽，避免平铺直叙。
- 语言生动，多用比喻、举例、追问，确保内容丰富详尽。
""".strip(),
}

# max segments per length
_LENGTH_MAX_SEGS = {"short": 18, "medium": 36, "long": 65}


def paper_to_crosstalk_json(
    paper_text: str,
    language: str = "zh",
    length: str = "medium",
) -> dict:
    """
    Generate a crosstalk JSON from paper text.

    Args:
        paper_text: Extracted text from the arXiv PDF.
        language:   'zh' or 'en'.
        length:     'short', 'medium', or 'long'.
    """
    length = length if length in _LENGTH_MAX_SEGS else "medium"
    max_seg = _LENGTH_MAX_SEGS[length]
    extra = _LENGTH_EXTRA[length].format(max_seg=max_seg)
    system_prompt = _BASE_SYSTEM + "\n\n" + extra

    user_msg = (
        f"语言={language}\n"
        f"以下是论文内容，请按要求输出相声脚本 JSON：\n\n"
        f"{paper_text}"
    )

    completion = _client.chat.completions.create(
        model=MODEL,
        temperature=AI_TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_msg},
        ],
    )
    payload = completion.choices[0].message.content or ""
    data = json.loads(payload)
    if "segments" not in data or not isinstance(data["segments"], list):
        raise ValueError("AI 返回格式不正确，缺少 segments 字段。")
    return data
