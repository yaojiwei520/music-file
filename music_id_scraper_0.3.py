import requests
import json
import urllib.parse
import time
import re  # 新增：用于正则表达式清洗歌名
import math  # 虽然只取一个结果，但 search_music 方法内部结构暂时保留页数概念


class MyFreeMp3Scraper:
    """
    用于抓取 MyFreeMp3 网站音乐的 Python 封装类。
    支持搜索音乐并获取第一个精确匹配歌曲的名称、歌手和ID。
    """

    def __init__(self):
        self.base_url = "https://www.myfreemp3.com.cn/"
        self.session = requests.Session()
        self._set_common_headers()

    def _set_common_headers(self):
        """
        设置会话的通用请求头。
        """
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "DNT": "1",
            "Priority": "u=1, i",
            "Sec-Ch-Ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
        })

    def search_music_raw(self, keyword, target_count=10, music_type="netease"):
        """
        根据关键字搜索音乐，返回原始API结果列表 (多条)。
        这个方法是为了获取一个“候选列表”，供后续的本地精确匹配使用。
        """
        search_url = self.base_url
        all_music_results = []
        results_per_page = 10

        # 确保至少请求一页，但不会超过 target_count 的页数
        pages_to_fetch = math.ceil(target_count / results_per_page)
        if pages_to_fetch == 0:
            pages_to_fetch = 1

        post_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url.rstrip('/'),
            "Referer": self.base_url
        }
        self.session.headers.update(post_headers)

        # 打印信息，但不再强调“目标获取多少首歌”，因为这只是一个获取候选列表的过程
        print(f"正在向API搜索 '{keyword}' 获取初步结果列表...")

        for p in range(1, pages_to_fetch + 1):
            if len(all_music_results) >= target_count:
                break

            payload = {
                "input": keyword,
                "filter": "name",  # 网站的API通常只支持一个综合搜索字段
                "page": str(p),
                "type": music_type
            }

            try:
                response = self.session.post(search_url, data=payload, timeout=10)
                response.raise_for_status()

                result_json = response.json()

                if result_json.get("code") == 200 and result_json.get("data") and result_json["data"].get("list"):
                    current_page_list = result_json["data"]["list"]

                    if not current_page_list:
                        break

                    all_music_results.extend(current_page_list)
                    # print(f"  - 第 {p} 页获取 {len(current_page_list)} 首。当前总数: {len(all_music_results)}")

                    if len(current_page_list) < results_per_page:
                        break
                else:
                    # error_msg = result_json.get('error') or result_json.get('msg') or "未知错误"
                    # print(f"  - 第 {p} 页搜索失败或未找到歌曲。响应详情: {error_msg}")
                    break
            except requests.exceptions.RequestException as e:
                # print(f"  - 第 {p} 页搜索音乐请求失败: {e}")
                break
            except (json.JSONDecodeError, IndexError) as e:
                # print(f"  - 第 {p} 页解析搜索响应失败或未找到歌曲: {e}. 响应内容: {response.text[:200]}")
                break
            except Exception as e:
                # print(f"  - 第 {p} 页发生未知错误: {e}")
                break

        # 格式化所有获取到的结果，并截取到目标数量
        formatted_list = []
        for music in all_music_results[:target_count]:
            formatted_list.append({
                "title": music.get("title", "未知歌曲"),
                "author": music.get("author", "未知歌手"),
                "songid": music.get("songid", "N/A")
            })

        # print(f"API初步搜索完成，获取到 {len(formatted_list)} 个候选结果。")
        return formatted_list


# --- 辅助函数：用于清洗和匹配 ---
def _clean_string_for_match(s):
    """
    清洗字符串，移除括号内容、多余空格，并转换为小写，用于比较。
    例如: "爱在西元前（温柔男声版）" -> "爱在西元前"
    """
    if not isinstance(s, str):
        return ""
    # 移除括号及其内容 (全角和半角括号)
    s = re.sub(r'\(.*?\)|（.*?）|\[.*?\]|【.*?】', '', s)
    # 移除额外的空格并转换为小写
    s = s.strip().lower()
    return s


def find_strict_match(expected_title_raw, expected_artist_raw, search_results):
    """
    在搜索结果列表中查找最符合要求的歌曲。
    要求：歌手严格匹配 (不区分大小写)，歌名模糊匹配 (包含关系，清洗后)。
    """
    if not search_results:
        return None

    # 清洗用户输入的歌名和歌手，用于比较
    expected_title_cleaned = _clean_string_for_match(expected_title_raw) if expected_title_raw else ""
    expected_artist_cleaned = expected_artist_raw.strip().lower() if expected_artist_raw else ""

    best_match = None
    best_score = -1  # 用于记录匹配度，分数越高越好

    for song in search_results:
        actual_title_raw = song.get("title", "")
        actual_artist_raw = song.get("author", "")

        actual_title_cleaned = _clean_string_for_match(actual_title_raw)
        actual_artist_cleaned = actual_artist_raw.strip().lower()

        current_score = 0

        # --- 歌手匹配 (严格匹配) ---
        artist_matched = False
        if expected_artist_cleaned:  # 如果用户输入了歌手才进行匹配
            if expected_artist_cleaned == actual_artist_cleaned:
                artist_matched = True
                current_score += 10  # 歌手精确匹配，加高分
            else:
                # 歌手不匹配，直接跳过此歌曲
                continue
        else:  # 如果用户未输入歌手，则任何歌手都算匹配
            artist_matched = True

        # --- 歌名匹配 (模糊匹配) ---
        title_matched = False
        if expected_title_cleaned:  # 如果用户输入了歌名才进行匹配
            # 检查用户输入的歌名是否在实际歌名中 或 实际歌名是否在用户输入歌名中
            if expected_title_cleaned in actual_title_cleaned:
                title_matched = True
                current_score += 5  # 歌名包含关系
            elif actual_title_cleaned in expected_title_cleaned:
                title_matched = True
                current_score += 4  # 反向包含

            # 如果是完全相等（清洗后），则加更高分
            if expected_title_cleaned == actual_title_cleaned:
                current_score += 5  # 歌名完全匹配，加更高分

            # If after cleaning, actual title is very close to expected, e.g., "唯一" vs "光良" for "唯一-光良"
            # This logic needs to be careful not to make false positives.
            # print(f"  DEBUG: {expected_title_cleaned=} {actual_title_cleaned=} {title_matched=}")
        else:  # 如果用户未输入歌名，则任何歌名都算匹配
            title_matched = True

        # 只有当歌名和歌手都匹配时，才考虑这个结果
        if title_matched and artist_matched:
            if current_score > best_score:
                best_match = song
                best_score = current_score

    return best_match


# --- 主程序逻辑 ---
if __name__ == "__main__":
    scraper = MyFreeMp3Scraper()

    # 获取用户输入
    user_input = input("请输入您想搜索的音乐或歌手 (格式: '歌名-歌手' 或 纯关键词): ").strip()

    # 处理空输入
    if not user_input:
        print("输入为空，将为您搜索默认歌曲 '爱在西元前-周杰伦'。")
        user_input = "爱在西元前-周杰伦"

    search_title = None
    search_artist = None
    api_keyword = user_input  # 用于发送给API的原始或组合关键词

    # 检查是否为模糊搜索格式 (例如 "歌名 - 歌手")
    if '-' in user_input:
        parts = user_input.rsplit('-', 1)  # 从右边开始分割，只分割一次
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()

            if part1 and part2:
                search_title = part1
                search_artist = part2
                api_keyword = f"{search_title} {search_artist}"  # 组合关键词给API
                print(
                    f"检测到指令格式 '{user_input}'。将使用组合关键词 '{api_keyword}' 向API初步搜索，并进行本地精确匹配。")
            else:
                print(f"检测到指令格式 '{user_input}'，但部分内容为空。将按原始输入 '{user_input}' 进行搜索。")
                # api_keyword 保持 user_input
        else:
            print(f"检测到指令格式 '{user_input}'，但解析失败。将按原始输入 '{user_input}' 进行搜索。")
            # api_keyword 保持 user_input
    # 否则，按普通关键词搜索，search_title/search_artist保持None，api_keyword保持user_input
    else:
        search_title = user_input  # 如果没有歌手，则认为整个输入都是歌名

    # 1. 向API发送初步搜索请求，获取一个候选列表
    # 我们希望从第一页获取足够多的候选结果 (例如10个)
    candidate_music_results = scraper.search_music_raw(api_keyword, target_count=10)

    # 2. 在本地对候选列表进行精确匹配
    found_match = find_strict_match(search_title, search_artist, candidate_music_results)

    if found_match:
        print(f"\n匹配到歌曲: {found_match['title']} - {found_match['author']}")
        print(f"对应歌曲ID: {found_match['songid']}")
    else:
        print(f"\n未找到与 '{user_input}' 严格匹配的歌曲。")

    print("\n程序执行完毕。")
