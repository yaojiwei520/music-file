import requests
import json
import sys
from typing import Dict, List, Any, Optional


class NeteaseAPIClient:
    """
    一个简单的网易云音乐API客户端，用于搜索单曲。
    """
    BASE_URL = "https://apis.netstart.cn/music"

    def __init__(self, cookies: Optional[Dict[str, str]] = None):
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://music.163.com/',
        })
        if cookies:
            self._session.cookies.update(cookies)

    def _make_request(self, endpoint: str, params: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
        """
        封装请求发送和JSON解析，提供基本的错误处理。
        Args:
            verbose: 如果为True，打印详细的请求信息。
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            if verbose:
                print(f"DEBUG: 请求URL: {url}")
                print(f"DEBUG: 请求参数: {params}")

            response = self._session.get(url, params=params, timeout=10)
            response.raise_for_status()  # 检查HTTP响应状态码，如果不是2xx，则抛出HTTPError

            json_response = response.json()
            if verbose:
                print(f"DEBUG: 接收到响应 Code: {json_response.get('code')}")
            return json_response

        except requests.exceptions.HTTPError as e:
            # 对于HTTP错误，仍然打印详细信息供调试，但对外只抛简化错误
            raise Exception(f"API请求失败 (HTTP {e.response.status_code}): {e.response.text.strip()}")
        except requests.exceptions.Timeout:
            raise Exception("API请求超时，请检查网络连接。")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接失败，请检查您的网络。")
        except json.JSONDecodeError as e:
            raise Exception(f"API响应数据格式错误: {e}. 原始响应可能不是JSON。")
        except Exception as e:
            raise Exception(f"发生未知错误: {e}")

    def search_song_by_name(self, song_name: str, artist_name: Optional[str] = None, limit: int = 5, offset: int = 0,
                            verbose_debug: bool = False) -> List[Dict[str, Any]]:
        """
        根据歌曲名称和歌手名称使用 `/cloudsearch` 接口搜索单曲，
        并返回歌曲ID、名称、艺术家和专辑信息。

        Args:
            song_name: 要搜索的歌曲名称。
            artist_name: 可选的歌手名称，用于提高搜索精度。
            limit: 返回结果的数量限制，默认为 5。
            offset: 偏移数量，用于分页，默认为 0。
            verbose_debug: 如果为True，打印详细的请求和响应信息。

        Returns:
            一个列表，其中每个元素是一个字典，包含歌曲的 'id', 'name', 'artist', 'album', 'duration'。
            如果未找到歌曲，则返回空列表。

        Raises:
            Exception: 如果API通信失败或数据解析失败。
        """
        endpoint = "/cloudsearch"

        # 构建更精确的关键词，如果提供了歌手名
        keywords = f"{song_name} {artist_name}" if artist_name else song_name

        params = {
            "keywords": keywords,
            "type": 1,  # 1 代表搜索单曲
            "limit": limit,
            "offset": offset
        }

        response_data = self._make_request(endpoint, params, verbose=verbose_debug)

        if response_data.get('code') != 200:
            raise Exception(f"API业务错误: {response_data.get('msg', response_data.get('message', '未知错误'))}")

        songs = response_data.get('result', {}).get('songs', [])

        results = []
        if songs:
            for song in songs:
                artist_names = [ar.get('name', '未知艺术家') for ar in song.get('ar', [])]
                main_artist = ', '.join(artist_names)

                results.append({
                    'id': song.get('id'),
                    'name': song.get('name'),
                    'artist': main_artist,
                    'album': song.get('al', {}).get('name', '未知专辑'),
                    'duration': song.get('dt')  # 歌曲时长 (毫秒)
                })
        return results


def parse_input_query(query_string: str) -> Dict[str, Optional[str]]:
    """
    解析用户输入的歌曲名-歌手字符串。
    如果输入是 "歌曲名-歌手"，则解析出歌曲名和歌手名。
    如果只有 "歌曲名"，则只解析出歌曲名。
    """
    parts = query_string.split('-', 1)  # 只按第一个 '-' 分割
    song_name = parts[0].strip()
    artist_name = parts[1].strip() if len(parts) > 1 else None
    return {"song_name": song_name, "artist_name": artist_name}


def main():
    print("网易云音乐单曲ID搜索器")
    print("--------------------")
    print("请输入歌曲名，或 '歌曲名-歌手' 格式进行搜索 (输入 'exit' 退出):")

    client = NeteaseAPIClient()

    while True:
        try:
            user_input = input("搜索 > ").strip()
            if user_input.lower() == 'exit':
                break
            if not user_input:
                continue

            parsed_query = parse_input_query(user_input)
            song_name = parsed_query["song_name"]
            artist_name = parsed_query["artist_name"]

            # 清除上次的搜索结果显示，让输出更整洁
            print("\033[F\033[K" + "搜索 > ", end='')  # 移动光标到上一行开头并清除该行

            print(f"正在搜索 '{user_input}'...")

            songs = client.search_song_by_name(song_name, artist_name, limit=5)

            if not songs:
                print("空空如也~~")
            else:
                found_match = False
                for i, song in enumerate(songs):
                    # 尝试进行一个简单的匹配，确保结果是用户真正想要的
                    # 例如，歌曲名是否包含用户输入的歌曲名，且歌手名是否匹配 (如果提供了)
                    is_exact_match = True
                    if song_name.lower() not in song['name'].lower():
                        is_exact_match = False
                    if artist_name and artist_name.lower() not in song['artist'].lower():
                        is_exact_match = False

                    if is_exact_match:
                        print(
                            f"  {i + 1}. ID: {song['id']}, 名称: '{song['name']}', 歌手: {song['artist']}, 专辑: '{song['album']}'")
                        found_match = True

                if not found_match and songs:
                    print(f"未找到与 '{user_input}' 高度匹配的歌曲，但找到以下可能相关的结果:")
                    for i, song in enumerate(songs):
                        print(
                            f"  {i + 1}. ID: {song['id']}, 名称: '{song['name']}', 歌手: {song['artist']}, 专辑: '{song['album']}'")
                elif not found_match:
                    # 如果找到了结果但没有高度匹配的，而上面没有输出，那就是真的没有
                    print("空空如也~~")

            print("\n请输入歌曲名，或 '歌曲名-歌手' 格式进行搜索 (输入 'exit' 退出):")

        except Exception as e:
            print(f"搜索时发生错误: {e}")
            print("请检查输入或稍后重试。")
            print("\n请输入歌曲名，或 '歌曲名-歌手' 格式进行搜索 (输入 'exit' 退出):")


if __name__ == "__main__":
    main()