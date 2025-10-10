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
            "X-Requested-With": "XMLHttpRequest",
            # 注意：Cookie通常由requests自动管理，或者需要根据实际抓取情况动态获取
            # 但作为起始请求，可以先不设置，或者设置一个示例。
            # "Cookie": "UM_distinctid=...; CNZZDATA1281319036=..."
        })

    def get_hot_keywords(self):
        """
        获取网站的热门搜索关键词列表。
        """
        hotkey_url = self.base_url + "tdhot.php"

        # 动态生成 searchid，模拟浏览器
        search_id = str(int(time.time() * 1000)) + str(int(time.time() * 100 % 100))

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
            print(f"解析热门关键词响应失败: {e}. 响应内容: {response.text[:200]}")
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

            result_json = response.json()

            if result_json.get("code") == 200 and result_json.get("data") and result_json["data"].get("list"):
                music_list = result_json["data"]["list"]
                print(f"搜索 '{keyword}' 成功，找到 {len(music_list)} 首歌曲。")

                # 提取并格式化所需信息
                formatted_list = []
                for music in music_list:
                    formatted_list.append({
                        "title": music.get("title"),
                        "author": music.get("author"),
                        "url_128": music.get("url_128"),  # 128kbps音质链接
                        "url_320": music.get("url_320"),  # 320kbps音质链接
                        "pic": music.get("pic"),  # 专辑封面
                        "songid": music.get("songid")
                    })
                return formatted_list
            else:
                print(f"搜索 '{keyword}' 失败或未找到歌曲。响应: {result_json.get('error') or result_json}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"搜索音乐失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"解析搜索响应失败: {e}. 响应内容: {response.text[:200]}")
            return None

    def download_music(self, music_url, filename, save_dir="downloads"):
        """
        下载音乐文件到本地。

        Args:
            music_url (str): 音乐文件的下载URL。
            filename (str): 保存到本地的文件名（包含扩展名，如 ".mp3"）。
            save_dir (str): 保存文件的目录，默认为 "downloads"。

        Returns:
            str or None: 下载成功则返回文件路径，否则返回 None。
        """
        if not music_url:
            print("下载链接为空，无法下载。")
            return None

        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)

        print(f"正在下载 '{filename}' 到 '{file_path}'...")
        try:
            # 使用 stream=True 边下边存，防止大文件一次性加载到内存
            response = self.session.get(music_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size_in_bytes = int(response.headers.get("content-length", 0))

            with open(file_path, 'wb') as f:
                # 使用 tqdm 显示下载进度
                with tqdm(total=total_size_in_bytes, unit='B', unit_scale=True, desc=filename, ascii=True) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            print(f"'{filename}' 下载完成！")
            return file_path
        except requests.exceptions.RequestException as e:
            print(f"下载 '{filename}' 失败: {e}")
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

    # 2. 搜索关键字
    search_query = input("请输入您想搜索的音乐或歌手: ")
    if not search_query:
        search_query = "阿杜"  # 默认搜索阿杜

    music_results = scraper.search_music(search_query)

    if music_results:
        print("\n--- 搜索结果 ---")
        for i, music in enumerate(music_results):
            print(f"{i + 1}. 歌曲: {music['title']} - 歌手: {music['author']} (ID: {music['songid']})")
        print("----------------\n")

        # 3. 选择音乐并下载
        try:
            choice = int(input("请输入您想下载的歌曲序号 (输入 0 放弃下载): "))
            if 1 <= choice <= len(music_results):
                selected_music = music_results[choice - 1]

                # 清理文件名中不允许的字符
                safe_title = "".join(c for c in selected_music['title'] if c.isalnum() or c in (' ', '.', '_')).strip()
                safe_author = "".join(
                    c for c in selected_music['author'] if c.isalnum() or c in (' ', '.', '_')).strip()

                filename = f"{safe_title} - {safe_author}_{selected_music['songid']}.mp3"

                download_path = scraper.download_music(selected_music['url_128'], filename)
                if download_path:
                    print(f"音乐已保存到: {download_path}")
            elif choice == 0:
                print("放弃下载。")
            else:
                print("无效的序号。")
        except ValueError:
            print("输入无效，请输入数字。")
    else:
        print("未找到相关音乐。")

    print("\n程序执行完毕。")
