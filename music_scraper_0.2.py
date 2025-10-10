import requests
import json
import urllib.parse
import os
import time
from datetime import datetime
from tqdm import tqdm  # 用于显示下载进度条


class MyFreeMp3Scraper:
    """
    用于抓取 MyFreeMp3 网站音乐的 Python 封装类。
    支持获取热门关键词、搜索音乐以及下载音乐文件。
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
            # 如果需要，可以在这里手动添加或更新Cookie，但requests.Session通常会处理好
            # "Cookie": "UM_distinctid=...; CNZZDATA1281319036=..."
        })

    def get_hot_keywords(self):
        """
        获取网站的热门搜索关键词列表。
        """
        hotkey_url = self.base_url + "tdhot.php"

        # 动态生成 searchid，模拟浏览器
        search_id = str(int(time.time() * 1000)) + str(int(time.time() * 100 % 100)).zfill(2)  # 确保是两位数

        # 构建 hotkey_data 字典
        hotkey_data_dict = {
            "hotkey": {
                "module": "tencent_musicsoso_hotkey.HotkeyService",
                "method": "GetHotkeyForQQMusicMobile",
                "param": {
                    "remoteplace": "txt.miniapp.wxada7aab80ba27074",
                    "searchid": search_id  # 使用动态生成的 searchid
                }
            }
        }

        # 将字典转换为 JSON 字符串，并进行 URL 编码
        encoded_data = urllib.parse.quote(json.dumps(hotkey_data_dict))

        params = {
            "td": "1",
            "data": encoded_data
        }

        print("正在获取热门关键词...")
        try:
            response = self.session.get(hotkey_url, params=params, timeout=10)
            response.raise_for_status()  # 检查HTTP请求是否成功

            # 网站返回的JSON可能不是标准的UTF-8，可能会有Unicode转义
            # requests会自动处理大部分编码，但如果直接拿到text，中文会显示为 `\uXXXX`
            # 此时使用 json.loads 转换即可
            hot_keywords_raw = json.loads(response.text)

            keywords = [item[0] for item in hot_keywords_raw]
            print("热门关键词获取成功！")
            return keywords
        except requests.exceptions.RequestException as e:
            print(f"获取热门关键词失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"解析热门关键词响应失败: {e}.")
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type')}")
            print(f"Response Body (first 200 chars): {response.text[:200]}...")
            return None

    def search_music(self, keyword, page=1, music_type="netease"):
        """
        根据关键字搜索音乐。

        Args:
            keyword (str): 要搜索的音乐关键词（歌曲名或歌手名）。
            page (int): 搜索结果的页码，默认为1。
            music_type (str): 音乐来源类型，默认为 "netease" (网易云)。
                              其他可能的值包括 "qq" 等，但根据提供的载荷，这里只使用netease。

        Returns:
            list: 包含音乐信息的字典列表，每个字典包含 'title', 'author', 'url_128', 'pic' 等。
                  如果失败，返回 None。
        """
        search_url = self.base_url  # 搜索请求的URL就是基URL

        # POST请求的载荷
        payload = {
            "input": keyword,
            "filter": "name",  # 根据提供的载荷，filter为name
            "page": str(page),
            "type": music_type
        }

        # 更新POST请求特有的headers
        post_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url.rstrip('/'),  # 去掉末尾斜杠以匹配提供的Origin
            "Referer": self.base_url  # Referer通常是当前页面URL
        }
        self.session.headers.update(post_headers)

        print(f"正在搜索 '{keyword}' (第 {page} 页)...")
        try:
            response = self.session.post(search_url, data=payload, timeout=10)
            response.raise_for_status()  # 检查HTTP请求是否成功

            # --- 新增的健壮性检查：检查Content-Type ---
            content_type = response.headers.get('Content-Type', '').lower()
            if 'json' not in content_type and 'javascript' not in content_type:
                print(f"第 {page} 页搜索 '{keyword}' 失败。服务器返回内容不是JSON (Content-Type: {content_type})。")
                print(f"HTTP Status Code: {response.status_code}")
                print(f"Response Body (first 500 chars): {response.text[:500]}...")
                return []  # 返回空列表，表示当前页无结果

            result_json = response.json()

            if result_json.get("code") == 200 and result_json.get("data") and result_json["data"].get("list"):
                music_list = result_json["data"]["list"]
                print(f"第 {page} 页搜索成功，找到 {len(music_list)} 首歌曲。")

                # 提取并格式化所需信息
                formatted_list = []
                for music in music_list:
                    formatted_list.append({
                        "title": music.get("title"),
                        "author": music.get("author"),
                        "url_128": music.get("url_128"),  # 128kbps音质链接
                        "url_320": music.get("url_320"),  # 320kbps音质链接
                        "pic": music.get("pic"),  # 专辑封面
                        "songid": str(music.get("songid"))  # 转换为字符串，方便去重
                    })
                return formatted_list
            else:
                print(
                    f"第 {page} 页搜索 '{keyword}' 失败或未找到歌曲。错误信息: {result_json.get('error') or 'Unspecified Error'}")
                print(f"完整响应: {result_json}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"搜索音乐失败 (第 {page} 页 - 网络或HTTP错误): {e}")
            return None  # 返回 None 表示发生更严重的网络错误，可能需要停止多页爬取
        except json.JSONDecodeError as e:
            print(f"解析搜索响应失败 (第 {page} 页 - JSON格式错误): {e}.")
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type')}")
            print(f"Response Body (first 500 chars): {response.text[:500]}...")
            return []  # 返回空列表，表示当前页无结果

    def download_music(self, music_info, quality='128', save_dir="downloads"):
        """
        下载音乐文件到本地。增强健壮性。

        Args:
            music_info (dict): 包含音乐信息（如title, author, url_128, url_320, songid）的字典。
            quality (str): '128' 或 '320'，选择下载音质。
            save_dir (str): 保存文件的目录，默认为 "downloads"。

        Returns:
            str or None: 下载成功则返回文件路径，否则返回 None。
        """
        title = music_info.get('title', '未知歌曲')
        author = music_info.get('author', '未知歌手')
        songid = music_info.get('songid', '未知ID')

        music_url = music_info.get(f'url_{quality}')
        if not music_url:
            print(f"警告: 歌曲 '{title}' 没有找到 {quality}kbps 音质的下载链接。尝试自动切换到 128kbps。")
            music_url = music_info.get('url_128')
            if not music_url:
                print(f"下载链接为空 ({quality}kbps 和 128kbps 均无)，无法下载 '{title}'。")
                return None
            else:
                print("已切换到 128kbps 下载链接。")
                quality = '128'  # 更新实际使用的音质标记

        # 清理文件名中不允许的字符
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).strip()
        safe_author = "".join(c for c in author if c.isalnum() or c in (' ', '.', '_')).strip()

        # 确保filename的长度合理，避免过长导致文件系统问题
        max_filename_len = 100
        filename_base = f"{safe_title} - {safe_author}_{songid}"
        if len(filename_base) > max_filename_len - len(f"_{quality}kbps.mp3"):
            filename_base = filename_base[:max_filename_len - len(f"_{quality}kbps.mp3")]

        filename = f"{filename_base}_{quality}kbps.mp3"

        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)

        print(f"正在下载 '{filename}' (原链接: {music_url}) 到 '{file_path}'...")
        try:
            # 使用 stream=True 边下边存，防止大文件一次性加载到内存
            response = self.session.get(music_url, stream=True, timeout=30)
            response.raise_for_status()

            # --- 健壮性检查 ---
            content_type = response.headers.get('Content-Type', '').lower()
            # 检查是否是音频类型，比如 audio/mpeg (MP3), audio/wav 等
            # 或者文件下载类型 application/octet-stream
            if not any(t in content_type for t in ['audio/', 'application/octet-stream', 'video/']):
                print(
                    f"警告: 下载 '{filename}' 时收到了非音频内容 (Content-Type: {content_type})，可能是错误页面。不保存文件。")
                print(f"最终下载链接 (可能经过重定向): {response.url}")
                return None

            total_size_in_bytes = int(response.headers.get("content-length", 0))
            if total_size_in_bytes < 500 * 1024 and total_size_in_bytes != 0:  # 500KB 以下且非0的，很可能是无效文件，具体数值可调整
                print(
                    f"警告: 下载 '{filename}' 文件大小异常小 ({total_size_in_bytes / 1024:.2f} KB)。可能不是完整的音乐文件。")
                print(f"最终下载链接 (可能经过重定向): {response.url}")
            elif total_size_in_bytes == 0:
                print(f"警告: 下载 '{filename}' 文件大小为 0 KB。可能是下载失败。不保存文件。")
                print(f"最终下载链接 (可能经过重定向): {response.url}")
                return None

            with open(file_path, 'wb') as f:
                # 使用 tqdm 显示下载进度
                # miniters=1 确保即使文件很小也能显示进度条
                with tqdm(total=total_size_in_bytes, unit='B', unit_scale=True, desc=filename, ascii=True,
                          miniters=1) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            print(f"'{filename}' 下载完成！")
            return file_path
        except requests.exceptions.RequestException as e:
            print(f"下载 '{filename}' 失败 (网络或HTTP错误): {e}")
            print(f"尝试下载的原始链接: {music_url}")
            return None


# --- 主程序逻辑 ---
if __name__ == "__main__":
    scraper = MyFreeMp3Scraper()

    # 1. 获取热门关键词
    hot_keywords = scraper.get_hot_keywords()
    if hot_keywords:
        print("\n--- 热门搜索关键词 ---")
        for i, keyword in enumerate(hot_keywords[:10]):  # 只显示前10个
            print(f"{i + 1}. {keyword}")
        print("---------------------\n")

    # 2. 搜索关键字 (支持多页)
    search_query = input("请输入您想搜索的音乐或歌手: ")
    if not search_query:
        search_query = "周杰伦"  # 默认搜索热门歌手便于测试

    try:
        max_search_pages = int(input("请输入您想搜索的最大页数 (例如 3，每页约10首): ") or 3)  # 默认搜3页
    except ValueError:
        print("页数输入无效，将使用默认值 3。")
        max_search_pages = 3

    download_quality = input("请输入下载音质 ('128' 或 '320', 默认 128): ") or '128'
    if download_quality not in ['128', '320']:
        print("音质选择无效，将使用默认值 128。")
        download_quality = '128'

    all_music_results = []
    seen_song_ids = set()  # 用于去重

    current_page = 1
    while current_page <= max_search_pages:
        page_results = scraper.search_music(search_query, page=current_page)

        if page_results is None:  # 在 search_music 里，只有网络或HTTP错误会返回None
            print(f"在获取第 {current_page} 页时发生网络错误，停止多页搜索。")
            break

        if not page_results:  # 当前页没有结果，或者服务器返回了非JSON内容/错误JSON
            print(f"第 {current_page} 页未找到更多结果或请求被拒绝，停止多页搜索。")
            break

        for music in page_results:
            if music['songid'] not in seen_song_ids:
                all_music_results.append(music)
                seen_song_ids.add(music['songid'])

        print(f"已获取 {len(all_music_results)} 首不重复的歌曲结果。")
        current_page += 1
        time.sleep(1)  # 增加暂停时间，减少被屏蔽的风险

    if all_music_results:
        print(f"\n--- 找到 {len(all_music_results)} 首歌曲 ---")
        for i, music in enumerate(all_music_results):
            print(f"{i + 1}. 歌曲: {music['title']} - 歌手: {music['author']} (ID: {music['songid']})")
        print("-------------------------------------------\n")

        # 3. 选择音乐并下载
        if len(all_music_results) > 0:
            try:
                choice = int(input(f"请输入您想下载的歌曲序号 (1-{len(all_music_results)}, 输入 0 放弃下载): "))
                if 1 <= choice <= len(all_music_results):
                    selected_music = all_music_results[choice - 1]

                    download_path = scraper.download_music(selected_music, quality=download_quality)
                    if download_path:
                        print(f"音乐已保存到: {download_path}")
                    else:
                        print("音乐下载失败或被拒绝。")
                elif choice == 0:
                    print("放弃下载。")
                else:
                    print("无效的序号。")
            except ValueError:
                print("输入无效，请输入数字。")
        else:
            print("没有歌曲可供下载。")
    else:
        print("未找到相关音乐。")

    print("\n程序执行完毕。")
