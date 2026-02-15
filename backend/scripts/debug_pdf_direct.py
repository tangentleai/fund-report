import sys
from pathlib import Path
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

fund_code = "006567"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parents[1] / "backend" / "data" / "reports"
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
        print("前3页完整内容:")
        print("=" * 80)
        
        for i in range(min(3, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            print(f"\n--- 第 {i+1} 页 ---\n")
            print(text if text else "空")
            print("\n")
        
        print("=" * 80)
        print("寻找 '投资策略' 关键词:")
        print("=" * 80)
        
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text += text + "\n\n"
        
        keywords = ["投资策略", "运作分析", "管理人报告", "4.2"]
        for kw in keywords:
            if kw in all_text:
                print(f"✓ 找到 '{kw}'")
                idx = all_text.find(kw)
                print(f"位置: {idx}")
                print(f"前后200字符:")
                start = max(0, idx - 200)
                end = min(len(all_text), idx + 400)
                print(all_text[start:end])
                print("\n")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
