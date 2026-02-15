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
print(f"正在获取基金 {fund_code} 的公告列表...")

try:
    announcement_df = ak.fund_announcement_report_em(symbol=fund_code)
    print(f"✓ 成功获取公告列表，共 {len(announcement_df)} 条")
    
    name_col = "公告标题"
    date_col = "公告日期"
    report_id_col = "报告ID"
    
    df = announcement_df.copy()
    df = df[df[name_col].astype(str).str.contains("季度报告|季报", regex=True)]
    df = df.sort_values(date_col, ascending=False)
    
    print(f"\n筛选后有 {len(df)} 条季度报告")
    print(f"最新的公告:")
    print(df.iloc[0].to_string())
    
    latest = df.iloc[0]
    report_id = str(latest[report_id_col])
    url = f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf"
    
    print(f"\n尝试下载PDF: {url}")
    
    response = requests.get(url, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {response.headers.get('Content-Length')}")
    print(f"文件头: {response.content[:50]}")
    
    if response.content.startswith(b"%PDF-"):
        print("✓ 这是有效的PDF文件")
    else:
        print("✗ 这不是有效的PDF文件")
        print("\n尝试查看响应内容:")
        print(response.text[:1000])
        
except Exception as e:
    print(f"失败: {e}")
    import traceback
    traceback.print_exc()
