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


async def download_pdf():
    fund_code = "000477"
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
    url = f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf"
    
    print(f"报告ID: {report_id}")
    print(f"PDF URL: {url}")
    
    print("\n启动浏览器...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        
        print(f"访问: {url}")
        
        download_task = asyncio.create_task(page.wait_for_event("download"))
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"页面加载超时或错误: {e}")
        
        await asyncio.sleep(3)
        
        print("\n检查页面内容...")
        content = await page.content()
        print(f"页面大小: {len(content)} 字符")
        
        if "%PDF-" in content:
            print("✓ 页面包含PDF内容")
        
        pdf_bytes = await page.pdf()
        print(f"✓ 获取到PDF，大小: {len(pdf_bytes)} 字节")
        
        test_path = Path("/tmp/test_playwright.pdf")
        test_path.write_bytes(pdf_bytes)
        print(f"已保存到: {test_path}")
        
        await browser.close()
        return test_path


if __name__ == "__main__":
    asyncio.run(download_pdf())
