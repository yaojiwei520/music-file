import json

data = {
    "status_code": 200,
    "body": '[{"id":33497050,"name":"心跳","artist":"王力宏","album":"力宏二十 二十周年唯一精选","duration_ms":263400},{"id":25643258,"name":"心跳","artist":"王力宏","album":"心·跳","duration_ms":263400},{"id":306877,"name":"遗失的心跳","artist":"萧亚轩","album":"我爱我 (心跳100影音庆功版)","duration_ms":216960},{"id":1818832364,"name":"心跳（翻自 王力宏）","artist":"薛不西","album":"声声不西","duration_ms":260634}]',
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

# 访问 "body" 字段的值，它是一个 JSON 格式的字符串
body_str = data["body"]
#print(f"原始body字符串的前50个字符: {body_str[:50]}...")
# 将 "body" 字符串解析成 Python 列表
body_list = json.loads(body_str)
#print(f"解析后的body类型: {type(body_list)}")
#print(f"解析后的body第一个元素: {body_list[0]}")
# 从列表中获取第一个字典，并访问其 "id" 键的值
first_id = body_list[0]["id"]
#print(f"\n清洗结果：获取到的第一个id是: {first_id}")
# 打印结果
print(first_id)