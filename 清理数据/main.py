import json
from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="JSON转文本API",
    description="将给定的JSON歌曲数据转换为易于阅读的文本格式"
)


def format_json_to_text(data: List[Dict[str, Any]]) -> str:
    """
    将 JSON 格式的歌曲列表数据转换为格式化的文本字符串。
    """
    text_output = "歌曲列表\n\n"
    text_output += "---\n\n"

    for i, song in enumerate(data, 1):
        text_output += f"**歌曲{i}**\n"
        text_output += f"* **ID:** {song.get('id', 'N/A')}\n"
        text_output += f"* **歌曲名:** {song.get('name', 'N/A')}\n"
        text_output += f"* **歌手:** {song.get('artist', 'N/A')}\n"
        text_output += f"* **专辑:** {song.get('album', 'N/A')}\n"
        text_output += f"* **时长:** {song.get('duration_ms', 'N/A')} 毫秒\n\n"
        text_output += "---\n\n"

    return text_output.strip()


@app.post("/convert_to_dify_json", response_class=JSONResponse)
async def convert_json_to_dify_format(data: List[Dict[str, Any]]):
    """
    接收一个 JSON 格式的歌曲列表，并返回一个符合 Dify API 期望的 JSON 对象。
    """
    formatted_text = format_json_to_text(data)

    # 构造符合 Dify 要求的 JSON 对象
    dify_payload = {
        "name": "formatted_music_list",  # 你可以给文件起个有意义的名字
        "text": formatted_text,
        "indexing_technique": "high_quality",
        "process_rule": {
            "mode": "automatic"
        }
    }

    return dify_payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)