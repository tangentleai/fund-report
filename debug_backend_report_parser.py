
#!/usr/bin/env python3
"""直接调试后端服务的 report_parser.py 的 get_report_viewpoint 函数"""

import sys
from pathlib import Path

# 导入后端服务的模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.services.report_parser import get_report_viewpoint

fund_code = "008272"
report_period = "2025Q4"

print("="*80)
print(f"测试基金: {fund_code}, 报告期: {report_period}")
print("="*80)

viewpoint, fund_info = get_report_viewpoint(fund_code, report_period)

print("\n返回结果:")
print(f"  基金信息: {fund_info}")
print(f"  观点长度: {len(viewpoint) if viewpoint else 0}")
if viewpoint:
    print(f"  观点内容:\n{repr(viewpoint)}")

print("\n\n现在让我们检查为什么会返回这个内容...")

print("\n让我们检查我们自己直接调用 extract_manager_viewpoint:")

from fund_report_parser import extract_manager_viewpoint
from backend.services.report_parser import _load_real_report_text

report_text = _load_real_report_text(fund_code, report_period)
print(f"_load_real_report_text 返回长度: {len(report_text) if report_text else 0}")

if report_text:
    print(f"\n现在调用我们修改后的 extract_manager_viewpoint:")
    vp = extract_manager_viewpoint(report_text)
    print(f"直接调用的结果长度: {len(vp) if vp else 0}")
    print(f"直接调用的内容: {repr(vp)}")

