import requests
import json
import time
import os
from tqdm import tqdm
import re
from typing import List, Dict, Any

# --- 配置 ---
BASE_URL = "https://api.vkeys.cn/v2/music/tencent"
DOWNLOAD_DIR = "downloads"


# --- 辅助函数：目录、搜索、详情、匹配 ---

def ensure_download_dir():
    """检查并创建下载目录。"""
    if not os.path.exists(DOWNLOAD_DIR):
        try:
            os.makedirs(DOWNLOAD_DIR)
            print(f"📁 已创建下载目录: '{DOWNLOAD_DIR}'")
        except OSError as e:
            print(f"❌ 无法创建下载目录 '{DOWNLOAD_DIR}': {e}")


def search_music(query: str) -> List[Dict[str, Any]] | None:
    """调用腾讯音乐搜索 API 获取初步结果列表。"""
    processed_query = query.replace('-', ' ').strip()
    search_api = f"{BASE_URL}?word={requests.utils.quote(processed_query)}"

    print(f"正在向 API 搜索 '{processed_query}' 获取初步结果列表 (目标 10 条)...")

    try:
        response = requests.get(search_api)
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 200 and data.get("data"):
            return data["data"][:10]
        else:
            print(f"❌ 搜索 API 返回错误或无数据: {data.get('message')}")
            return None

    except requests.RequestException as e:
        print(f"❌ 搜索请求失败: {e}")
        return None


def get_song_url(song_id: int) -> Dict[str, Any] | None:
    """根据歌曲 ID 获取详细信息和播放链接。"""
    url_api = f"{BASE_URL}/geturl?id={song_id}"

    try:
        response = requests.get(url_api)
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 200 and data.get("data"):
            return data["data"]
        else:
            return None

    except requests.RequestException:
        return None


def get_song_lyrics(song_id: int) -> Dict[str, Any] | None:
    """根据歌曲 ID 获取歌词详情（包含lrc, trans, yrc）。"""
    lyric_api = f"{BASE_URL}/lyric?id={song_id}"

    try:
        response = requests.get(lyric_api)
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 200 and data.get("data"):
            return data["data"]
        else:
            return None

    except requests.RequestException:
        return None


def find_best_match(query: str, results: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """在结果列表中寻找歌名+歌手的精确匹配。"""
    query_parts = re.split(r'[\s\-]+', query.strip())

    if len(query_parts) >= 2:
        target_song = query_parts[0].lower()
        target_singer = query_parts[1].lower()
        print("进行歌名+歌手精确匹配...")

        for song in results:
            song_name = song.get('song', '').lower()
            singer_name = song.get('singer', '').lower()

            if target_song in song_name and target_singer in singer_name:
                return song

    return None


# --- 核心操作函数：下载与保存 ---

def actual_download(filename: str, url: str, total_size: int):
    """实现真正的文件下载到 downloads 目录，并显示进度条。"""
    save_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            with tqdm(
                    desc=f"下载 {filename}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=100
            ) as bar:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

        downloaded_size = os.path.getsize(save_path)
        if abs(downloaded_size - total_size) > 1024 * 1024:
            # 允许少量误差
            raise Exception(f"文件大小不匹配 (预期: {total_size}B, 实际: {downloaded_size}B)，下载可能中断或链接已失效。")

        # print(f"✅ 歌曲文件下载成功！")
        # print(f"🎶 文件已保存到: {save_path}")
        return True

    except requests.RequestException as e:
        print(f"\n❌ 下载请求失败: {e}")
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"已删除不完整歌曲文件: {filename}")
        return False
    except Exception as e:
        print(f"\n❌ 下载或写入歌曲文件时发生错误: {e}")
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"已删除不完整歌曲文件: {filename}")
        return False


def save_lyrics(filename_base: str, lyrics_data: Dict[str, Any]):
    """将 LRC 歌词保存为 .lrc 文件。"""

    lrc_filename = f"{filename_base}.lrc"
    save_path = os.path.join(DOWNLOAD_DIR, lrc_filename)

    lyrics_content = ""
    if lyrics_data.get('lrc'):
        lyrics_content = lyrics_data['lrc']
    else:
        # print("❌ 歌词数据中没有找到可保存的LRC内容。")
        return False

    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(lyrics_content)

        # print(f"✅ 歌词文件保存成功！")
        # print(f"📝 歌词已保存到: {save_path}")
        return True

    except Exception:
        # print(f"❌ 歌词文件写入失败: {e}")
        return False


# --- 核心流程：处理单首歌曲下载 ---

def download_single_song(selected_song: Dict[str, Any]):
    """处理单首歌曲的下载和歌词保存，作为多选调用的子函数。"""

    song_id = selected_song['id']
    song_name = selected_song['song']
    song_singer = selected_song['singer']

    print(f"\n--- 开始处理: {song_name} - {song_singer} ---")

    # 1. 获取歌曲 URL 详情
    details = get_song_url(song_id)
    if not (details and details.get('url')):
        print("❌ 歌曲链接获取失败或API未提供有效URL。")
        return

    # 准备文件信息
    file_name_base = f"{song_name} - {song_singer}_{song_id}"
    music_filename = f"{file_name_base}.flac"
    size_str = details.get('size', '5MB').replace('MB', '')

    try:
        size_mb = float(size_str)
        total_size_bytes = int(size_mb * 1024 * 1024)
    except ValueError:
        size_mb = 5.0
        total_size_bytes = 5 * 1024 * 1024

        # 2. 真实下载歌曲文件
    download_success = actual_download(music_filename, details['url'], total_size_bytes)

    # 3. 获取并保存歌词
    if download_success:
        lyrics_data = get_song_lyrics(song_id)
        if lyrics_data:
            if save_lyrics(file_name_base, lyrics_data):
                print(f"✅ 歌词文件已保存到: {os.path.join(DOWNLOAD_DIR, file_name_base)}.lrc")
            else:
                print("⚠️ 歌词获取成功但保存失败。")
        else:
            print("⚠️ 未找到歌词信息。")

    print(f"--- 处理完成: {song_name} - {song_singer} ---\n")


# --- 解析用户多选输入 ---

def parse_selection_input(input_str: str, max_index: int) -> List[int] | None:
    """
    解析用户输入 (e.g., '1', '1,3,5', '2-6', 'all') 为一个索引列表 (0-based)。
    返回一个包含有效序号（从0开始）的列表。
    """
    input_str = input_str.strip().lower().replace(' ', '')
    selected_indices = set()

    if input_str == 'all':
        return list(range(max_index))

    parts = input_str.split(',')

    for part in parts:
        if '-' in part:
            # 处理范围选择 '2-6'
            try:
                start_str, end_str = part.split('-', 1)
                start = int(start_str)
                end = int(end_str)

                # 确保范围有效且在界限内
                if 1 <= start <= max_index and 1 <= end <= max_index and start <= end:
                    for i in range(start, end + 1):
                        selected_indices.add(i - 1)
                else:
                    print(f"⚠️ 范围选择 '{part}' 无效或超出列表范围 (1-{max_index})。")
                    return None
            except ValueError:
                print(f"⚠️ 范围格式 '{part}' 不正确。")
                return None
        else:
            # 处理单个序号 '3'
            try:
                index = int(part)
                if 1 <= index <= max_index:
                    selected_indices.add(index - 1)
                else:
                    print(f"⚠️ 序号 '{part}' 超出列表范围 (1-{max_index})。")
                    return None
            except ValueError:
                print(f"⚠️ 序号格式 '{part}' 不正确。")
                return None

    return sorted(list(selected_indices))


# --- 主程序 CLI ---

def main_cli():
    """主命令行交互循环，支持多选下载。"""

    ensure_download_dir()

    while True:
        try:
            user_input = input(
                "\n请输入您想搜索的音乐或歌手 (格式: '歌名-歌手', '歌名 歌手', 纯歌手名 或 纯歌名; 输入 2 退出): "
            ).strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n程序中断。")
            break

        if user_input == '2':
            print("程序退出。")
            break

        if not user_input:
            continue

        search_results = search_music(user_input)
        if not search_results:
            print("❌ 未找到任何匹配结果。")
            print("-" * 60)
            continue

        # 1. 尝试精确匹配 (歌名+歌手)
        exact_match = find_best_match(user_input, search_results)

        if exact_match:
            print(f"ℹ️ 找到精确匹配歌曲: {exact_match['song']} - {exact_match['singer']}。")
            confirm = input("是否获取链接并开始下载（含歌词）？(y/n，默认y): ").strip().lower()
            if confirm in ('y', ''):
                download_single_song(exact_match)
            print("-" * 60)
            continue

        # 2. 如果是纯歌手或纯歌名，展示所有结果供用户选择
        print(f"ℹ️ 检测到纯歌名或纯歌手名指令 '{user_input}'。")
        print("\n--- 搜索结果列表（未找到精确匹配）：---")
        for i, song in enumerate(search_results):
            print(f"[{i + 1:2}] {song['song']} - {song['singer']} ({song.get('interval', '时长未知')})")

        max_index = len(search_results)

        while True:
            try:
                choice = input(
                    f"请输入歌曲序号 (1-{max_index})，支持多选 (e.g., '1,3,5' 或 '2-6' 或 'all')，或输入 'n' 跳过: "
                ).strip()

                if choice.lower() == 'n':
                    print("-" * 60)
                    break

                selected_indices = parse_selection_input(choice, max_index)

                if selected_indices is None:
                    continue

                if not selected_indices:
                    print("⚠️ 未选择任何有效歌曲。")
                    continue

                print(f"\n即将下载 {len(selected_indices)} 首歌曲...")

                # 遍历并下载所有选中的歌曲
                for index in selected_indices:
                    song = search_results[index]
                    download_single_song(song)

                print("-" * 60)
                break

            except Exception as e:
                print(f"⚠️ 发生未知错误: {e}")


# --- 运行主程序 ---
if __name__ == '__main__':
    main_cli()