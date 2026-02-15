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
    
    name_col = "公告标题"
    date_col = "公告日期"
    report_id_col = "报告ID"
    
    df = announcement_df.copy()
    df = df[df[name_col].astype(str).str.contains("季度报告|季报", regex=True)]
    df = df.sort_values(date_col, ascending=False)
    
    latest = df.iloc[0]
    report_id = str(latest[report_id_col])
    
    print(f"报告ID: {report_id}")
    print(f"标题: {latest[name_col]}")
    
    announcement_url = f"https://fund.eastmoney.com/gonggao/{fund_code},{report_id}.html"
    print(f"\n尝试访问公告详情页: {announcement_url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": f"https://fund.eastmoney.com/{fund_code}.html",
    }
    
    session = requests.Session()
    response = session.get(announcement_url, headers=headers, timeout=30)
    print(f"状态码: {response.status_code}")
    
    print("\n页面内容前2000字符:")
    print(response.text[:2000])
    
    print("\n尝试查找PDF链接...")
    pdf_patterns = [
        r'(https?://[^"\']+?\.pdf[^"\']*)',
        r'href=["\']([^"\']+?\.pdf[^"\']*)["\']',
        r'src=["\']([^"\']+?\.pdf[^"\']*)["\']',
    ]
    
    for pattern in pdf_patterns:
        matches = re.findall(pattern, response.text, flags=re.IGNORECASE)
        if matches:
            print(f"✓ 找到 {len(matches)} 个可能的PDF链接:")
            for i, match in enumerate(matches[:5]):
                print(f"  {i+1}. {match}")
                
except Exception as e:
    print(f"失败: {e}")
    import traceback
    traceback.print_exc()
