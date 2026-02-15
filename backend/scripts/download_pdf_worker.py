#!/usr/bin/env python3
"""独立的 PDF 下载工作脚本，通过 subprocess 调用，避免事件循环冲突"""

import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import logging

logging.basicConfig(level=logging.INFO)


async def download_pdf_async(url: str, output_path: str) -> dict:
    """异步下载 PDF"""
    from playwright.async_api import async_playwright
    
    result = {"success": False, "error": None}
    
    try:
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
            
            download_path = Path(output_path)
            actual_download_path = None
            
            async def handle_download(download):
                nonlocal actual_download_path
                actual_download_path = download_path
                await download.save_as(actual_download_path)
            
            page.on("download", handle_download)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
            except Exception:
                pass
            
            await asyncio.sleep(5)
            
            if actual_download_path and actual_download_path.exists():
                try:
                    with open(actual_download_path, "rb") as f:
                        header = f.read(5)
                    if header.startswith(b"%PDF-"):
                        result["success"] = True
                        result["path"] = str(actual_download_path)
                        await browser.close()
                        return result
                except Exception as e:
                    result["error"] = str(e)
            
            await browser.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"success": False, "error": "Usage: download_pdf_worker.py <url> <output_path>"}))
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    result = asyncio.run(download_pdf_async(url, output_path))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
