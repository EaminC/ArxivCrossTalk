import json

from openai import OpenAI

from src.config import FORGE_API_KEY, FORGE_BASE_URL, MODEL, AI_TEMPERATURE

_client = OpenAI(base_url=FORGE_BASE_URL, api_key=FORGE_API_KEY)

# ── Base system prompts (per language) ───────────────────────────────────
_BASE_SYSTEM = {
    "zh": """
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
  "language": "zh",
  "segments": [
    {
      "stage": "opening|intro|background|motivation|innovation|method|experiments|outlook|ending",
      "role": "male|female",
      "text": "...",
      "pause_in_seconds": 0.4
    }
  ]
}
""".strip(),

    "en": """
You are an "Academic Stand-Up Comedy Writer AI".
Based on the given paper text, generate a strictly parseable JSON comedy script in the style of a two-person crosstalk (Chinese-style stand-up dialogue).

Requirements:
1. Stages must appear in this order: opening, intro, background, motivation, innovation, method, experiments, outlook, ending.
2. Two speakers alternate: roles are "male" and "female".
3. The opening should be a lively warm-up; the ending should be a proper sign-off.
4. Content must be both entertaining and faithful to the paper — never fabricate experimental numbers.
5. Return ONLY the JSON. No Markdown fences, no explanations.

JSON schema:
{
  "title": "Paper title",
  "language": "en",
  "segments": [
    {
      "stage": "opening|intro|background|motivation|innovation|method|experiments|outlook|ending",
      "role": "male|female",
      "text": "...",
      "pause_in_seconds": 0.4
    }
  ]
}
""".strip(),
}

# ── Per-length extra instructions (per language) ──────────────────────────
_LENGTH_EXTRA = {
    "zh": {
        "short": """
【长度：短版】
- 每个阶段仅 1-2 句对话，总段数不超过 {max_seg} 条。
- 抓住每部分最核心的一句话，快速推进，像精华摘要版相声。
- 语言简洁有力，不展开细节。
""".strip(),

        "medium": """
【长度：中版】
- 每个阶段 2-4 句对话，总段数不超过 {max_seg} 条。
- 兼顾广度与深度，每个部分都有清晰的介绍和一两个有趣互动。
- 可以适当加入 1-2 个比喻或类比帮助听众理解。
""".strip(),

        "long": """
【长度：长版·深度解析】
- 每个阶段 4-7 句对话，总段数不超过 {max_seg} 条。
- 必须包含以下深度元素：
  a) background：详细讲解领域历史和前人工作的局限性，举 1-2 个具体例子。
  b) motivation：说明为什么现有方案不够好，用生活类比让非专业听众也能理解。
  c) innovation：细致拆解核心创新点，一方追问、另一方补充解释，来回至少 3 轮。
  d) method：逐步讲解技术方案，包含关键公式/模块的直白翻译，允许提问反驳。
  e) experiments：分析主要实验结果，提及与 baseline 对比，讨论消融实验（如有）。
  f) outlook：展望未来方向，讨论局限性，加入对该领域的批判性思考。
- 对话节奏要有变化：可插入反问、惊叹、幽默吐槽，避免平铺直叙。
""".strip(),
    },

    "en": {
        "short": """
[Length: Short]
- Each stage gets only 1-2 exchanges; total must not exceed {max_seg} segments.
- Hit the single most important point per section — fast, punchy, like a highlights reel.
- Keep language crisp; skip detailed elaboration.
""".strip(),

        "medium": """
[Length: Medium]
- Each stage gets 2-4 exchanges; total must not exceed {max_seg} segments.
- Balance breadth and depth; include a clear intro and one or two fun interactions per section.
- Add 1-2 analogies or metaphors to help a general audience follow along.
""".strip(),

        "long": """
[Length: Long — Deep Dive]
- Each stage gets 4-7 exchanges; total must not exceed {max_seg} segments.
- Must include the following depth elements:
  a) background: explain field history and prior work's limitations with 1-2 concrete examples.
  b) motivation: articulate why existing solutions fall short; use an everyday analogy.
  c) innovation: unpack the core contribution through back-and-forth (at least 3 rounds of Q&A).
  d) method: walk through the technical approach step by step; plainly translate key formulas/modules; include pushback.
  e) experiments: analyse main results, compare against baselines, discuss ablations if present.
  f) outlook: speculate on future directions, acknowledge limitations, add critical perspective on the field.
- Vary pacing: mix rhetorical questions, exclamations, and witty remarks — avoid monotone delivery.
""".strip(),
    },
}

_LENGTH_MAX_SEGS = {"short": 18, "medium": 36, "long": 65}


def paper_to_crosstalk_json(
    paper_text: str,
    language: str = "zh",
    length: str = "medium",
) -> dict:
    language = language if language in _BASE_SYSTEM else "zh"
    length   = length   if length   in _LENGTH_MAX_SEGS else "medium"

    max_seg      = _LENGTH_MAX_SEGS[length]
    extra        = _LENGTH_EXTRA[language][length].format(max_seg=max_seg)
    system_prompt = _BASE_SYSTEM[language] + "\n\n" + extra

    if language == "zh":
        user_msg = (
            f"以下是论文内容，请按要求输出相声脚本 JSON：\n\n{paper_text}"
        )
    else:
        user_msg = (
            f"Here is the paper content. Output the crosstalk script JSON as instructed:\n\n{paper_text}"
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
        raise ValueError("AI returned invalid format — missing 'segments' list.")
    return data
