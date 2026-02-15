
#!/usr/bin/env python3
"""详细调试 008272 基金"""

import sys
from pathlib import Path
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fund_report_parser

fund_code = "008272"
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parent / "backend" / "data" / "reports"
fund_dir = data_dir / fund_code
pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))

pdf_path = pdf_files[0]
print(f"✅ 找到PDF: {pdf_path}")

try:
    with pdfplumber.open(str(pdf_path)) as pdf:
        print(f"\n总页数: {len(pdf.pages)}")
        
        # 打印前10页
        print("\n" + "="*80)
        print("前8页内容:")
        print("="*80)
        
        for i in range(min(8, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            print(f"\n--- 第 {i+1} 页 ---\n")
            print(text)
        
        # 现在提取所有文本并测试我们的解析器
        print("\n\n" + "="*80)
        print("现在测试我们的 extract_manager_viewpoint 函数:")
        print("="*80)
        
        all_text = ""
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            all_text += text + "\n\n"
        
        # 测试一下，我们要看看为什么它匹配到了前面的部分
        import re
        
        # 我们来检查为什么我们的候选列表里有前面的内容
        # 我们手动运行一下模式匹配，看看每个模式匹配到什么
        
        print("\n正在手动检查匹配模式...")
        
        patterns = [
            r"4\.\d+报告期内基金的投资策略和运作分析\s*[：:]?\s*([\s\S]{20,8000}?)(?=\s*(?:4\.\d+|§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
            r"报告期内基金投资策略和运作分析\s*[：:]?\s*\n?\s*([^§]+?)(?=\s*(?:§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
            r"投资策略和运作分析\s*[：:]?\s*([\s\S]{20,8000}?)(?=\s*(?:§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
        ]
        
        cleaned_text = fund_report_parser.clean_text(all_text)
        
        candidates = []
        for idx, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, cleaned_text, re.DOTALL | re.IGNORECASE))
            print(f"\n模式 {idx+1} 匹配到 {len(matches)} 个结果")
            for m_idx, match in enumerate(matches):
                content = match.group(1).strip()
                cleaned_content = fund_report_parser.post_clean(content)
                print(f"  匹配 {m_idx+1}: 长度 {len(cleaned_content)} 字符")
                print(f"  前100字符: {repr(cleaned_content[:100])}")
                candidates.append(cleaned_content)
        
        # 现在测试我们的函数
        print("\n" + "="*80)
        print("最终测试 extract_manager_viewpoint:")
        print("="*80)
        viewpoint = fund_report_parser.extract_manager_viewpoint(all_text)
        
        if viewpoint:
            print(f"\n✅ 成功! 观点长度: {len(viewpoint)} 字符")
            print("\n完整观点内容:")
            print("-"*80)
            print(viewpoint)
            print("-"*80)
        else:
            print("\n❌ 未提取到观点")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

