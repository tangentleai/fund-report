import sys
from pathlib import Path
import pdfplumber

fund_code = "006567"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parents[0] / "backend" / "data" / "reports"
fund_dir = data_dir / fund_code
pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))

if not pdf_files:
    print("未找到PDF")
    sys.exit(1)

pdf_path = pdf_files[0]
print(f"PDF文件: {pdf_path.name}\n")

try:
    with pdfplumber.open(str(pdf_path)) as pdf:
        print(f"总页数: {len(pdf.pages)}\n")
        
        print("=" * 80)
        print("前4页完整内容:")
        print("=" * 80)
        
        for i in range(min(4, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            print(f"\n--- 第 {i+1} 页 ---\n")
            print(text if text else "空")
            print("\n")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
