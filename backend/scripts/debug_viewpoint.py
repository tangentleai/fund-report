import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.report_parser import _extract_pdf_text
from fund_report_parser import extract_manager_viewpoint

fund_codes = ["006567", "008272", "008318", "013642", "015245", "015290", "016841", "023350"]
report_period = "2025Q4"

data_dir = Path(__file__).resolve().parents[1] / "backend" / "data" / "reports"

for fund_code in fund_codes:
    print(f"\n{'='*60}")
    print(f"检查基金: {fund_code}")
    print(f"{'='*60}")
    
    fund_dir = data_dir / fund_code
    if not fund_dir.exists():
        print(f"✗ 基金目录不存在: {fund_dir}")
        continue
    
    pdf_files = list(fund_dir.glob(f"{report_period}_*.pdf"))
    if not pdf_files:
        print(f"✗ 未找到 {report_period} 的 PDF")
        continue
    
    pdf_path = pdf_files[0]
    print(f"✓ 找到PDF: {pdf_path.name}")
    
    text = _extract_pdf_text(pdf_path)
    if text:
        print(f"✓ PDF解析成功: {len(text)} 字符")
        
        print(f"\n--- PDF前1500字符预览 ---")
        print(text[:1500])
        
        try:
            viewpoint = extract_manager_viewpoint(text)
            print(f"\n--- 提取的观点 ---")
            print(f"长度: {len(viewpoint)}")
            if viewpoint:
                print(f"内容:\n{viewpoint}")
            else:
                print(f"为空!")
        except Exception as e:
            print(f"\n✗ 提取观点失败: {e}")
    else:
        print(f"✗ PDF解析失败")
    
    break
