import asyncio
import edge_tts

async def main():
    text = "Hello, this is a test of Edge TTS."
    voice = "en-US-JennyNeural"

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("output.mp3")

asyncio.run(main())

#中文
#zh-CN-XiaoxiaoNeural ⭐（自然女声）
#zh-CN-YunxiNeural（男声）
#英语
#en-US-JennyNeural ⭐（女声，最常用）
#en-US-GuyNeural（男声）