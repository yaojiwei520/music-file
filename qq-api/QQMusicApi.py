import asyncio

from qqmusic_api import search

async def main():
    # 搜索歌曲
    result = await search.search_by_type(keyword="好不容易", num=20)
    # 打印结果
    print(result)

asyncio.run(main())