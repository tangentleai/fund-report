import requests

fund_code = "005094"
report_period = "2025Q4"

url = f"http://localhost:8000/api/funds/{fund_code}/report/{report_period}"
print(f"请求API: {url}")

response = requests.get(url)
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\n完整响应: {data}")
else:
    print(f"错误: {response.text}")
