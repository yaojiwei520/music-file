from fastapi import FastAPI
from typing import List, Dict, Any

app = FastAPI()

@app.post("/process-data")
async def process_data(data: List[Dict[str, Any]]):
    """
    接收一个 JSON 列表，并返回第一个元素的 'id'。
    """
    try:
        # 检查列表是否为空
        if not data:
            return "Data body is empty."

        # 获取第一个元素的 'id'
        first_item = data[0]
        first_id = first_item.get("id")

        # 检查 'id' 字段是否存在
        if first_id is None:
            return "ID not found in the first element."

        # 返回数值
        return first_id

    except Exception as e:
        # 捕获其他可能的错误
        return f"An unexpected error occurred: {str(e)}"