import sys
from pathlib import Path
import pdfplumber
import re

def clean_text(text: str) -> str:
    """文本预处理"""
    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 去掉页眉页脚 (如 "第 X 页 共 Y 页")
    text = re.sub(r"第\s*\d+\s*页\s*共\s*\d+\s*页", "", text)
    text = re.sub(r"Page\s*\d+\s*of\s*\d+", "", text, flags=re.IGNORECASE)

    # 去掉页码 (如 "- 3 -" 或 "—3—")
    text = re.sub(r"[\-–—]\s*\d+\s*[\-–—]", "", text)

    # 合并单行换行，保留段落换行
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r" +", " ", text)

    # 合并多个换行
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
        print(f"总页数: {len(pdf.pages)}\n")
        
        all_text = ""
        for i in range(min(10, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            all_text += text + "\n\n"
        
        print("=" * 80)
        print("原始文本（第6-8页内容片段）:")
        print("=" * 80)
        
        start_idx = all_text.find("4.4 报告期内基金的投资策略和运作分析")
        if start_idx != -1:
            end_idx = all_text.find("4.5 报告期内基金的业绩表现", start_idx)
            if end_idx != -1:
                print(all_text[start_idx : end_idx + 100])
            else:
                print(all_text[start_idx : start_idx + 3000])
        
        print("\n\n")
        print("=" * 80)
        print("clean_text 之后的内容:")
        print("=" * 80)
        
        cleaned = clean_text(all_text)
        print(cleaned)
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
