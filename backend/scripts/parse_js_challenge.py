import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import requests
import re
import time

logging.basicConfig(level=logging.DEBUG)

try:
    import akshare as ak
except Exception as e:
    print(f"导入akshare失败: {e}")
    sys.exit(1)

fund_code = "000477"
announcement_df = ak.fund_announcement_report_em(symbol=fund_code)

name_col = "公告标题"
date_col = "公告日期"
report_id_col = "报告ID"

df = announcement_df.copy()
df = df[df[name_col].astype(str).str.contains("季度报告|季报", regex=True)]
df = df.sort_values(date_col, ascending=False)

latest = df.iloc[0]
report_id = str(latest[report_id_col])
url = f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf"

print(f"URL: {url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

session = requests.Session()

print("\n第一次请求...")
response1 = session.get(url, headers=headers, timeout=30)
print(f"状态码: {response1.status_code}")
print(f"Set-Cookie: {response1.headers.get('Set-Cookie')}")

cookies = session.cookies.get_dict()
print(f"\nCookies: {cookies}")

js_content = response1.text
print(f"\nJS内容长度: {len(js_content)}")
print(f"\nJS内容:\n{js_content}")

print("\n等待2秒后再次请求...")
time.sleep(2)

print("\n第二次请求（带上cookies）...")
response2 = session.get(url, headers=headers, timeout=30)
print(f"状态码: {response2.status_code}")
print(f"Content-Type: {response2.headers.get('Content-Type')}")
print(f"Content-Length: {response2.headers.get('Content-Length')}")

if response2.content.startswith(b"%PDF-"):
    print("✓ 成功获取到PDF!")
    test_path = Path("/tmp/test_js_challenge.pdf")
    test_path.write_bytes(response2.content)
    print(f"已保存到: {test_path}")
else:
    print("✗ 仍然不是PDF")
    print(f"文件头: {response2.content[:200]}")
