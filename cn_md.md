### 如何使用？

1. **环境准备**：
   - 确保您的计算机上安装了 Python 3.x。
   - 确保安装了 `requests` 和 `beautifulsoup4` 库。可以使用以下命令安装：
     ```bash
     pip install requests beautifulsoup4
     ```
   - 确保安装了 FFmpeg，并将其添加到系统的 PATH 中。如果没有 FFmpeg，可以忽略自动转换功能。

2. **配置 Cookies 和 Headers**：
   - 打开脚本中的 `cookies` 和 `get_html_headers` 字典，并根据需要更新其内容。这些信息通常可以从您的浏览器中获取。

3. **运行脚本**：
   - 在命令行中运行脚本：
     ```bash
     python your_script_name.py
     ```
   - 输入您想搜索的歌曲关键词，程序将返回搜索结果。

4. **选择并下载歌曲**：
   - 根据提示输入您想下载的歌曲序号，可以输入多个序号，使用空格分隔；输入 `all` 可以下载所有歌曲；如果直接回车，则默认下载前5首歌曲。

### 使用了哪几个脚本？

- `check_ffmpeg_available()`：检查系统中是否安装了 FFmpeg。
- `convert_aac_to_mp3(input_filepath)`：将 AAC 文件转换为 MP3 格式。
- `sanitize_filename(name)`：清理文件名中的不安全字符。
- `download_music_file(url, title, artist)`：根据 URL 下载音乐文件，并处理文件名。
- `search_songs(keyword)`：根据关键词搜索歌曲，并提取歌曲信息。
- `_get_play_id_from_html(track_id)`：从歌曲详情页的 HTML 中提取播放 ID。
- `get_music_url(track_id)`：通过歌曲 ID 获取音乐的播放链接。

### 总结

此脚本为您提供了一个便捷的工具，可以通过关键词搜索歌曲并下载相关音乐文件。请确保在使用前正确配置必要的 Cookies 和 Headers，并注意 FFmpeg 的可用性。如果在使用过程中遇到问题，请检查网络连接和配置的准确性。

---


