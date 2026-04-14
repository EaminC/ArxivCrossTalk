# ArxivCrossTalk

一个把 arXiv 论文转换成“科研相声”音频的 Web 应用。

## 功能

- 输入 arXiv 链接或选择经典论文下拉选项
- PDF 转文本（`src/pdf2text/main.py`）
- AI 生成相声脚本 JSON（`src/api/main.py`）
- TTS 合成中/英文语音（`src/tts/main.py`）
- 可叠加 BGM、混响，并做 normalize
- 导出 MP3

## 环境变量

统一从项目根目录 `.env` 读取。至少需要：

- `FORGE_API_KEY`
- `FORGE_BASE_URL`
- `MODEL`
- `AI_TEMPERATURE`
- `PORT`（可选，默认 `3344`）
- `OUTPUT_BITRATE`（可选，默认 `192k`）

## 运行

```bash
pip install -r requirements.txt
python -m src.main
```

默认监听 `0.0.0.0:3344`，可公网访问（取决于你的服务器/防火墙配置）。
