import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging
logging.basicConfig(level=logging.INFO)

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
    print("\n列名:")
    print(announcement_df.columns.tolist())
    
    print("\n前20条公告:")
    print(announcement_df.head(20).to_string())
    
    print("\n筛选季度报告:")
    name_col = None
    for col in ["名称", "公告标题", "标题", "公告名称"]:
        if col in announcement_df.columns:
            name_col = col
            break
    
    if name_col:
        df = announcement_df.copy()
        df = df[df[name_col].astype(str).str.contains("季度报告|季报", regex=True)]
        print(f"找到 {len(df)} 条季度报告")
        print(df.head(10).to_string())
    else:
        print("未找到名称列")
        
except Exception as e:
    print(f"获取公告失败: {e}")
    import traceback
    traceback.print_exc()
