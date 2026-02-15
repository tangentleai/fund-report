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


async def download_pdf_with_playwright(url: str, output_path: Path) -> bool:
    """使用 Playwright 下载 PDF"""
    print(f"正在启动浏览器...")
    
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
        
        print(f"正在访问: {url}")
        
        download_path = None
        
        async def handle_download(download):
            nonlocal download_path
            print(f"检测到下载: {download.suggested_filename}")
            download_path = output_path
            await download.save_as(download_path)
            print(f"✓ 下载完成: {download_path}")
        
        page.on("download", handle_download)
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"页面加载: {e}")
        
        await asyncio.sleep(5)
        
        if download_path and download_path.exists():
            with open(download_path, "rb") as f:
                header = f.read(5)
            if header.startswith(b"%PDF-"):
                print(f"✓ 验证成功，是有效的PDF文件")
                await browser.close()
                return True
            else:
                print(f"✗ 下载的不是有效的PDF文件")
                download_path.unlink(missing_ok=True)
        
        print(f"尝试直接获取页面内容...")
        try:
            pdf_bytes = await page.pdf()
            output_path.write_bytes(pdf_bytes)
            print(f"✓ 通过page.pdf()获取成功，大小: {len(pdf_bytes)} 字节")
            await browser.close()
            return True
        except Exception as e:
            print(f"page.pdf()失败: {e}")
        
        await browser.close()
        return False


async def main():
    fund_code = "000477"
    report_period = "2025Q4"
    
    print(f"正在获取基金 {fund_code} 的公告列表...")
    
    announcement_df = ak.fund_announcement_report_em(symbol=fund_code)
    
    name_col = "公告标题"
    date_col = "公告日期"
    report_id_col = "报告ID"
    
    df = announcement_df.copy()
    df = df[df[name_col].astype(str).str.contains("季度报告|季报", regex=True)]
    df = df.sort_values(date_col, ascending=False)
    
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
    
    for url in urls_to_try:
        print(f"\n尝试: {url}")
        success = await download_pdf_with_playwright(url, file_path)
        if success:
            print(f"\n✓ 成功下载PDF: {file_path}")
            
            from backend.services.report_parser import _extract_pdf_text
            text = _extract_pdf_text(file_path)
            if text:
                print(f"✓ PDF解析成功，共 {len(text)} 字符")
                print(f"\n预览:\n{text[:500]}")
            return
    
    print("\n✗ 所有方法都失败了")


if __name__ == "__main__":
    asyncio.run(main())
