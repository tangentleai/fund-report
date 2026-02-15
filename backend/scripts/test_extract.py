import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services.report_parser import get_report_viewpoint

fund_code = "000477"
report_period = "2025Q4"

print(f"正在提取 {fund_code} {report_period} 的报告观点...")
viewpoint, fund = get_report_viewpoint(fund_code, report_period)

print(f"\n基金: {fund['name']}({fund['code']}) 经理: {fund['manager']}")
print(f"\n观点内容:")
print("=" * 80)
print(viewpoint)
print("=" * 80)
print(f"\n观点长度: {len(viewpoint)} 字符")
