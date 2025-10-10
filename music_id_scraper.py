import requests
import json
import urllib.parse
import time
import math  # 虽然只取一个结果，但计算页数时仍然用到


class MyFreeMp3Scraper:
    """
    用于抓取 MyFreeMp3 网站音乐的 Python 封装类。
    支持搜索音乐并获取第一个匹配歌曲的名称、歌手和ID。
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

    def search_music(self, keyword, music_type="netease"):
        """
        根据关键字搜索音乐，只返回第一个匹配的歌曲信息。

        Args:
            keyword (str): 要搜索的音乐关键词（歌曲名或歌手名）。
            music_type (str): 音乐来源类型，默认为 "netease" (网易云)。

        Returns:
            dict or None: 包含 'title', 'author', 'songid' 的字典，
                          如果未找到则返回 None。
        """
        search_url = self.base_url

        # 只需要请求第一页来获取第一个结果
        page_to_fetch = 1

        post_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url.rstrip('/'),
            "Referer": self.base_url
        }
        self.session.headers.update(post_headers)

        print(f"正在搜索 '{keyword}'...")

        payload = {
            "input": keyword,
            "filter": "name",
            "page": str(page_to_fetch),  # 只请求第一页
            "type": music_type
        }

        try:
            response = self.session.post(search_url, data=payload, timeout=10)
            response.raise_for_status()

            result_json = response.json()

            if result_json.get("code") == 200 and result_json.get("data") and result_json["data"].get("list"):
                # 只取第一个结果
                first_music = result_json["data"]["list"][0]

                # 格式化并返回
                formatted_result = {
                    "title": first_music.get("title", "未知歌曲"),
                    "author": first_music.get("author", "未知歌手"),
                    "songid": first_music.get("songid", "N/A")
                }
                print(
                    f"找到歌曲: {formatted_result['title']} - {formatted_result['author']} (ID: {formatted_result['songid']})")
                return formatted_result
            else:
                error_msg = result_json.get('error') or result_json.get('msg') or "未知错误"
                print(f"搜索失败或未找到歌曲。响应详情: {error_msg}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"搜索请求失败: {e}")
            return None
        except (json.JSONDecodeError, IndexError) as e:  # IndexError 用于处理列表为空的情况
            print(f"解析搜索响应失败或未找到歌曲: {e}. 响应内容: {response.text[:200]}")
            return None
        except Exception as e:
            print(f"发生未知错误: {e}")
            return None


# --- 主程序逻辑 ---
if __name__ == "__main__":
    scraper = MyFreeMp3Scraper()

    # 搜索关键字
    search_query = input("请输入您想搜索的音乐或歌手: ").strip()

    if not search_query:
        print("输入为空，将为您搜索默认歌曲 '唯一'。")
        search_query = "唯一"  # 更改默认搜索词以符合示例

    music_result = scraper.search_music(search_query)  # 不再需 target_count 参数

    if music_result:
        # 直接打印找到的第一首歌的详细信息
        print(f"\n找到歌曲ID: {music_result['songid']}")
    else:
        print(f"未找到 '{search_query}' 的相关歌曲。")

    print("\n程序执行完毕。")
