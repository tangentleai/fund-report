
#!/usr/bin/env python3
"""强制重新加载模块"""

import sys
from pathlib import Path
import importlib

# 确保导入路径正确
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 先删除已缓存的模块
if 'fund_report_parser' in sys.modules:
    del sys.modules['fund_report_parser']
if 'backend.services.report_parser' in sys.modules:
    del sys.modules['backend.services.report_parser']

# 现在重新导入
print("重新导入模块...")

from backend.services.report_parser import get_report_viewpoint
from fund_report_parser import extract_manager_viewpoint
from backend.services.report_parser import _load_real_report_text

fund_code = "008272"
report_period = "2025Q4"

print("\n现在调用 get_report_viewpoint:")
viewpoint, fund_info = get_report_viewpoint(fund_code, report_period)
print(f"返回观点长度: {len(viewpoint) if viewpoint else 0}")
print(f"观点内容: {repr(viewpoint)}")

print("\n现在直接调用 extract_manager_viewpoint:")
report_text = _load_real_report_text(fund_code, report_period)
vp = extract_manager_viewpoint(report_text)
print(f"直接调用结果长度: {len(vp) if vp else 0}")
print(f"直接调用内容: {repr(vp)}")

print("\n让我们检查一下 fund_report_parser.extract_manager_viewpoint 的实现!")
import inspect
print("\n" + "="*80)
print(inspect.getsource(extract_manager_viewpoint))
print("="*80)

