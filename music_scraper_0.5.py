import requests
import json
import urllib.parse
import os
import time
import re
import math
from tqdm import tqdm


class MyFreeMp3Scraper:
    """
    用于抓取 MyFreeMp3 网站音乐的 Python 封装类。
    支持搜索音乐（配合本地精确匹配），并通过第三方API获取下载链接并下载。
    """

    def __init__(self):
        self.base_url = "https://www.myfreemp3.com.cn/"
        self.session = requests.Session()
        self._set_common_headers()
        # 请替换为新的第三方 API 地址！
        self.byfuns_api_url = "https://api.bugpk.com/api/163_music"

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

    def search_music_raw(self, keyword, target_count=100, music_type="netease"):  # 默认 target_count 提高到 100
        """
        根据关键字向 myfreemp3.com.cn 网站搜索音乐，返回原始API结果列表 (多条)。
        这个方法是为了获取一个“候选列表”，供后续的本地精确匹配使用。
        """
        search_url = self.base_url
        all_music_results = []
        results_per_page = 10

        pages_to_fetch = math.ceil(target_count / results_per_page)
        if pages_to_fetch == 0:
            pages_to_fetch = 1

        post_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url.rstrip('/'),
            "Referer": self.base_url
        }
        self.session.headers.update(post_headers)

        print(f"正在向 {self.base_url} 搜索 '{keyword}' 获取初步结果列表 (目标 {target_count} 条)...")

        for p in range(1, pages_to_fetch + 1):
            if len(all_music_results) >= target_count:
                break

            payload = {
                "input": keyword,
                "filter": "name",
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

                    if len(current_page_list) < results_per_page:
                        break
                else:
                    break
            except requests.exceptions.RequestException:
                break
            except (json.JSONDecodeError, IndexError):
                break
            except Exception:
                break

        formatted_list = []
        for music in all_music_results[:target_count]:
            formatted_list.append({
                "title": music.get("title", "未知歌曲"),
                "author": music.get("author", "未知歌手"),
                "songid": music.get("songid", "N/A")
            })

        return formatted_list

    def get_download_link_from_byfuns(self, song_id, level="standard"):
        """
        通过新的第三方 API (bugpk.com) 获取音乐的直链。

        Args:
            song_id (str): 网易云音乐的歌曲ID。
            level (str): 音质选择，例如 "standard", "exhigh", "lossless", "hires", "jyeffect", "sky", "jymaster"。
                         默认为 "standard"。

        Returns:
            str or None: 音乐直链，如果获取失败则返回 None。
        """
        if not song_id or str(song_id) == "N/A":
            print("歌曲ID无效，无法获取下载链接。")
            return None

        valid_levels = ["standard", "exhigh", "lossless", "hires", "jyeffect", "sky", "jymaster"]
        if level not in valid_levels:
            print(f"警告: 无效的音质级别 '{level}'。将使用默认的 'standard'。")
            level = "standard"

        params = {
            "ids": song_id,
            "level": level,
            "type": "json"
        }

        print(f"正在通过第三方API获取下载链接 (ID: {song_id}, 音质: {level})...")
        try:
            response = self.session.get(self.byfuns_api_url, params=params, timeout=10)
            response.raise_for_status()

            result_json = response.json()

            if result_json.get("status") == 200:
                download_url = result_json.get("url")
                if download_url and download_url.startswith("http"):
                    print("成功获取下载链接。")
                    return download_url
                else:
                    print(f"第三方API返回的JSON中 'url' 字段无效或缺失。完整响应: {result_json}")
                    return None
            else:
                error_msg = result_json.get("msg", "未知错误")
                print(f"第三方API返回错误状态 {result_json.get('status', 'N/A')}: {error_msg}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"从第三方API获取链接失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"解析第三方API响应失败: {e}. 响应内容: {response.text[:200]}...")
            return None
        except Exception as e:
            print(f"获取第三方API链接时发生未知错误: {e}")
            return None

    def download_music(self, music_url, filename, save_dir="downloads"):
        """
        下载音乐文件到本地。
        """
        if not music_url:
            print("下载链接为空，无法下载。")
            return None

        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)

        print(f"正在下载 '{filename}' 到 '{file_path}'...")
        try:
            response = self.session.get(music_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size_in_bytes = int(response.headers.get("content-length", 0))

            with open(file_path, 'wb') as f:
                with tqdm(total=total_size_in_bytes, unit='B', unit_scale=True, desc=filename, ascii=True,
                          ncols=100) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            print(f"'{filename}' 下载完成！")
            return file_path
        except requests.exceptions.RequestException as e:
            print(f"下载 '{filename}' 失败: {e}")
            return None
        except Exception as e:
            print(f"下载 '{filename}' 时发生未知错误: {e}")
            return None


# --- 辅助函数：用于清洗和匹配 ---
def _clean_string_for_match(s):
    """
    清洗字符串，移除括号内容、多余空格、描述性后缀，并转换为小写，用于比较。
    """
    if not isinstance(s, str):
        return ""
    s = re.sub(r'\(.*?\)|（.*?）|\[.*?\]|【.*?】', '', s)
    s = re.sub(r'[\s]*-[\s](Live|伴奏|demo|纯音乐|remix|现场版|粤语版|国语版).*$', '', s, flags=re.IGNORECASE)
    s = s.strip().lower()
    return s


def find_strict_match(expected_title_raw, expected_artist_raw, search_results):
    """
    在搜索结果列表中查找最符合要求的歌曲。返回一个最佳匹配。
    主要用于“歌名-歌手”的精确匹配，或“纯歌名”的最佳猜测。
    如果 expected_title_raw 或 expected_artist_raw 为 None/空，则该项不参与严格判断。
    """
    if not search_results:
        return None

    expected_title_cleaned = _clean_string_for_match(expected_title_raw) if expected_title_raw else ""
    expected_artist_cleaned = expected_artist_raw.strip().lower() if expected_artist_raw else ""

    best_match = None
    best_score = -1

    for song in search_results:
        actual_title_raw = song.get("title", "")
        actual_artist_raw = song.get("author", "")

        actual_title_cleaned = _clean_string_for_match(actual_title_raw)
        actual_artist_cleaned = actual_artist_raw.strip().lower()

        current_score = 0

        # --- 歌手匹配 (严格匹配 if provided) ---
        artist_matched = False
        if expected_artist_cleaned:  # 只有用户明确指定了歌手才进行严格匹配
            if expected_artist_cleaned == actual_artist_cleaned:
                artist_matched = True
                current_score += 10
            else:
                continue  # 歌手不匹配且被期望匹配，则跳过
        else:  # 如果用户没有指定歌手，则任何歌手都算通过此项
            artist_matched = True

        # --- 歌名匹配 (模糊匹配 if provided) ---
        title_matched = False
        if expected_title_cleaned:  # 只有用户明确指定了歌名才进行匹配
            if expected_title_cleaned == actual_title_cleaned:  # 歌名完全匹配 (清洗后)
                title_matched = True
                current_score += 10
            elif expected_title_cleaned in actual_title_cleaned:  # 用户歌名是实际歌名的一部分
                title_matched = True
                current_score += 5
            elif actual_title_cleaned in expected_title_cleaned:  # 实际歌名是用户歌名的一部分
                title_matched = True
                current_score += 4

        else:  # 如果用户没有指定歌名，则任何歌名都算通过此项
            title_matched = True

        # 仅在歌名和歌手都满足条件时，才记录分数以便选择最佳匹配
        if title_matched and artist_matched:
            if current_score > best_score:
                best_match = song
                best_score = current_score

    return best_match


# --- 主程序逻辑 ---
if __name__ == "__main__":
    scraper = MyFreeMp3Scraper()

    while True:
        user_input = input(
            "请输入您想搜索的音乐或歌手 (格式: '歌名-歌手', '歌名 歌手', 纯歌手名 或 纯歌名; 输入 2 退出): ").strip()

        if user_input == '2':
            print("感谢使用，程序已退出。")
            break

        if not user_input:
            print("输入为空，将为您搜索默认歌曲 '爱在西元前-周杰伦'。")
            user_input = "爱在西元前-周杰伦"

        parsed_title = None  # 最终确定用于匹配的歌名
        parsed_artist = None  # 最终确定用于匹配的歌手
        api_initial_keyword = user_input  # 用于 myfreemp3 API 的原始关键词

        is_pure_artist_search_intent = False  # 标记是否识别为纯歌手搜索意图

        # --- 输入解析逻辑 ---
        split_char = None
        if '-' in user_input and user_input.count('-') == 1:
            split_char = '-'
        elif ' ' in user_input and user_input.count(' ') == 1:  # 修正：user_input.count(' ') == 1
            split_char = ' '

        if split_char:  # 用户输入包含分隔符 ('歌名-歌手' 或 '歌名 歌手' 格式)
            parts = user_input.rsplit(split_char, 1)
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                parsed_title = parts[0].strip()
                parsed_artist = parts[1].strip()
                api_initial_keyword = f"{parsed_title} {parsed_artist}"
                print(f"ℹ️ 检测到歌曲+歌手指令 '{user_input}'。")
            else:  # 解析失败，按纯关键词处理
                print(f"⚠️ 指令格式 '{user_input}' 解析失败，将按原始输入处理。")
                # parsed_title 等仍然为 None，走下面的纯关键词逻辑

        else:  # 用户输入的是纯关键词 (没有分隔符)
            api_initial_keyword = user_input  # API依然用原始输入去搜

            # --- 启发式判断：尝试识别纯歌手搜索意图 ---
            # 暂时将 user_input 清洗后作为潜在的歌手名，用于后续的过滤
            expected_artist_potential_cleaned = _clean_string_for_match(user_input)

            # 由于 myfreemp3 API 对纯歌手名的搜索结果可能比较乱，先不做这个判断，
            # 而是统一获取结果后，再在本地根据结果来判断是纯歌手还是纯歌名。
            # 这里不设置 parsed_title 或 parsed_artist，让它们保持 None，
            # 这样 find_strict_match 在没有明确指定歌名/歌手时不会严格匹配这两项。
            print(f"ℹ️ 检测到纯关键词输入 '{user_input}'。")

        # 1. 向 MyFreeMp3 API 发送初步搜索请求，获取一个候选列表
        # `target_count` 提高到 100，以确保纯歌手搜索有足够多的数据进行筛选
        candidate_music_results = scraper.search_music_raw(api_initial_keyword, target_count=100)

        selected_for_download = None

        # --- 根据用户输入类型和匹配结果，决定如何展示和选择歌曲 ---

        if parsed_title and parsed_artist:  # 用户明确输入了 "歌名-歌手" 或 "歌名 歌手"
            print("进行歌名+歌手精确匹配...")
            most_accurate_combined_match = find_strict_match(parsed_title, parsed_artist, candidate_music_results)

            if most_accurate_combined_match:
                print(
                    f"\n✅ 找到精确匹配歌曲: {most_accurate_combined_match['title']} - {most_accurate_combined_match['author']} (ID: {most_accurate_combined_match['songid']})")

                download_choice = input("是否下载这首歌曲？(y/n，默认y): ").strip().lower()
                if download_choice == '' or download_choice == 'y':
                    selected_for_download = most_accurate_combined_match
                else:
                    print("放弃下载该精确匹配歌曲。")
            else:
                print(f"⚠️ 未找到与 '{user_input}' 精确匹配的歌曲。")
                # 如果没有精确匹配，则展示前10个通用结果
                results_to_display = candidate_music_results[:10]
        else:  # 用户输入的是纯关键词 (parsed_title 和 parsed_artist 均为 None)

            # --- 启发式判断：是否是纯歌手搜索意图 ---
            expected_artist_cleaned = _clean_string_for_match(user_input)  # 假设用户输入是歌手
            artist_filtered_songs = []
            for song in candidate_music_results:
                actual_artist_cleaned = _clean_string_for_match(song.get("author", ""))
                if expected_artist_cleaned == actual_artist_cleaned:
                    artist_filtered_songs.append(song)

            # 如果按作者匹配到的歌曲数量达到阈值 (例如 5 首)，则认为是纯歌手搜索
            if len(artist_filtered_songs) >= 5:
                is_pure_artist_search_intent = True
                print(f"ℹ️ 识别为纯歌手搜索意图: '{user_input}'。将展示最多50首该歌手的歌曲。")
                results_to_display = artist_filtered_songs[:50]  # 展示最多50首该歌手的歌曲

            else:  # 未识别为纯歌手意图，则按纯歌名搜索处理，或者作为通用关键词
                print(f"ℹ️ 未识别为纯歌手意图，将按歌名最匹配或通用关键词处理: '{user_input}'。")
                # 尝试找纯歌名的最佳匹配
                most_accurate_song_only_match = find_strict_match(user_input, None, candidate_music_results)

                if most_accurate_song_only_match:
                    print(
                        f"\n✅ 找到最匹配歌曲 (按歌名): {most_accurate_song_only_match['title']} - {most_accurate_song_only_match['author']} (ID: {most_accurate_song_only_match['songid']})")
                    download_choice = input("是否下载这首歌曲？(y/n，默认y): ").strip().lower()
                    if download_choice == '' or download_choice == 'y':
                        selected_for_download = most_accurate_song_only_match
                    else:
                        print("放弃下载该歌曲。")
                else:
                    print(f"⚠️ 未找到与 '{user_input}' 最匹配的单曲。将展示通用搜索结果。")
                    results_to_display = candidate_music_results[:10]  # Show top 10 general results

        # --- 显示结果列表并获取用户选择 (如果还没有直接确定下载歌曲) ---
        if selected_for_download:  # 歌曲已经通过精确匹配或纯歌名匹配被选中并询问下载
            pass  # 直接跳到下载执行
        elif results_to_display:  # 需要从列表选择歌曲
            list_header = f"--- 歌曲列表 (共找到 {len(results_to_display)} 首"
            if is_pure_artist_search_intent:  # 如果是纯歌手列表
                list_header += f", 歌手: {user_input})"
            else:  # 如果是前10个通用结果
                list_header += f", 关键词: {user_input})"

            print(f"\n{list_header} ---")

            for i, music in enumerate(results_to_display):
                title = music.get('title', '未知歌曲')
                author = music.get('author', '未知歌手')
                songid = music.get('songid', 'N/A')
                print(f"{i + 1}. 歌曲: {title} - 歌手: {author} (ID: {songid})")
            print("--------------------------------------------------\n")

            try:
                choice_input = input("请输入您想下载的歌曲序号 (输入 0 放弃下载): ").strip()
                if choice_input.isdigit():
                    choice = int(choice_input)
                    if 1 <= choice <= len(results_to_display):
                        selected_for_download = results_to_display[choice - 1]
                    elif choice == 0:
                        print("放弃下载。")
                    else:
                        print(f"无效的序号。请选择 1 到 {len(results_to_display)} 之间的数字，或输入 0 放弃。")
                else:
                    print("输入无效，请输入数字。")
            except Exception as e:
                print(f"处理下载选择时发生意外错误: {e}")
        else:  # 经过所有尝试，仍然没有找到任何结果
            print(f"⚠️ 未找到与输入的 '{user_input}' 相关的歌曲。")

        # --- 最终下载执行 ---
        if selected_for_download:
            download_link = scraper.get_download_link_from_byfuns(selected_for_download['songid'], level="lossless")
            if download_link:
                safe_title = "".join(
                    c for c in selected_for_download['title'] if c.isalnum() or c in (' ', '.', '_')).strip()
                safe_author = "".join(
                    c for c in selected_for_download['author'] if c.isalnum() or c in (' ', '.', '_')).strip()
                filename = f"{safe_title} - {safe_author}_{selected_for_download['songid']}.mp3"
                download_path = scraper.download_music(download_link, filename)
                if download_path:
                    print(f"音乐已保存到: {download_path}")
                else:
                    print("下载音乐文件失败。")
            else:
                print("未能获取到有效的音乐下载链接，无法下载。")

        print("\n------------------------------------------------------")
        print("准备进行下一次搜索。\n")
