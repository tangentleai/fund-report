import sys
from pathlib import Path
import pdfplumber
import re

def clean_text(text: str) -> str:
    """文本预处理"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"第\s*\d+\s*页\s*共\s*\d+\s*页", "", text)
    text = re.sub(r"Page\s*\d+\s*of\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\-–—]\s*\d+\s*[\-–—]", "", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


fund_code = "008318"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parents[0] / "backend" / "data" / "reports"
fund_dir = data_dir / fund_code
pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))

pdf_path = pdf_files[0]

try:
    with pdfplumber.open(str(pdf_path)) as pdf:
        all_text = ""
        for i in range(min(10, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            all_text += text + "\n\n"
        
        cleaned = clean_text(all_text)
        
        print("=" * 80)
        print("cleaned 前 2000 字符:")
        print("=" * 80)
        print(repr(cleaned[:2000]))
        
        print("\n\n")
        print("=" * 80)
        print("查找 '§4' 的位置:")
        print("=" * 80)
        if "§4" in cleaned:
            idx = cleaned.find("§4")
            print(f"找到 §4 在位置: {idx}")
            print(f"\n从 §4 开始的内容:")
            print(repr(cleaned[idx: idx + 3000]))
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
