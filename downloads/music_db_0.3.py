import requests
import json
import urllib.parse
import os
import time
from datetime import datetime
import pymysql
from tqdm import tqdm

# --- 数据库配置信息 ---
# 这些信息需要与 docker-compose.yml 中设置的保持一致
DB_CONFIG = {
    'host': '10.10.10.130',  # 请确保这个IP地址是您的MySQL服务可达的IP
    'port': 3306,
    'user': 'scraper_user',  # !!! 替换为你的 MySQL 用户名
    'password': '3971247',  # !!! 替换为你的 MySQL 密码
    'database': 'music_data',  # !!! 替换为你的数据库名
    'charset': 'utf8mb4',
    'connect_timeout': 10  # 连接超时时间，防止长时间阻塞
}


class MusicDatabaseManager:
    """
    负责管理音乐数据的数据库操作。
    """

    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self._get_connection()  # 尝试在初始化时就建立连接

    def _get_connection(self):
        """获取或创建数据库连接"""
        if self.conn is None or not self.conn.open:
            print(
                f"尝试连接数据库: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']} with user {self.db_config['user']}...")
            try:
                self.conn = pymysql.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['database'],
                    charset=self.db_config['charset'],
                    connect_timeout=self.db_config.get('connect_timeout', 10)
                )
                print("数据库连接成功！")
            except pymysql.OperationalError as e:
                print(f"ERROR: 数据库连接失败 (Operational Error - 可能是参数错误、网络不通或MySQL未启动): {e}")
                self.conn = None
            except pymysql.Error as e:
                print(f"ERROR: 数据库连接失败 (General pymysql Error): {e}")
                self.conn = None
            except Exception as e:
                print(f"ERROR: 数据库连接时发生未知错误: {e}")
                self.conn = None
        return self.conn

    def insert_music_tracks(self, music_list):
        """
        批量插入音乐数据到数据库。
        使用 REPLACE INTO 语句实现插入或更新，并防止重复插入。
        """
        if not music_list:
            return 0

        conn = self._get_connection()
        if not conn:
            print("警告: 数据库连接不可用，未能插入音乐数据。")
            return 0

        inserted_count = 0
        try:
            with conn.cursor() as cursor:
                sql = """
                      REPLACE \
                      INTO music_tracks 
                (songid, title, author, url_128, url_320, pic)
                VALUES ( \
                      %s, \
                      %s, \
                      %s, \
                      %s, \
                      %s, \
                      %s \
                      ) \
                      """
                for music in music_list:
                    try:
                        cursor.execute(sql, (
                            music.get('songid'),
                            music.get('title'),
                            music.get('author'),
                            music.get('url_128'),
                            music.get('url_320'),
                            music.get('pic')
                        ))
                        inserted_count += 1
                    except pymysql.IntegrityError as e:
                        title = music.get('title', 'N/A')
                        songid = music.get('songid', 'N/A')
                        print(f"警告: 歌曲 '{title}' (ID: {songid}) 插入/更新失败，可能是键冲突或数据截断: {e}")
                    except pymysql.Error as e:
                        title = music.get('title', 'N/A')
                        songid = music.get('songid', 'N/A')
                        print(f"插入歌曲 '{title}' (ID: {songid}) 时发生数据库错误: {e}")
                conn.commit()
        except pymysql.Error as e:
            conn.rollback()
            print(f"批量插入音乐数据时发生数据库事务错误: {e}")
        finally:
            pass
        return inserted_count

    def close(self):
        """关闭数据库连接"""
        if self.conn and self.conn.open:
            self.conn.close()
            self.conn = None
            print("数据库连接已关闭。")


class MyFreeMp3Scraper:
    """
    用于抓取 MyFreeMp3 网站音乐的 Python 封装类。
    支持获取热门关键词、搜索音乐。
    """

    def __init__(self):
        self.base_url = "https://www.myfreemp3.com.cn/"
        self.session = requests.Session()
        self._set_common_headers()

        # 模拟访问首页，以获取可能存在的会话 Cookie。
        # 即使手动设置了Cookie Header，Session仍会管理其他Set-Cookie
        print(f"初始化Session，模拟首次访问 {self.base_url} 以获取最新Cookies...")
        try:
            initial_response = self.session.get(self.base_url, timeout=10)
            initial_response.raise_for_status()
            print(f"首页访问成功，获取到 {len(self.session.cookies)} 个Cookie。")
            # 打印一下Session中当前存在的Cookie，用于调试
            # print("当前Session Cookies:", dict(self.session.cookies))
        except requests.exceptions.RequestException as e:
            print(f"警告: 模拟访问首页失败，可能影响后续请求的Cookie携带: {e}")

    def _set_common_headers(self):
        """
        设置会话的通用请求头。
        完全复制浏览器成功请求时的所有关键Header，包括最新的Cookie。
        """
        # !!! 这是最关键的修改，使用您提供的最新且完整的Cookie字符串作为Header
        # 注意：这个Cookie可能会过期，如果再次出现问题，您需要从浏览器中获取最新的
        latest_full_cookie_string = "UM_distinctid=1990d8e64ba4c9-0ead8f9b44a795-26011051-100200-1990d8e64bb14d; CNZZDATA1281319036=827025939-1756869060-https%253A%252F%252Fcn.bing.com%252F%7C175687656"

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": latest_full_cookie_string,  # 直接设置完整的Cookie Header
            "DNT": "1",
            "Priority": "u=1, i",  # 确保这个头被包含
            "Sec-Ch-Ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",  # !!! 确保这个头被包含
            # Origin 和 Referer 是针对POST请求的，我们会在 search_music 方法中单独设置
            # 因为它们的值通常是当前页面的URL，或根据请求类型动态变化
        })

    def get_hot_keywords(self):
        """
        获取网站的热门搜索关键词列表。
        此方法中，由于服务器即使返回JSON也可能使用text/html作为Content-Type，
        我们只检查JSON解析是否成功，而不是严格检查Content-Type。
        """
        hotkey_url = self.base_url + "tdhot.php"

        search_id = str(int(time.time() * 1000)) + str(int(time.time() * 100 % 100)).zfill(2)

        hotkey_data_dict = {
            "hotkey": {
                "module": "tencent_musicsoso_hotkey.HotkeyService",
                "method": "GetHotkeyForQQMusicMobile",
                "param": {
                    "remoteplace": "txt.miniapp.wxada7aab80ba27074",
                    "searchid": search_id
                }
            }
        }

        encoded_data = urllib.parse.quote(json.dumps(hotkey_data_dict))

        params = {
            "td": "1",
            "data": encoded_data
        }

        print("正在获取热门关键词...")
        try:
            response = self.session.get(hotkey_url, params=params, timeout=10)
            response.raise_for_status()

            # 放松 Content-Type 检查，直接尝试解析 JSON
            hot_keywords_raw = json.loads(response.text)

            keywords = [item[0] for item in hot_keywords_raw]
            print("热门关键词获取成功！")
            return keywords
        except requests.exceptions.RequestException as e:
            print(f"获取热门关键词失败 (网络或HTTP错误): {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"解析热门关键词响应失败 (JSON格式错误): {e}.")
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type')}")
            print(f"Response Body (first 500 chars): {response.text[:500]}...")
            return None

    def search_music(self, keyword, page=1, music_type="netease"):
        """
        分页搜索音乐。
        这个方法将直接返回音乐列表，不进行数据库操作。
        """
        search_url = self.base_url

        payload = {
            "input": keyword,
            "filter": "name",
            "page": str(page),
            "type": music_type
        }

        # POST请求特有的headers，这些在Session中设置的通用headers基础上进行更新或添加
        # 注意：这里不能用 self.session.headers.update(post_headers)
        # 因为 headers 每次请求都会被 Session 维护。我们直接在请求中传入 headers
        # 确保每次请求都有最新的 Origin/Referer
        request_headers = self.session.headers.copy()  # 复制会话的当前头，然后修改
        request_headers.update({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url.rstrip('/'),
            "Referer": self.base_url
            # X-Requested-With, Priority, etc. 已经在 common headers 里了
        })

        print(f"正在搜索 '{keyword}' (第 {page} 页)...")
        try:
            response = self.session.post(search_url, data=payload, headers=request_headers, timeout=10)
            response.raise_for_status()

            # For search results, we strictly expect JSON. If HTML is returned, it means anti-bot.
            content_type = response.headers.get('Content-Type', '').lower()
            if 'json' not in content_type and 'javascript' not in content_type:
                print(
                    f"WARNING: 第 {page} 页搜索 '{keyword}' 失败。服务器返回内容不是JSON (Content-Type: {content_type})。")
                print(f"HTTP Status Code: {response.status_code}")
                # print(f"Response Headers: {response.headers}") # 调试时可以取消注释
                print(f"Response Body (first 500 chars): {response.text[:500]}...")
                return []

            result_json = response.json()

            if result_json.get("code") == 200 and result_json.get("data") and result_json["data"].get("list"):
                music_list = result_json["data"]["list"]
                print(f"第 {page} 页搜索成功，找到 {len(music_list)} 首歌曲。")

                formatted_list = []
                for music in music_list:
                    formatted_list.append({
                        "title": music.get("title"),
                        "author": music.get("author"),
                        "url_128": music.get("url_128"),
                        "url_320": music.get("url_320"),
                        "pic": music.get("pic"),
                        "songid": str(music.get("songid"))
                    })
                return formatted_list
            else:
                print(
                    f"第 {page} 页搜索 '{keyword}' 失败或未找到歌曲。错误信息: {result_json.get('error') or 'Unspecified Error'}")
                print(f"完整响应: {result_json}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"搜索音乐失败 (第 {page} 页 - 网络或HTTP错误): {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"解析搜索响应失败 (第 {page} 页 - JSON格式错误): {e}.")
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type')}")
            # print(f"Response Headers: {response.headers}") # 调试时可以取消注释
            print(f"Response Body (first 500 chars): {response.text[:500]}...")
            return []


# --- 主程序逻辑 ---
if __name__ == "__main__":
    print("Python script started.")

    # 初始化数据库管理器
    db_manager = MusicDatabaseManager(DB_CONFIG)
    if not db_manager._get_connection():
        print("\n数据库连接失败，请检查 MySQL 服务和配置。程序将退出。")
        exit(1)

    scraper = MyFreeMp3Scraper()

    # 1. 获取热门关键词
    hot_keywords = scraper.get_hot_keywords()
    if hot_keywords:
        print("\n--- 热门搜索关键词 ---")
        for i, keyword in enumerate(hot_keywords[:10]):
            print(f"{i + 1}. {keyword}")
        print("---------------------\n")
    else:
        print("\n未能获取到热门关键词。\n")

    # 2. 用户输入搜索参数
    search_query = input("请输入您想搜索的音乐或歌手: ")
    if not search_query:
        search_query = "周杰伦"

    try:
        max_search_pages = int(input("请输入您想搜索的最大页数 (例如 3，每页约10首): ") or 3)
    except ValueError:
        print("页数输入无效，将使用默认值 3。")
        max_search_pages = 3

    # 3. 分页爬取并写入数据库
    total_newly_inserted = 0
    seen_song_ids = set()

    current_page = 1
    while current_page <= max_search_pages:
        page_music_results = scraper.search_music(search_query, page=current_page)

        if page_music_results is None:
            print(f"在获取第 {current_page} 页时发生网络错误，停止多页搜索。")
            break

        if not page_music_results and current_page > 1:
            print(f"第 {current_page} 页未找到更多结果或请求被拒绝，停止多页搜索。")
            break

        # 如果第一页就没结果，但并非网络错误，也应该停止（空列表情况）
        if not page_music_results and current_page == 1:
            print(f"第 {current_page} 页未找到任何结果。")
            break

        new_music_to_insert = []
        for music in page_music_results:
            if music['songid'] not in seen_song_ids:
                new_music_to_insert.append(music)
                seen_song_ids.add(music['songid'])

        if new_music_to_insert:
            print(f"准备将 {len(new_music_to_insert)} 条新数据从第 {current_page} 页写入数据库...")
            inserted_count = db_manager.insert_music_tracks(new_music_to_insert)
            total_newly_inserted += inserted_count
        else:
            print(f"第 {current_page} 页没有新的不重复歌曲数据可写入数据库。")

        current_page += 1
        time.sleep(3)  # 增加暂停时间到3秒

    print(f"\n--- 爬取与数据库写入完成 ---")
    print(f"总计从网站抓取并处理了 {len(seen_song_ids)} 首歌曲数据。")
    print(f"其中 {total_newly_inserted} 条数据被新插入或更新到数据库。")
    print("----------------------------\n")

    # 关闭数据库连接
    db_manager.close()
    print("\n程序执行完毕。")
