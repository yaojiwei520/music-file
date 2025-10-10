import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import urllib.parse
import os  # 用于创建调试文件


def get_artist_data():
    """
    爬取网易云音乐所有歌手信息，并保存到CSV文件。
    该函数将遍历预定义的歌手分类ID和首字母组合，发送HTTP请求，
    解析返回的HTML内容以提取歌手名称、ID和链接，然后将数据去重后保存。
    """
    # 歌手分类ID列表
    ls1 = [1001, 1002, 1003, 2001, 2002, 2003, 6001, 6002, 6003, 7001, 7002, 7003, 4001, 4002, 4003]
    # 首字母/数字/其他 对应的ASCII码或特殊值
    ls2 = [-1, 0, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89,
           90]

    # 完整、精确地模拟浏览器请求头。
    # 这些headers是根据您之前提供的浏览器实际请求头信息整理的。
    # 特别是Cookie和Referer，它们对于绕过反爬机制非常重要。
    # 请确保Cookie是最新且有效的。
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',  # 告知服务器客户端支持的压缩方式
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',  # 请求不使用缓存
        # 从您提供的原始请求信息中复制的完整Cookie字符串。
        # 注意：Cookie会过期，如果遇到爬取失败，请重新从浏览器获取最新Cookie。
        'Cookie': '_ntes_nnid=b1476dd9c69c5e987f74c9306303f746,1753375028182; _ntes_nuid=b1476dd9c69c5e987f74c9306303f746; NMTID=00O_lbVMAkCcy9IR0zIpK3u_EawdiwAAAGYPUu_yw; WEVNSM=1.0.0; WNMCID=jqzrqg.1753375033773.01.0; ntes_utid=tid._.mv%252FaRYPKrH1BF1RQBFLDxUq2JN63MwOI._.0; sDeviceId=YD-JmH6HUeCgDdEB1FUERfChB72cNr3M1Pc; __snaker__id=3jeJPCRVVrIrQQJ2; WM_TID=aBQT4oIFhQBAEFVVRQOCkUr2NcvjnIbD; __remember_me=true; ntes_kaola_ad=1; __csrf=0b7b8f365a7f13190efcf659922582e0; gdxidpyhxdE=O%2Bdq8bQ0lczlB16AyOc2xzwk1S9jal7B1gONmlLKv3uKD%2FY4n%2Bhoww98fWuB7WZPkR2SmaJz3K3kHgtamnXT6%2BMUsIXbUQAq3DmXtzBx%2FdLLfL%5C%5C6auZ6j74YO66pe7HTz6oJ%2Balr9CzYfbnTWHWs4EzA%2FAOcRzLe%2FafUlKgqXRLleGr%3A1756969456096; __csrf=023112af9101280bdd45c022f8bf0063; MUSIC_U=0024094A5082154C0F47E52028EA76E69A6AFD2B4E1E8F522A155E309DDF3BD6E53D0E070A033DF549D93EF4EE343A6702E4C050EFB899855A628B32121C421EDB8C0ACF9CD14AE36DD05716C0FD34F6B99C329AC20985FBC0595A99FB1AC5AE8265A159ADC6AAE0C79975CF8B3FB08E4A947D376F1B9BB779232BA6D8094BB73B770FECDCD338E516A954CA22CDF2B177F522B21B9D84D0E80C68DF9A552AFF20D4DAF7A392B43D13203C86B98683401189DFED83BD2B78EACD57A377DFB9217973B888B6A8C910A0E492EFE7E78B27D4C0B1C499A0E06C230C223E5A7498A8FDB1DE5E7FF4255F4B91F9E3ED348C855E6C42FE3469509AB01A974486216937EF7C46113E3D3CD92657DC07B22CD498969307F5DE61E554CD0AF18738B97D4F2F3F30FA021CC7FE64FD177088D03403837182566EF9BCA6A7082A03BA3C38D4D49FA6E453B0B18ABF40EBFCC01904933EDA5B28D1701606368793E03E46E9AA2991A5FF05BE6C6CB763DCBBA08147BC39A6DD599855D33D7153B5C769E2C45E2376CB71BCB1F97C29B36C3AEE7EC22A21EDE73B17F42563B7708AB044999E7BB3; _iuqxldmzr_=32; WM_NI=Fr0ZUfmXCBb7mE7Ngt7SDhSzSrNm7uas%2FJENJBkQlWoI77XqfgvzOj1f2eaaEefkCZ8hGEnZ%2FUFG14VnyuchVOZoySLyp53RGw6MLxrgzIJtudPAUa%2FG2ZbP3PDeg6OkbVg%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6eea4c85fb69bab9be14a93e78ab6c15a838e8b82c764acbf8787d8679586828ecc2af0fea7c3b92a86ae00bbd86eaf888da3e13daf9bf9afe680f58d8c89d27291ae828eb67fa3ade1abc8468a9ea5b2ef5dad97f9d8db7ba6b9ba9bce62f3bafe86e46b87bbaa8cc252fcb889a6ed52ed8b8aa8b44096b2b796e26496919690fc5990a7c0d6b25a85a9faaecf74b2b9b6aac980b7bca0a2d86bed99febbe15cf1908c86e63e8db5aeb7e637e2a3; JSESSIONID-WYYY=vpMCs2Q3goSX9n%2FODwqMiWTtRqk%2BaxTQFm%2F%5CUr%2FbZk6QF74SFRqH1OSy2gVnSCdMv6U6i3p3gKv%5CeUr%2BYrG8SMZCtr8yscpFw%2F1Aoa9Yi%2F6tiv%2F58zk%2BH9qJ119bE2WJgfv%2BCkAJxF%2F1EUZHbBTHO%2Fpiqiyj3AR6G%5Cs9g45CBpA7%2F3qn%3A1757095338950',
        'DNT': '1',  # Do Not Track
        'Referer': 'https://music.163.com/',  # 从哪个页面链接过来，有助于模仿真实访问
        'Sec-CH-UA': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'iframe',  # 明确指出请求目标是iframe，更精确模拟浏览器行为
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Upgrade-Insecure-Requests': '1',  # 提示浏览器可以升级不安全的请求到HTTPS
    }

    base_url = 'https://music.163.com/discover/artist/cat?'  # 网易云音乐歌手分类的基础URL

    all_artists_data = []  # 用于存储所有爬取到的歌手信息

    # 辅助函数：将initial值转换为可读字符
    def get_initial_char(code):
        if code == -1:
            return 'Other'
        elif code == 0:
            return '#'
        else:
            return chr(code)  # ASCII码转换为字符 (如 65 -> 'A')

    total_combinations = len(ls1) * len(ls2)  # 总的请求组合数
    current_combination = 0  # 当前处理的组合计数

    print(f"✨ 开始爬取网易云音乐歌手信息，共 {total_combinations} 种组合...")

    for id_val in ls1:
        for initial_val in ls2:
            current_combination += 1
            params = {'id': str(id_val), 'initial': str(initial_val)}
            # 使用urllib.parse.urlencode安全地构建URL参数
            full_url = f"{base_url}{urllib.parse.urlencode(params)}"
            initial_display = get_initial_char(initial_val)

            print(
                f"[{current_combination}/{total_combinations}] 正在请求: ID={id_val}, Initial={initial_display} ({full_url})")

            try:
                # 发送GET请求，带上模拟的headers和超时设置
                response = requests.get(full_url, headers=headers, timeout=15)
                # 检查HTTP状态码，如果不是200，则抛出异常
                response.raise_for_status()

                # 使用BeautifulSoup解析HTML内容
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找歌手列表的UL元素。
                # 经验证，歌手列表在 class="m-cvrlst m-cvrlst-3 f-cb" 的 ul 中。
                # 这里的 class_ 参数也可以接受一个字符串 'm-cvrlst m-cvrlst-3 f-cb'
                artist_list_ul = soup.find('ul', class_='m-cvrlst m-cvrlst-3 f-cb')

                if artist_list_ul:
                    # 在找到的UL元素中，查找所有歌手的a标签。
                    # 经验证，歌手a标签的class包含 'nm'。
                    artist_links = artist_list_ul.find_all('a', class_='nm')

                    if artist_links:
                        for link in artist_links:
                            artist_name = link.get_text(strip=True)  # 获取歌手名字，并去除首尾空白
                            artist_href = link.get('href', '')  # 获取链接的相对路径

                            # 从链接中提取歌手ID (例如：/artist?id=XXXXX -> XXXXX)
                            artist_id = artist_href.split('=')[-1] if '=' in artist_href else None

                            # 构造完整的歌手主页链接
                            full_profile_link = "https://music.163.com" + artist_href

                            all_artists_data.append({
                                'category_id': id_val,
                                'initial_char_code': initial_val,
                                'initial_char': initial_display,
                                'artist_name': artist_name,
                                'artist_id': artist_id,
                                'profile_link': full_profile_link
                            })
                        print(f"  √ 成功找到并解析 {len(artist_links)} 位歌手。")
                    else:
                        print(
                            f"  └ 警告: 找到歌手列表容器，但内部没有找到歌手链接: ID={id_val}, Initial={initial_display}")
                        print(f"    └ 收到的HTML开头 (前500字): {response.text[:500]}...")  # 辅助调试
                else:
                    print(f"  └ 警告: 没有找到歌手列表容器: ID={id_val}, Initial={initial_display}")
                    # 打印收到的HTML开头，帮助我们判断问题
                    received_html = response.text
                    if received_html:
                        print(f"    └ 收到的HTML开头 (前1000字): {received_html[:1000]}...")
                        # 如果需要更详细地检查每个页面的HTML，可以取消注释下面两行将完整HTML保存到文件
                        # debug_dir = "debug_html_pages"
                        # os.makedirs(debug_dir, exist_ok=True)
                        # with open(os.path.join(debug_dir, f"debug_id{id_val}_initial{initial_display}.html"), "w", encoding="utf-8") as f:
                        #    f.write(received_html)
                        # print(f"    └ 完整HTML已保存至 {os.path.join(debug_dir, f'debug_id{id_val}_initial{initial_display}.html')}")
                    else:
                        print("  └ 警告: 收到的HTML内容为空！")

            except requests.exceptions.HTTPError as e:
                # 捕获HTTP错误 (如 403 Forbidden, 404 Not Found, 500 Server Error)
                print(f"  ❌ HTTP请求错误 (状态码 {e.response.status_code}): {full_url} - {e}")
                print(f"    └ 响应内容 (前500字): {response.text[:500]}...")  # 打印错误响应内容
            except requests.exceptions.RequestException as e:
                # 捕获所有requests相关的异常 (如网络连接问题，DNS解析失败，超时等)
                print(f"  ❌ 请求发生异常: {full_url} - {e}")
            except Exception as e:
                # 捕获其他未知异常
                print(f"  ❌ 发生其他错误: {full_url} - {e}")

            # 随机延迟，模拟人类行为，避免请求过于频繁被服务器识别为爬虫或封禁IP
            time.sleep(random.uniform(0.5, 2.5))  # 每次请求之间暂停0.5到2.5秒

    if all_artists_data:
        # 将爬取到的数据列表转换为pandas DataFrame
        df = pd.DataFrame(all_artists_data)
        # 根据 artist_id 去除重复的歌手，因为同一个歌手可能出现在多个分类下
        df.drop_duplicates(subset=['artist_id'], inplace=True)

        # 定义输出文件名
        output_filename = '网易云音乐歌手信息.csv'
        # 保存到CSV文件，encoding='utf-8-sig' 解决中文乱码问题并兼容Excel
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n✅ 所有歌手信息已成功爬取并保存到 '{output_filename}' 文件中。")
        print(f"   共计 {len(df)} 条不重复的歌手信息。")
    else:
        print("\n⚠️ 没有爬取到任何歌手信息。")
        print("   请检查以下可能的原因：")
        print("   1. **`headers` 中的 `Cookie` 是否是最新且有效的**：`Cookie` 会过期，需要定期更新。")
        print(
            "   2. **网易云音乐页面HTML结构是否发生了变化**：用于定位歌手列表 (`ul.m-cvrlst.m-cvrlst-3.f-cb`) 或歌手链接 (`a.nm`) 的 CSS 选择器可能已失效。请打开浏览器开发者工具检查页面结构。")
        print(
            "   3. **网站的反爬机制**：服务器可能返回了验证码页面、重定向或其他非预期内容，即使状态码是200。请查看调试输出中的HTML内容。")
        print("   4. **网络问题**：检查您的网络连接是否稳定。")


if __name__ == "__main__":
    get_artist_data()
