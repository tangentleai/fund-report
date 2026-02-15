
#!/usr/bin/env python3
"""调试为什么text1（后端提取的文本）的匹配结果是错误的"""

import sys
from pathlib import Path
import pdfplumber
import re

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fund_report_parser import clean_text, post_clean, extract_manager_viewpoint
from backend.services.report_parser import _extract_pdf_text

fund_code = "008272"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parent / "backend" / "data" / "reports"
fund_dir = data_dir / fund_code
pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))
pdf_path = pdf_files[0]

text1 = _extract_pdf_text(pdf_path)

print("="*80)
print("现在详细调试为什么对 text1 的匹配失败了")
print("="*80)

# 先看 clean_text 后的 text1
cleaned_text = clean_text(text1)
print(f"\nclean_text 后的长度: {len(cleaned_text)}")
print(f"\nclean_text 后的前 500 字符:\n{repr(cleaned_text[:500])}")
print(f"\nclean_text 后的后 500 字符:\n{repr(cleaned_text[-500:])}")

print("\n\n现在找为什么匹配错误了，让我们看看我们的 patterns 分别匹配到了什么")

patterns = [
    r"4\.\d+报告期内基金的投资策略和运作分析\s*[：:]?\s*([\s\S]{20,8000}?)(?=\s*(?:4\.\d+|§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
    r"报告期内基金投资策略和运作分析\s*[：:]?\s*\n?\s*([^§]+?)(?=\s*(?:§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
    r"投资策略和运作分析\s*[：:]?\s*([\s\S]{20,8000}?)(?=\s*(?:§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
]

candidates = []
for idx, pattern in enumerate(patterns):
    matches = list(re.finditer(pattern, cleaned_text, re.DOTALL | re.IGNORECASE))
    print(f"\n模式 {idx+1} 匹配到 {len(matches)} 个结果:")
    for m_idx, match in enumerate(matches):
        print(f"  匹配 {m_idx+1}:")
        print(f"  匹配到的完整区域 (前50后50):")
        start = max(0, match.start()-50)
        end = min(len(cleaned_text), match.end()+50)
        print(f"  '{cleaned_text[start:end]}'")
        print(f"  分组内容 (前200):")
        content = match.group(1).strip()
        print(f"  '{content[:200]}'")
        cleaned_content = post_clean(content)
        print(f"  post_clean 后的内容长度: {len(cleaned_content)}")
        print(f"  post_clean 后的内容: '{cleaned_content}'")
        candidates.append(cleaned_content)

print("\n\n所有 candidates:")
for i, c in enumerate(candidates):
    print(f"候选 {i+1}: (长度 {len(c)})")
    print(repr(c))

print("\n\n现在选最长的候选:")
candidates.sort(key=lambda x: len(x), reverse=True)
print(f"最长的候选是: 长度 {len(candidates[0])}, 内容: {repr(candidates[0])}")

