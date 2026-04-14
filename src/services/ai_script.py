import json

from openai import OpenAI

from src.config import FORGE_API_KEY, FORGE_BASE_URL, MODEL, AI_TEMPERATURE

_client = OpenAI(base_url=FORGE_BASE_URL, api_key=FORGE_API_KEY)

_SYSTEM_PROMPT = """
你是一个"科研相声编剧 AI"。
根据给定论文文本，生成严格可解析的 JSON 格式相声脚本。

要求：
1. 阶段（stage）必须按顺序包含：opening, intro, background, motivation, innovation, method, experiments, outlook, ending。
2. 风格是双人相声对话，角色固定用 male / female 轮流说。
3. 开场要有相声式的热场，结尾要有谢幕。
4. 内容要既风趣幽默，又忠实于论文实际内容，不捏造数字。
5. 只返回 JSON，不加任何 Markdown 包装或解释文字。

JSON 结构如下：
{
  "title": "论文标题（中文或英文）",
  "language": "zh 或 en",
  "segments": [
    {
      "stage": "opening",
      "role": "male",
      "text": "...",
      "pause_in_seconds": 0.4
    }
  ]
}
""".strip()


def paper_to_crosstalk_json(
    paper_text: str,
    language: str = "zh",
    max_segments: int = 40,
) -> dict:
    user_msg = (
        f"语言={language}\n"
        f"每个阶段 1-3 句对话，合计不超过 {max_segments} 条。\n"
        "以下是论文内容：\n\n"
        f"{paper_text}"
    )
    completion = _client.chat.completions.create(
        model=MODEL,
        temperature=AI_TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    payload = completion.choices[0].message.content or ""
    data = json.loads(payload)
    if "segments" not in data or not isinstance(data["segments"], list):
        raise ValueError("AI 返回格式不正确，缺少 segments 字段。")
    return data
