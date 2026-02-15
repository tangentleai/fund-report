import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

# get_fund_by_code 替换为 akshare 获取
from fund_report_parser import extract_manager_viewpoint, parse_pdf_content


logger = logging.getLogger(__name__)


def _get_fund_info_by_akshare(fund_code: str) -> Optional[Dict]:
    """使用 akshare 获取基金基本信息"""
    try:
        import akshare as ak

        try:
            info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
            if info_df is not None and not info_df.empty:
                info_map = {
                    str(row["item"]).strip(): str(row["value"]).strip()
                    for _, row in info_df.iterrows()
                }
                return {
                    "code": fund_code,
                    "name": info_map.get("基金名称", fund_code),
                    "manager": info_map.get("基金经理", "未知"),
                    "fund_type": info_map.get("基金类型"),
                }
        except Exception:
            pass
        try:
            announcement_df = ak.fund_announcement_personnel_em(symbol=fund_code)
            if announcement_df is not None and not announcement_df.empty:
                name_col = None
                for col in announcement_df.columns:
                    if "名称" in str(col) or "name" in str(col).lower():
                        name_col = col
                        break
                if name_col:
                    fund_name = str(announcement_df.iloc[0][name_col])
                    fund_name = fund_name.split("-")[0].split("_")[0].strip()
                    return {
                        "code": fund_code,
                        "name": fund_name if fund_name else fund_code,
                        "manager": "未知",
                        "fund_type": None,
                    }
        except Exception:
            pass
    except Exception:
        logger.debug("akshare 获取基金信息失败: %s", fund_code)
    return None


SAMPLE_REPORTS = {
    "005827": """
易方达蓝筹精选混合型证券投资基金
2024年第4季度报告

§4 管理人报告
4.2 管理人对报告期内本基金投资策略和运作分析的说明

报告期内，A股市场呈现震荡走势，沪深300指数上涨。本基金保持较高的股票仓位，重点配置了消费、医药等行业的优质企业。

从长期看，中国经济的基本面依然稳固，优质企业的护城河仍在加深。我们认为当前市场的估值水平处于历史较低位置，为长期投资者提供了较好的布局机会。

在操作上，本基金维持了对优质企业的长期持有，并根据基本面变化进行了适度调整。
""",
    "003095": """
中欧医疗健康混合型证券投资基金
2024年第4季度报告

§4 管理人报告
4.2 管理人对报告期内本基金投资策略和运作分析的说明

报告期内，医药行业面临阶段性压力，但创新药与高端医疗器械仍保持较强增长。基金继续聚焦具备研发优势和渠道壁垒的核心资产。

我们认为行业政策逐步明朗，估值处于合理区间，未来将通过精选个股提升组合质量。
""",
    "161725": """
招商中证白酒指数型证券投资基金
2024年第4季度报告

§4 管理人报告
4.2 管理人对报告期内本基金投资策略和运作分析的说明

报告期内，白酒板块经历估值修复后进入震荡阶段，基金维持指数化跟踪策略，保持对龙头企业的配置。

我们预计消费复苏带动龙头盈利改善，长期配置价值仍在，但需关注短期波动风险。
""",
}


def get_report_viewpoint(fund_code: str, report_period: str) -> Tuple[str, Dict]:
    fund = _get_fund_info_by_akshare(fund_code)
    if not fund:
        fund = {
            "code": fund_code,
            "name": fund_code,
            "manager": "未知",
            "fund_type": None,
        }
        logger.warning("基金基础信息缺失，使用默认占位信息: %s", fund_code)
    report_text = _load_real_report_text(fund_code, report_period)
    if not report_text:
        report_text = SAMPLE_REPORTS.get(fund_code)
        if report_text:
            logger.info("未找到真实季报，回落到内置样例文本: %s", fund_code)
    viewpoint = None
    if report_text:
        parsed = parse_pdf_content(report_text)
        viewpoint = parsed.get("manager_viewpoint") or extract_manager_viewpoint(
            report_text
        )
        logger.info(
            "观点提取结果: length=%s, has_viewpoint=%s",
            len(viewpoint) if viewpoint else 0,
            bool(viewpoint),
        )
    if not viewpoint:
        viewpoint = ""
        logger.warning("观点为空: %s", fund_code)
    return viewpoint, fund


def _load_real_report_text(fund_code: str, report_period: str) -> Optional[str]:
    pdf_path = _download_latest_quarter_report(fund_code, report_period)
    if not pdf_path:
        logger.warning("未能下载真实季报PDF: %s %s", fund_code, report_period)
        return None
    
    # 验证文件是否为有效的PDF
    try:
        with pdf_path.open("rb") as f:
            header = f.read(5)
        if not header.startswith(b"%PDF-"):
            logger.warning("下载的文件不是有效的PDF，删除: %s", pdf_path)
            pdf_path.unlink(missing_ok=True)
            return None
    except Exception:
        logger.warning("验证PDF文件失败: %s", pdf_path)
        return None
    
    text = _extract_pdf_text(pdf_path)
    if not text:
        logger.warning("PDF解析为空: %s", pdf_path)
    else:
        logger.info("PDF解析成功: %s chars", len(text))
    return text


def _download_latest_quarter_report(
    fund_code: str, report_period: str
) -> Optional[Path]:
    try:
        import akshare as ak
    except Exception:
        logger.warning("AKShare未安装或导入失败")
        return None
    announcement_df = None
    try:
        announcement_df = ak.fund_announcement_report_em(symbol=fund_code)
    except Exception:
        announcement_df = None
    if announcement_df is None or announcement_df.empty:
        try:
            announcement_df = ak.fund_announcement_personnel_em(symbol=fund_code)
        except Exception:
            announcement_df = None
    if announcement_df is None or announcement_df.empty:
        logger.warning("公告列表获取失败: %s", fund_code)
        return None
    if announcement_df is None or announcement_df.empty:
        logger.warning("公告列表为空: %s", fund_code)
        return None
    name_column = _pick_column(
        announcement_df.columns, ["名称", "公告标题", "标题", "公告名称"]
    )
    date_column = _pick_column(
        announcement_df.columns, ["发布时间", "公告日期", "发布日期", "日期"]
    )
    link_column = _pick_column(
        announcement_df.columns,
        ["公告链接", "链接", "url", "URL", "公告url", "公告链接地址"],
    )
    report_id_column = _pick_column(
        announcement_df.columns,
        ["报告ID", "公告ID", "公告代码", "报告编号", "infocode"],
    )
    if not name_column or (not link_column and not report_id_column):
        logger.warning(
            "公告字段缺失: name=%s link=%s report_id=%s",
            name_column,
            link_column,
            report_id_column,
        )
        return None
    df = announcement_df.copy()
    df = df[df[name_column].astype(str).str.contains("季度报告|季报", regex=True)]
    if df.empty:
        logger.warning("未找到季度报告公告: %s", fund_code)
        return None
    if date_column:
        df[date_column] = df[date_column].apply(_parse_date)
        df = df.sort_values(date_column, ascending=False)
    latest = df.iloc[0]
    
    report_dir = Path(__file__).resolve().parents[1] / "data" / "reports" / fund_code
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / _build_report_filename(latest[name_column], report_period)
    
    if file_path.exists():
        try:
            with file_path.open("rb") as f:
                header = f.read(5)
            if header.startswith(b"%PDF-"):
                logger.info("命中缓存PDF: %s", file_path)
                return file_path
            else:
                logger.warning("缓存文件不是有效的PDF，删除并重新下载: %s", file_path)
                file_path.unlink()
        except Exception:
            logger.warning("验证缓存PDF失败，删除并重新下载: %s", file_path)
            file_path.unlink(missing_ok=True)
    
    urls_to_try = []
    
    if link_column:
        url = str(latest[link_column])
        if url and url.startswith("http"):
            urls_to_try.append(url)
    
    if report_id_column:
        report_id = str(latest[report_id_column])
        urls_to_try.extend(_get_pdf_urls(report_id))
    
    if not urls_to_try:
        logger.warning("没有可用的URL来下载PDF")
        return None
    
    headers = _get_browser_headers()
    session = requests.Session()
    
    for url in urls_to_try:
        try:
            logger.info(f"尝试下载PDF: {url}")
            
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            content = response.content
            
            if content.startswith(b"%PDF-"):
                file_path.write_bytes(content)
                logger.info(f"✓ 成功下载PDF: {file_path}")
                return file_path
            
            if b"<script" in content[:500]:
                logger.warning(f"遇到反爬虫JS验证，尝试使用Playwright: {url}")
                success = _download_with_playwright(url, file_path)
                if success:
                    return file_path
                continue
                
            pdf_url = _extract_pdf_url_from_html(response.text)
            if pdf_url:
                logger.info(f"从HTML中提取到PDF链接: {pdf_url}")
                pdf_response = session.get(pdf_url, headers=headers, timeout=30)
                pdf_response.raise_for_status()
                pdf_content = pdf_response.content
                if pdf_content.startswith(b"%PDF-"):
                    file_path.write_bytes(pdf_content)
                    logger.info(f"✓ 成功下载PDF: {file_path}")
                    return file_path
                    
        except Exception as e:
            logger.warning(f"下载失败 {url}: {e}")
            continue
    
    logger.warning("所有下载方法都失败了")
    return None


def _download_with_playwright(url: str, output_path: Path) -> bool:
    """使用 Playwright 下载 PDF（处理反爬虫） - 通过 subprocess 调用独立脚本"""
    import subprocess
    import json
    
    worker_script = Path(__file__).resolve().parents[1] / "scripts" / "download_pdf_worker.py"
    
    if not worker_script.exists():
        logger.warning(f"下载工作脚本不存在: {worker_script}")
        return False
    
    try:
        logger.info(f"通过 subprocess 调用下载脚本: {worker_script}")
        
        result = subprocess.run(
            [
                sys.executable,
                str(worker_script),
                url,
                str(output_path)
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("success"):
                    logger.info(f"✓ subprocess 下载成功: {data.get('path')}")
                    return True
                else:
                    logger.warning(f"subprocess 下载失败: {data.get('error')}")
            except json.JSONDecodeError:
                logger.warning(f"解析 subprocess 输出失败: {result.stdout}")
        else:
            logger.warning(f"subprocess 执行失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.warning("subprocess 下载超时")
    except Exception as e:
        logger.warning(f"subprocess 调用失败: {e}")
    
    return False


def _build_report_filename(title: str, report_period: str) -> str:
    suffix = report_period
    match = re.search(r"(\d{4})年?第([一二三四1234])季度", title)
    if match:
        year = match.group(1)
        quarter = match.group(2)
        quarter_map = {"一": "1", "二": "2", "三": "3", "四": "4"}
        quarter = quarter_map.get(quarter, quarter)
        suffix = f"{year}Q{quarter}"
    safe_title = re.sub(r"[^\w\u4e00-\u9fff]+", "_", title)[:40]
    return f"{suffix}_{safe_title}.pdf"


def _extract_pdf_text(pdf_path: Path) -> Optional[str]:
    try:
        import pdfplumber
    except Exception:
        logger.warning("pdfplumber未安装或导入失败")
        return None
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
    except Exception:
        logger.exception("PDF解析异常: %s", pdf_path)
        return None
    text = "\n".join([page for page in pages if page])
    return text if text.strip() else None


def _extract_pdf_url_from_html(html: str) -> Optional[str]:
    match = re.search(r'(https?://[^"\']+?\.pdf[^"\']*)', html, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _build_pdf_url_from_report_id(report_id: str) -> Optional[str]:
    if not report_id:
        return None
    return f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf"


def _get_pdf_urls(report_id: str) -> list[str]:
    """生成多个可能的PDF URL格式"""
    urls = []
    if report_id.startswith("AN"):
        urls.append(f"https://pdf.dfcfw.com/pdf/H2_{report_id}_1.pdf")
        urls.append(f"https://pdf.dfcfw.com/pdf/H3_{report_id}_1.pdf")
        urls.append(f"https://pdf.dfcfw.com/pdf/H1_{report_id}_1.pdf")
        urls.append(f"https://pdf.dfcfw.com/pdf/{report_id}_1.pdf")
    return urls


def _get_browser_headers() -> dict:
    """获取模拟浏览器的请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }


def _pick_column(columns, candidates) -> Optional[str]:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    for candidate in candidates:
        for col in columns:
            if str(col).lower() == candidate.lower():
                return col
    return None


def _parse_date(value) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text[:10], fmt)
        except Exception:
            continue
    return datetime.min
