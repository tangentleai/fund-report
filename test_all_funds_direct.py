
#!/usr/bin/env python3
"""批量测试所有目标基金的观点提取"""

import sys
from pathlib import Path
import pdfplumber

# 导入我们修改后的解析器
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fund_report_parser

fund_codes = ["006567", "008272", "008318", "013642", "015245", "015290", "016841", "023350"]
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parent / "backend" / "data" / "reports"

results = []

for fund_code in fund_codes:
    print(f"\n{'='*80}")
    print(f"测试基金: {fund_code}")
    print(f"{'='*80}")
    
    fund_dir = data_dir / fund_code
    pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))
    
    if not pdf_files:
        print(f"❌ 未找到基金 {fund_code} 在 {report_period} 的报告")
        results.append({"code": fund_code, "success": False, "reason": "未找到PDF"})
        continue
    
    pdf_path = pdf_files[0]
    print(f"✅ 找到PDF: {pdf_path.name}")
    
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            all_text = ""
            # 提取所有页面的文本
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                all_text += text + "\n\n"
            
            # 测试 extract_manager_viewpoint 函数
            viewpoint = fund_report_parser.extract_manager_viewpoint(all_text)
            
            if viewpoint:
                print(f"✅ 成功! 观点长度: {len(viewpoint)} 字符")
                print(f"观点预览: {viewpoint[:100]}...")
                results.append({
                    "code": fund_code, 
                    "success": True, 
                    "length": len(viewpoint), 
                    "viewpoint": viewpoint
                })
            else:
                print(f"❌ 未提取到观点")
                results.append({"code": fund_code, "success": False, "reason": "未提取到观点"})
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        results.append({"code": fund_code, "success": False, "reason": str(e)})

print(f"\n{'='*80}")
print("📊 测试总结")
print(f"{'='*80}")

success_count = sum(1 for r in results if r["success"])
print(f"成功: {success_count}/{len(fund_codes)}")

print("\n详细结果:")
for r in results:
    status = "✅" if r["success"] else "❌"
    if r["success"]:
        print(f"{status} {r['code']}: 成功 ({r['length']} 字符)")
    else:
        print(f"{status} {r['code']}: {r['reason']}")

