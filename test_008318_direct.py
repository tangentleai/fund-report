
#!/usr/bin/env python3
"""直接测试008318基金的观点提取"""

import sys
from pathlib import Path
import pdfplumber

# 导入我们修改后的解析器
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fund_report_parser

fund_code = "008318"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parent / "backend" / "data" / "reports"
fund_dir = data_dir / fund_code
pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))

if not pdf_files:
    print(f"❌ 未找到基金 {fund_code} 在 {report_period} 的报告")
    sys.exit(1)

pdf_path = pdf_files[0]
print(f"✅ 找到PDF: {pdf_path}")

try:
    with pdfplumber.open(str(pdf_path)) as pdf:
        all_text = ""
        # 提取所有页面的文本
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            all_text += text + "\n\n"
        
        print(f"\n✅ 成功提取PDF文本，总长度: {len(all_text)} 字符")
        
        # 测试我们的 extract_manager_viewpoint 函数
        print("\n" + "="*80)
        print("正在测试 extract_manager_viewpoint...")
        print("="*80)
        
        viewpoint = fund_report_parser.extract_manager_viewpoint(all_text)
        
        if viewpoint:
            print(f"\n✅ 成功提取观点! 长度: {len(viewpoint)} 字符")
            print("\n观点内容:")
            print("-"*80)
            print(viewpoint)
            print("-"*80)
        else:
            print("\n❌ 未提取到观点")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

