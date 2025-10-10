import json

# 原始数据
data = {
  "status_code": 200,
  "body": "[{\"id\":2118458192,\"name\":\"Do That\",\"artist\":\"ljz329, 马思唯\",\"album\":\"Do That\",\"duration_ms\":184421}]",
  "headers": {
    "age": "0",
    "cache-control": "public, max-age=0, must-revalidate",
    "content-length": "104",
    "content-type": "application/json",
    "date": "Sat, 13 Sep 2025 16:00:39 GMT",
    "server": "Vercel",
    "strict-transport-security": "max-age=63072000",
    "x-vercel-cache": "MISS",
    "x-vercel-id": "hnd1::iad1::89ll9-1757779238150-5492a081b836"
  },
  "files": []
}


def parse_body_content(data_dict):
    """
    解析数据字典中的 'body' 字符串为 Python 列表。
    """
    body_string = data_dict.get('body')
    if not body_string:
        print("错误：数据中缺少 'body' 字段或其值为空。")
        return None
    try:
        body_list = json.loads(body_string)
        if not isinstance(body_list, list):
            print("错误：'body'字段解析后不是一个列表。")
            return None
        return body_list
    except json.JSONDecodeError as e:
        print(f"错误：解析body字符串失败，它不是一个有效的JSON格式。详细信息: {e}")
        return None


def get_item_id_by_index(items_list, n_th_item):
    """
    从给定的列表中获取第n个元素的'id'。
    Args:
        items_list (list): 包含字典的列表。
        n_th_item (int): 需要获取的元素序号（从1开始计数）。
    Returns:
        int or None: 如果成功获取到ID，则返回ID值；否则返回None，并打印错误信息。
    """
    if not isinstance(items_list, list) or not items_list:
        print("错误：提供的列表为空或不是有效列表。")
        return None

    if not isinstance(n_th_item, int) or n_th_item < 1:
        print("错误：序号必须是一个正整数（从1开始）。")
        return None

    target_index = n_th_item - 1

    if target_index >= len(items_list):
        print(f"错误：列表只有 {len(items_list)} 个元素，无法获取第 {n_th_item} 个元素。")
        return None

    try:
        item = items_list[target_index]
        item_id = item.get('id')
        if item_id is None:
            print(f"错误：第 {n_th_item} 个元素中没有找到 'id' 键。")
            return None
        return item_id
    except (TypeError, KeyError):
        print(f"错误：获取第 {n_th_item} 个元素时发生未知错误，可能数据结构不正确。")
        return None


# --- 主程序逻辑 ---

# 1. 解析body内容
body_elements = parse_body_content(data)

if body_elements is None:
    print("无法进行数据清洗，程序退出。")
    exit()

total_elements_count = len(body_elements)
print(f"欢迎使用数据清洗工具。当前body数组共有 {total_elements_count} 个元素。")

while True:
    print("\n请选择操作：")
    print("1. 按关键词搜索 (名称/艺术家)")
    print("2. 按精确序号直接获取ID")
    print("3. 退出")

    choice = input("请输入您的选择 (1/2/3): ").strip()

    if choice == '1':
        search_term = input("请输入搜索关键词 (例如 '心跳' 或 '王力宏'): ").strip()
        if not search_term:
            print("搜索关键词不能为空。")
            continue

        matching_results = []
        lower_search_term = search_term.lower()

        for i, item in enumerate(body_elements):
            name = item.get('name', '').lower()
            artist = item.get('artist', '').lower()

            if lower_search_term in name or lower_search_term in artist:
                matching_results.append({'original_index': i + 1, 'item': item})  # 存储原始序号和元素

        if not matching_results:
            print(f"未找到与 '{search_term}' 匹配的元素。")
        else:
            print("\n----- 搜索结果 -----")
            for idx, result_entry in enumerate(matching_results):
                item = result_entry['item']
                print(
                    f"[{idx + 1}] 名称: {item.get('name', 'N/A')} | 艺术家: {item.get('artist', 'N/A')} | 专辑: {item.get('album', 'N/A')}")
            print("--------------------\n")

            while True:
                select_index_str = input(
                    f"请输入您想选择的序号（1-{len(matching_results)}）以获取ID，或输入 0 取消选择: ").strip()
                try:
                    selected_choice = int(select_index_str)
                    if selected_choice == 0:
                        print("已取消选择。")
                        break  # 跳出内层循环，返回主菜单

                    if 1 <= selected_choice <= len(matching_results):
                        # 获取用户在搜索结果中选择的元素
                        selected_result_entry = matching_results[selected_choice - 1]
                        # 获取该元素在原始body_elements中的id
                        item_id = selected_result_entry['item'].get('id')

                        if item_id is not None:
                            print(f"已选择：名称: {selected_result_entry['item'].get('name', 'N/A')} | ID: {item_id}")
                        else:
                            print(f"错误：所选元素没有 'id' 键。")
                        break  # 跳出内层循环，返回主菜单
                    else:
                        print("无效序号，请重新输入。")
                except ValueError:
                    print("无效输入，请输入数字。")

    elif choice == '2':
        user_input_str = input(f"请输入您想获取的第几个元素的ID (1-{total_elements_count}): ").strip()
        try:
            n_th = int(user_input_str)
        except ValueError:
            print("无效输入！请输入一个有效的正整数序号。")
            continue

        retrieved_id = get_item_id_by_index(body_elements, n_th)
        if retrieved_id is not None:
            print(f"清洗结果：获取到的body数组中第 {n_th} 个id是: {retrieved_id}")

    elif choice == '3':
        print("程序已退出。")
        break
    else:
        print("无效的选择，请重新输入。")

    print("-" * 50)  # 分隔线
