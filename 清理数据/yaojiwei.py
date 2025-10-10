import json

data = {
    "status_code": 200,
    "body": "[{\"id\":33497050,\"name\":\"心跳\",\"artist\":\"王力宏\",\"album\":\"力宏二十 二十周年唯一精选\",\"duration_ms\":263400},{\"id\":25643258,\"name\":\"心跳\",\"artist\":\"王力宏\",\"album\":\"心·跳\",\"duration_ms\":263400},{\"id\":306877,\"name\":\"遗失的心跳\",\"artist\":\"萧亚轩\",\"album\":\"我爱我 (心跳100影音庆功版)\",\"duration_ms\":216960},{\"id\":1818832364,\"name\":\"心跳（翻自 王力宏）\",\"artist\":\"薛不西\",\"album\":\"声声不西\",\"duration_ms\":260634}]",
    "headers": {
        "age": "0",
        "cache-control": "public, max-age=0, must-revalidate",
        "content-length": "465",
        "content-type": "application/json",
        "date": "Sat, 13 Sep 2025 03:50:49 GMT",
        "server": "Vercel",
        "strict-transport-security": "max-age=63072000",
        "x-vercel-cache": "MISS",
        "x-vercel-id": "iad1::iad1::6fr9k-1757735447989-5d632b6d2c6d"
    },
    "files": []
}

# 1. 获取body字符串
#body_str = data["body"]
#print(f"原始body字符串的前50个字符: {body_str[:50]}...")

# 2. 将body字符串解析为Python对象（列表）
# 注意：body字符串实际上是一个JSON数组的字符串表示







try:
    body_list = json.loads(body_str)
    print(f"解析后的body类型: {type(body_list)}")
    print(f"解析后的body第一个元素: {body_list[0]}")

    # 3. 获取列表中的第一个元素（字典）
    first_item = body_list[0]

    # 4. 从第一个元素中获取id
    first_id = first_item["id"]

    print(f"\n清洗结果：获取到的第一个id是: {first_id}")

except json.JSONDecodeError:
    print("错误：body字符串不是有效的JSON格式。")
    first_id = None
except IndexError:
    print("错误：body列表为空，无法获取第一个元素。")
    first_id = None
except KeyError:
    print("错误：第一个字典中没有'id'键。")
    first_id = None
