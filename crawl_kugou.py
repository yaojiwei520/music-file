import requests
import os
import json
from urllib.parse import urlparse

# --- 请求 1: 下载 MP3 文件 ---
print("--- 正在处理第一个请求：下载MP3文件 ---")

# 构造完整的 URL
mp3_host = "fsandroid.kugou.com"
mp3_path = "/202509040949/a0419967e72cf9c8977d89a5d34ad534/v3/8909e1809908cd8e3bf6cf85d98b93f0/yp/p_0_960115/ap1005_us0_df3eualy3qqdxg0pyrzb3lzgke_pi2_mx32042828_qu128_ct431000_s2055586539.mp3"
mp3_url = f"http://{mp3_host}{mp3_path}" # 注意：这里假设是 HTTPS

# 构建请求头
mp3_headers = {
    "Host": mp3_host,
    "User-Agent": "AndroidPhone-11709-Range-ActC-pgid857461132-fid21-hasfh-wifi-PXY(W)",
    "ppageid": "463467626,661004247",
    "mid": "195607c3b40ea207f37bf391d0ac0313",
    "mixsongid": "32042828",
    "KG-FAKE": "0",
    "KG-RC": "0",
    "KG-RF": "FF44550068B8F02F",
    # Content-Length: 0 通常用于POST请求，GET请求无需此头
}

# 从URL中提取文件名
parsed_url = urlparse(mp3_url)
mp3_filename = os.path.basename(parsed_url.path)
if not mp3_filename.endswith(".mp3"):
    mp3_filename = "downloaded_audio.mp3" # 备用文件名以防解析错误

print(f"尝试下载MP3文件: {mp3_url}")
print(f"目标文件名: {mp3_filename}")

try:
    # 对于大文件，使用 stream=True 并在 chunks 中迭代，以避免一次性加载到内存
    with requests.get(mp3_url, headers=mp3_headers, stream=True, timeout=30) as r:
        r.raise_for_status() # 如果状态码不是 2xx，则抛出 HTTPError

        total_length = r.headers.get('content-length')
        downloaded = 0

        with open(mp3_filename, 'wb') as f:
            print("下载中...")
            if total_length:
                total_length = int(total_length)
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # print(f"\rDownloaded: {downloaded / 1024 / 1024:.2f} MB / {total_length / 1024 / 1024:.2f} MB", end='')
                print(f"\nMP3文件 '{mp3_filename}' 下载成功，大小：{downloaded / (1024 * 1024):.2f} MB")
            else:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                print(f"MP3文件 '{mp3_filename}' 下载成功，大小：{downloaded / (1024 * 1024):.2f} MB (Content-Length头未提供)")


except requests.exceptions.HTTPError as errh:
    print(f"HTTP错误: {errh}")
except requests.exceptions.ConnectionError as errc:
    print(f"连接错误: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"请求超时: {errt}")
except requests.exceptions.RequestException as err:
    print(f"发生未知错误: {err}")
except Exception as e:
    print(f"处理MP3下载时发生错误: {e}")

print("\n" + "="*50 + "\n")

# --- 请求 2: 获取 JSON 数据 ---
print("--- 正在处理第二个请求：获取JSON数据 ---")

# 构造完整的 URL (已经包含了查询参数)
json_host = "nsongacsing.kugou.com"
json_path_with_query = "/sing7/accompanywan/json/v2/cdn/optimal_matching_accompany_2_listen.do?fileName=%E5%91%A8%E6%9D%B0%E4%BC%A6%E3%80%81%E5%BC%A0%E6%83%A0%E5%A6%B9+-+%E4%B8%8D%E8%AF%A5+%28with+aMEI%29&hash=fcf336e81da45a8e696032ffc1708175&mixId=39541135&platform=android&sign=b79d31de2210a5a0&source=%E6%92%AD%E6%94%BE%E9%A1%B5-%E5%94%B1%E5%B9%BF%E5%91%8A&version=11709"
json_url = f"https://{json_host}{json_path_with_query}" # 注意：这里假设是 HTTPS

# 构建请求头
json_headers = {
    "host": json_host,
    "user-agent": "Android9-AndroidPhone-11709-18-0-b-wifi",
    "kg-thash": "19f141e",
    "accept-encoding": "gzip, deflate", # requests 默认会处理 gzip 解压
    "kg-rc": "1",
    "kg-fake": "0",
    "kg-rf": "00834647",
}

print(f"尝试获取JSON数据: {json_url}")

try:
    response = requests.get(json_url, headers=json_headers, timeout=10)
    response.raise_for_status() # 如果状态码不是 2xx，则抛出 HTTPError

    # 尝试解析 JSON
    json_data = response.json()
    print("JSON数据获取成功:")
    print(json.dumps(json_data, indent=4, ensure_ascii=False)) # 打印格式化的JSON数据，支持中文

    # 你可以进一步访问 JSON 数据的特定字段
    if json_data.get("data"):
        print("\n--- 提取关键信息 ---")
        data = json_data["data"]
        print(f"歌曲名: {data.get('songname')}")
        print(f"歌手名: {data.get('singername')}")
        print(f"文件大小: {data.get('filesize')} 字节")
        print(f"哈希值: {data.get('hash')}")
    else:
        print("JSON响应中未找到 'data' 字段。")


except requests.exceptions.HTTPError as errh:
    print(f"HTTP错误: {errh}")
except requests.exceptions.ConnectionError as errc:
    print(f"连接错误: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"请求超时: {errt}")
except requests.exceptions.RequestException as err:
    print(f"发生未知错误: {err}")
except json.JSONDecodeError as json_err:
    print(f"JSON解析错误: {json_err}")
    print(f"响应内容: {response.text[:500]}...") # 打印部分响应内容以帮助调试
except Exception as e:
    print(f"处理JSON请求时发生错误: {e}")

print("\n--- 所有请求处理完毕 ---")