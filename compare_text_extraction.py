
#!/usr/bin/env python3
"""比较不同文本提取方式的差异"""

import sys
from pathlib import Path
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.services.report_parser import _extract_pdf_text

fund_code = "008272"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parent / "backend" / "data" / "reports"
fund_dir = data_dir / fund_code
pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))
pdf_path = pdf_files[0]

# 方法1：使用 backend/services/report_parser.py 的 _extract_pdf_text
print("="*80)
print("方法1: _extract_pdf_text (后端的函数)")
print("="*80)
text1 = _extract_pdf_text(pdf_path)
print(f"长度: {len(text1) if text1 else 0}")
if text1:
    print(f"前200字符:\n{repr(text1[:200])}")
    print(f"\n后200字符:\n{repr(text1[-200:])}")

# 方法2：使用我们 debug 脚本里的方式（我们之前用的）
print("\n\n" + "="*80)
print("方法2: 逐页提取 + \\n\\n 连接")
print("="*80)
with pdfplumber.open(str(pdf_path)) as pdf:
    all_text = ""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        all_text += text + "\n\n"
    text2 = all_text
print(f"长度: {len(text2) if text2 else 0}")
if text2:
    print(f"前200字符:\n{repr(text2[:200])}")
    print(f"\n后200字符:\n{repr(text2[-200:])}")

# 现在测试 extract_manager_viewpoint 对这两种文本的效果
print("\n\n" + "="*80)
print("测试 extract_manager_viewpoint 对两种文本的效果")
print("="*80)

from fund_report_parser import extract_manager_viewpoint

print("\n对 text1 (后端提取的):")
vp1 = extract_manager_viewpoint(text1)
print(f"  观点长度: {len(vp1) if vp1 else 0}")
if vp1:
    print(f"  观点内容:\n{repr(vp1)}")

print("\n对 text2 (我们调试用的提取方式):")
vp2 = extract_manager_viewpoint(text2)
print(f"  观点长度: {len(vp2) if vp2 else 0}")
if vp2:
    print(f"  观点内容:\n{repr(vp2)}")

