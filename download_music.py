import requests
import re
import json
import urllib.parse
import time
import sys
import os
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup

# --- 全局配置 ---
# 注意：这些 Cookies 和 Headers 可能有有效期，如果代码运行失败，
# 务必从浏览器中获取最新的 Cookies 和 Headers 并更新这里的字典。
# 警告：请在 GitHub Secrets 中存储敏感信息，这里仅为示例。
cookies = {
    'Hm_tf_no8z3ihhnja': '1759891990',
    'Hm_lvt_no8z3ihhnja': '1759891990,1759914819,1759943487,1759975751',
    'Hm_lvt_49c19bcfda4e5fdfea1a9bb225456abe': '1759891991,1759914819,1759943486,1759975753',
    'HMACCOUNT': 'F2D39E6791DCFBD4',
    'PHPSESSID': 'ba8veihlq2066mpmrbvi4tngm3',
    'server_name_session': '48ac7eb90472522710b482184d07bcd6',
    'Hm_lpvt_49c19bcfda4e5fdfea1a9bb225456abe': '1759982677',
    'Hm_lpvt_no8z3ihhnja': '1759982679',
}

# (其余 Headers 保持不变，代码略)
get_html_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'priority': 'u=0, i',
    'referer': 'https://www.gequhai.com/s/%E9%82%93%E7%B4%AB%E6%A3%8B',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
}
post_api_headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'dnt': '1',
    'origin': 'https://www.gequhai.com',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'x-custom-header': 'SecretKey',
    'x-requested-with': 'XMLHttpRequest',
}


# --- 常量和配置 ---
INITIAL_REQUEST_DELAY = 1.0 
MAX_RETRIES = 3  
RETRY_DELAY_MULTIPLIER = 2  
DOWNLOAD_DIR = Path("downloads")  
FFMPEG_AVAILABLE = False  
RETRY_TIME_PATTERN = re.compile(r'请 (\d+) 秒后再试。')
BR_TAG_PATTERN = re.compile(r'<br\s*/?>', re.IGNORECASE)


def print_status(message, end='\n'):
    """统一的打印函数，方便管理输出"""
    print(message, end=end)
    sys.stdout.flush() 

# (sanitize_filename, check_ffmpeg_available, convert_aac_to_mp3, download_lyric_file, 
# download_music_file, get_song_details_from_html, get_music_url, search_songs 函数保持不变，代码略)
# 请确保将您的原完整函数复制到最终的 `download_music.py` 文件中！
# 避免文件过长，这里只展示修改后的 `__main__`。

# --- 主程序执行部分 (已修改为命令行模式) ---
if __name__ == "__main__":
    
    # 检查是否提供了命令行参数
    if len(sys.argv) < 2:
        print_status("错误: 缺少搜索关键词参数。用法: python download_music.py \"歌曲名 歌手名\"")
        # 退出状态码 1，表示执行失败
        sys.exit(1) 
    
    # 获取命令行参数，即搜索关键词
    search_query = sys.argv[1].strip()

    if not search_query:
        print_status("未输入搜索关键词，程序退出。")
        sys.exit(1) 

    print_status(f"--- 欢迎使用 GitHub Actions 音乐下载工作流 ---")
    print_status(f"【目标关键词】: '{search_query}'")
    
    # 预先检查 FFmpeg 可用性（在 Actions 环境中通常需要手动安装）
    if check_ffmpeg_available():
        print_status("【格式转换】FFmpeg 检查成功，AAC 文件将自动转换为 MP3。")
    else:
        print_status("【格式转换】FFmpeg 警告: 转换功能可能不可用。")
    print_status("-" * 20)

    # 1. 搜索歌曲
    found_songs = search_songs(search_query)

    if not found_songs:
        print_status(f"没有找到与 '{search_query}' 相关的歌曲。程序退出。")
        sys.exit(0)
    
    # --- 关键修改：只处理第一首歌曲 ---
    song_to_process = found_songs[0]
    
    print_status(f"\n--- 步骤 2: 目标歌曲 (列表第一首) ---")
    print_status(f"歌曲: {song_to_process['title']} - {song_to_process['artist']} (ID: {song_to_process['id']})")
    print_status("-" * 20)
    
    # 2. 获取播放链接和歌词
    music_data, lrc_content, txt_content = get_music_url(song_to_process['id'])

    # 3. 下载文件和歌词
    download_success = download_music_file(music_data.get('url') if music_data else None,
                                           song_to_process['title'],
                                           song_to_process['artist'],
                                           lrc_content,
                                           txt_content)
                                           
    print_status("-" * 20)
    if download_success:
        print_status(f"【成功】文件和歌词已下载/更新。")
        # 退出状态码 0，表示执行成功
        sys.exit(0)
    else:
        print_status(f"【失败】未能成功下载音乐文件。请检查源链接或 Cookies。")
        # 退出状态码 1，表示执行失败
        sys.exit(1)
