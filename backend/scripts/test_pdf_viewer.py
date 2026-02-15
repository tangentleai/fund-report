import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
import requests
import re

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

print(f"报告ID: {report_id}")

pdf_viewer_urls = [
    f"https://pdf.dfcfw.com/pdf/{report_id}.pdf",
    f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf",
    f"https://pdf.dfcfw.com/pdf/H1_{report_id}_1.pdf",
    f"https://pdf.dfcfw.com/pdf/H3_{report_id}_1.pdf",
    f"https://pdf.dfcfw.com/pdf/H4_{report_id}_1.pdf",
    f"https://pdf.dfcfw.com/pdf/{report_id}_1.pdf",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://fund.eastmoney.com/",
}

session = requests.Session()

for url in pdf_viewer_urls:
    print(f"\n尝试: {url}")
    try:
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        print(f"  状态码: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Content-Length: {response.headers.get('Content-Length')}")
        
        if response.content.startswith(b"%PDF-"):
            print(f"  ✓ 找到有效的PDF!")
            print(f"  文件大小: {len(response.content)} 字节")
            
            test_path = Path("/tmp/test_download.pdf")
            test_path.write_bytes(response.content)
            print(f"  已保存到: {test_path}")
            break
        else:
            print(f"  ✗ 不是PDF")
            print(f"  文件头: {response.content[:100]}")
            
    except Exception as e:
        print(f"  失败: {e}")
