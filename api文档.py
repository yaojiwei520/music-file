import requests

url = "https://apis.netstart.cn/music/README.md"

# 模拟浏览器发送的请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Referer": "https://apis.netstart.cn/music/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", # 典型浏览器Accept头
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6", # 或您常用的语言
    "DNT": "1", # Do Not Track，也来自您提供的信息
    # Chrome Client Hints，可以尝试先不加，如果还不行再加
    "sec-ch-ua": "\"Not;A=Brand\";v=\"99\", \"Google Chrome\";v=\"139\", \"Chromium\";v=\"139\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
}

try:
    # 发送GET请求，并带上自定义的请求头
    response = requests.get(url, headers=headers)

    # 检查请求是否成功 (状态码200)
    response.raise_for_status()

    # 获取响应内容 (文本格式)
    content = response.text

    # 将内容保存到本地文件
    with open("cn_md.md", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"成功爬取 {url} 并保存到 cn_md.md")
    print(f"文件大小: {len(content)} 字节")
    # print("\n--- 文件开头部分 ---")
    # print(content[:1000]) # 打印前1000个字符
    # print("--- ... (文件其余内容已保存到 cn_md.md) ---")

except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")