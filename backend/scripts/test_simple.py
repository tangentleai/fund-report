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
print(f"尝试获取基金 {fund_code} 的其他数据...")

print("\n=== 尝试 fund_individual_info_em ===")
try:
    df = ak.fund_individual_info_em(symbol=fund_code)
    print(df.to_string())
except Exception as e:
    print(f"失败: {e}")

print("\n=== 尝试 fund_announcement_em ===")
try:
    df = ak.fund_announcement_em(symbol=fund_code)
    print(f"列名: {df.columns.tolist()}")
    print(df.head(10).to_string())
except Exception as e:
    print(f"失败: {e}")

print("\n=== 尝试 fund_portfolio_hold_em ===")
try:
    df = ak.fund_portfolio_hold_em(symbol=fund_code, date="2024-12-31")
    print(df.head(10).to_string())
except Exception as e:
    print(f"失败: {e}")

print("\n=== 尝试 fund_portfolio_scale_em ===")
try:
    df = ak.fund_portfolio_scale_em(symbol=fund_code)
    print(df.head(10).to_string())
except Exception as e:
    print(f"失败: {e}")
