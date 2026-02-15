import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import requests
import re

logging.basicConfig(level=logging.INFO)

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

announcement_url = f"https://fund.eastmoney.com/gonggao/{fund_code},{report_id}.html"
print(f"访问公告页: {announcement_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": f"https://fund.eastmoney.com/{fund_code}.html",
}

session = requests.Session()
response = session.get(announcement_url, headers=headers, timeout=30)
html = response.text

print(f"\n页面大小: {len(html)} 字符")

print("\n查找所有可能的PDF链接...")

patterns = [
    r'https?://[^\s"\'<>]+\.pdf',
    r'pdfurl["\s]*[:=]["\s]*([^"\']+)',
    r'pdfUrl["\s]*[:=]["\s]*([^"\']+)',
    r'fileUrl["\s]*[:=]["\s]*([^"\']+)',
    r'data-pdf=["\']([^"\']+)',
    r'onclick[^>]*pdf[^>]*',
]

for i, pattern in enumerate(patterns):
    matches = re.findall(pattern, html, flags=re.IGNORECASE)
    if matches:
        print(f"\n模式 {i+1} ({pattern}):")
        for j, match in enumerate(matches[:10]):
            print(f"  {j+1}. {match}")

print("\n查找iframe...")
iframe_matches = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
for i, src in enumerate(iframe_matches):
    print(f"  {i+1}. {src}")

print("\n查找script中的变量...")
script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html, flags=re.DOTALL)
for i, script in enumerate(script_matches):
    if 'pdf' in script.lower() or 'url' in script.lower():
        print(f"\n脚本 {i+1} 中包含PDF相关内容:")
        print(script[:1000])
