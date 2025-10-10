import requests
import json


def get_netease_music_info(song_identifier: str, quality_level: str = "lossless"):
    """
    通过API获取网易云音乐的歌曲信息。默认尝试获取无损音质。

    Args:
        song_identifier (str): 歌曲ID（纯数字）或歌曲分享链接。
                               例如: "186016" 或 "https://music.163.com/#/song?id=186016"
        quality_level (str): 期望的音质等级。
                               可选值: "standard", "exhigh", "lossless", "hires",
                                      "sky", "jyeffect", "jymaster"。
                               默认: "lossless"

    Returns:
        dict: 包含歌曲信息的字典，如果解析失败则包含错误信息。
              成功时包含字段如 'name', 'pic', 'ar_name', 'url', 'lyric' 等。
              失败时包含 'status' (非200) 和 'msg'。
    """
    API_URL = "https://api.kxzjoker.cn/api/163_music"  # 注意此API可能已失效，请自行测试或更换

    # 构建请求 payload
    payload = {
        "url": song_identifier,
        "level": quality_level,
        "type": "json"  # API要求此参数固定为 'json', 且前端js也是这样
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # 发送 POST 请求
        # 设置 timeout 可以避免长时间无响应
        response = requests.post(API_URL, data=payload, headers=headers, timeout=10)
        response.raise_for_status()  # 如果状态码不是 2xx，会抛出 HTTPError 异常

        # 解析 JSON 响应
        data = response.json()
        return data

    except requests.exceptions.Timeout:
        return {"status": 500, "msg": "请求API超时，请稍后再试。"}
    except requests.exceptions.HTTPError as e:
        try:
            # 尝试解析API返回的错误信息
            error_data = response.json()
            return {"status": response.status_code, "msg": f"API错误: {error_data.get('msg', '未知错误')}"}
        except json.JSONDecodeError:
            return {"status": response.status_code, "msg": f"请求API时发生HTTP错误: {e}, 且无法解析错误响应。"}
    except requests.exceptions.RequestException as e:
        return {"status": 500, "msg": f"连接API时发生网络错误: {e}"}
    except json.JSONDecodeError:
        return {"status": 500, "msg": "API返回的数据不是有效的JSON格式。"}
    except Exception as e:
        return {"status": 500, "msg": f"发生未知错误: {e}"}


if __name__ == "__main__":
    # 移除所有非JSON输出的引导性/交互性文字，只保留输入
    user_song_identifier = input(
        "请输入歌曲ID或完整分享链接 (例如: 186016 或 https://music.163.com/#/song?id=186016) : ")
    desired_quality = "lossless"  # 硬编码为无损音质

    result = get_netease_music_info(user_song_identifier, desired_quality)

    final_output = {}  # 初始化最终输出字典

    if result and result.get("status") == 200:
        final_output = {
            "overall_status": "success",
            "message": "歌曲信息解析成功。",
            "request_info": {
                "identifier_provided": user_song_identifier,
                "quality_requested": desired_quality
            },
            "song_data": {
                "song_name": result.get('name', 'N/A'),
                "artist_name": result.get('ar_name', 'N/A'),
                "album_name": result.get('al_name', 'N/A'),
                "actual_quality_level": result.get('level', 'N/A'),
                "file_size": result.get('size', 'N/A'),
                "cover_image_url": result.get('pic', 'N/A'),
                "audio_download_url": result.get('url', 'N/A'),
                "lyrics": result.get('lyric', None)  # 歌词直接放入，如果API返回None则为None
            },
            "api_raw_response_status": result.get('status')
        }
    else:
        final_output = {
            "overall_status": "failure",
            "message": "歌曲信息解析失败。",
            "request_info": {
                "identifier_provided": user_song_identifier,
                "quality_requested": desired_quality
            },
            "error_details": {
                "api_status_code": result.get("status", 500),
                "api_error_message": result.get("msg", "未知API错误"),
                "raw_api_response": result  # 包含原始API错误响应的所有细节
            }
        }

    # 将最终字典转换为标准JSON字符串并打印
    print(json.dumps(final_output, indent=4, ensure_ascii=False))

    # 移除退出提示，因为JSON输出通常用于程序间通信，不应有交互式提示
    # 如果需要保持交互性，可以在print(json.dumps(...))之后添加回去
    # input("按任意键退出...")