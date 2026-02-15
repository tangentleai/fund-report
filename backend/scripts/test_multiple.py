import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

try:
    import akshare as ak
    from playwright.async_api import async_playwright
except Exception as e:
    print(f"导入失败: {e}")
    sys.exit(1)


async def download_pdf(url: str, output_path: Path) -> bool:
    """使用 Playwright 下载 PDF"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        download_path = None
        
        async def handle_download(download):
            nonlocal download_path
            download_path = output_path
            await download.save_as(download_path)
        
        page.on("download", handle_download)
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception:
            pass
        
        await asyncio.sleep(5)
        
        if download_path and download_path.exists():
            try:
                with open(download_path, "rb") as f:
                    header = f.read(5)
                if header.startswith(b"%PDF-"):
                    await browser.close()
                    return True
            except Exception:
                pass
        
        await browser.close()
        return False


async def get_fund_report(fund_code: str, report_period: str) -> bool:
    print(f"\n{'='*60}")
    print(f"处理基金: {fund_code}")
    print(f"{'='*60}")
    
    try:
        announcement_df = ak.fund_announcement_report_em(symbol=fund_code)
    except Exception as e:
        print(f"获取公告列表失败: {e}")
        return False
    
    name_col = "公告标题"
    date_col = "公告日期"
    report_id_col = "报告ID"
    
    df = announcement_df.copy()
    df = df[df[name_col].astype(str).str.contains("季度报告|季报", regex=True)]
    df = df.sort_values(date_col, ascending=False)
    
    if df.empty:
        print(f"未找到季度报告")
        return False
    
    latest = df.iloc[0]
    report_id = str(latest[report_id_col])
    
    urls_to_try = [
        f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf",
        f"https://pdf.dfcfw.com/pdf/H1_{report_id}_1.pdf",
        f"https://pdf.dfcfw.com/pdf/H3_{report_id}_1.pdf",
    ]
    
    report_dir = Path(__file__).resolve().parents[1] / "data" / "reports" / fund_code
    report_dir.mkdir(parents=True, exist_ok=True)
    
    from backend.services.report_parser import _build_report_filename
    file_path = report_dir / _build_report_filename(latest[name_col], report_period)
    
    if file_path.exists():
        try:
            with file_path.open("rb") as f:
                header = f.read(5)
            if header.startswith(b"%PDF-"):
                print(f"✓ 命中缓存: {file_path}")
                return True
        except Exception:
            file_path.unlink(missing_ok=True)
    
    for url in urls_to_try:
        print(f"尝试: {url}")
        success = await download_pdf(url, file_path)
        if success:
            print(f"✓ 成功下载: {file_path}")
            
            from backend.services.report_parser import _extract_pdf_text, _extract_viewpoint
            text = _extract_pdf_text(file_path)
            if text:
                viewpoint = _extract_viewpoint(text)
                print(f"✓ 观点提取成功: {len(viewpoint)} 字符")
                print(f"\n观点预览: {viewpoint[:200]}...")
            return True
    
    print(f"✗ 下载失败")
    return False


async def main():
    fund_codes = ["006567", "007509"]
    report_period = "2025Q4"
    
    for code in fund_codes:
        await get_fund_report(code, report_period)


if __name__ == "__main__":
    asyncio.run(main())
