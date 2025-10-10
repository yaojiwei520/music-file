import json

# 原始数据
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


def get_nth_body_id(data_dict, n_th_item):
    """
    从给定的数据字典中解析body字段，并获取其中第n个元素的'id'。

    Args:
        data_dict (dict): 包含'body'字段的原始数据字典。
        n_th_item (int): 需要获取的元素序号（从1开始计数，例如1代表第一个，2代表第二个）。

    Returns:
        int or None: 如果成功获取到ID，则返回ID值；否则返回None，并打印错误信息。
    """
    if not isinstance(n_th_item, int) or n_th_item < 1:
        print("错误：'n_th_item' 必须是一个正整数（例如，1表示第一个，2表示第二个）。")
        return None

    # 将用户提供的从1开始的索引转换为Python的0开始的索引
    target_index = n_th_item - 1

    body_string = data_dict.get('body')

    if not body_string:
        print("错误：数据中缺少 'body' 字段或其值为空。")
        return None

    try:
        body_list = json.loads(body_string)
    except json.JSONDecodeError as e:
        print(f"错误：解析body字符串失败，它不是一个有效的JSON格式。详细信息: {e}")
        return None

    if not isinstance(body_list, list):
        print("错误：'body'字段解析后不是一个列表。")
        return None

    if target_index >= len(body_list):
        print(f"错误：body数组中只有 {len(body_list)} 个元素，无法获取第 {n_th_item} 个元素。")
        return None

    try:
        item = body_list[target_index]
        item_id = item.get('id')  # 使用.get()方法，防止KeyError如果'id'可能不存在
        if item_id is None:
            print(f"错误：body数组中的第 {n_th_item} 个元素没有找到 'id' 键。")
            return None
        return item_id
    except (TypeError, KeyError):  # 处理item不是字典或者id键不存在的情况
        print(f"错误：获取第 {n_th_item} 个元素时发生未知错误，可能数据结构不正确。")
        return None


# --- 自定义用户输入示例 ---
print("欢迎使用数据清洗工具，用于获取body数组中指定元素的ID。")
print("当前body数组共有 4 个元素。")

while True:
    user_input_str = input("请输入您想获取的第几个元素的ID (例如：1表示第一个，2表示第二个；输入 'q' 退出): ")

    if user_input_str.lower() == 'q':
        print("程序已退出。")
        break

    try:
        n_th = int(user_input_str)
    except ValueError:
        print("无效输入！请输入一个有效的正整数序号，或者 'q' 退出。")
        continue  # 继续循环，让用户重新输入

    retrieved_id = get_nth_body_id(data, n_th)

    if retrieved_id is not None:
        print(f"清洗结果：获取到的body数组中第 {n_th} 个id是: {retrieved_id}")
    # 如果retrieved_id是None，get_nth_body_id函数内部已经打印了错误信息，这里无需重复打印

    print("-" * 30)  # 分隔线，方便查看多次输入的结果
