import requests

# 设置请求URL和头部，用户中心获取token，自行替换其他参数
url = "https://api.makuo.cc/api/get.music.qq?mid=003OUlho2HcRHC"
headers = {
    'Authorization': 'UEfapp6cOlJFszrSitYFqQ'
}

# 发送GET请求
response = requests.get(url, headers=headers)
# 将响应解析为JSON格式
data = response.json()
# 输出JSON数据
print(data)