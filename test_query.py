import requests
import sys

# 测试查询
if len(sys.argv) > 1:
    query = sys.argv[1]
else:
    query = "发票怎么导入？"
print(f"发送查询: {query}")

# 发送POST请求
response = requests.post(
    "http://localhost:8000/api/query",
    data={"text": query},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

# 打印响应
print(f"响应状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
