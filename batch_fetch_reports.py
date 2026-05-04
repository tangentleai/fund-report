#!/usr/bin/env python3
"""批量拉取自选基金报告观点，返回 JSON 格式（直接调用后端函数，无需启动服务）"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_FUND_LIST = PROJECT_ROOT / "docs" / "my-fund-list.md"

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def load_fund_codes(path: str) -> list[str]:
    codes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and line.isdigit():
                codes.append(line)
    return codes


def fetch_report(fund_code: str, report_period: str) -> dict:
    from backend.services.report_parser import get_report_viewpoint

    start = time.time()
    try:
        viewpoint, fund_info = get_report_viewpoint(fund_code, report_period)
        elapsed = time.time() - start
        return {
            "fund_code": fund_code,
            "fund_name": fund_info.get("name", ""),
            "manager": fund_info.get("manager", ""),
            "report_period": report_period,
            "viewpoint": viewpoint or "",
            "success": True,
            "elapsed_seconds": round(elapsed, 1),
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "fund_code": fund_code,
            "report_period": report_period,
            "success": False,
            "error": str(e),
            "elapsed_seconds": round(elapsed, 1),
        }


def batch_fetch(fund_codes: list[str], report_period: str, interval: float = 1.0) -> dict:
    results = []
    total = len(fund_codes)

    for i, code in enumerate(fund_codes):
        result = fetch_report(code, report_period)
        results.append(result)
        idx = i + 1
        if result["success"]:
            vp_len = len(result.get("viewpoint", ""))
            name = result.get("fund_name", code)
            print(f"[{idx}/{total}] ✓ {code} {name} - 观点{vp_len}字 ({result['elapsed_seconds']}s)")
        else:
            print(f"[{idx}/{total}] ✗ {code} - {result.get('error', '未知错误')}")

        if idx < total:
            time.sleep(interval)

    success = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    return {
        "report_period": report_period,
        "total": total,
        "success_count": len(success),
        "failed_count": len(failed),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="批量拉取自选基金报告观点（直接调用后端函数）")
    parser.add_argument(
        "-f", "--fund-list",
        default=str(DEFAULT_FUND_LIST),
        help=f"基金代码列表文件路径 (默认: {DEFAULT_FUND_LIST})",
    )
    parser.add_argument(
        "-p", "--period",
        default="2025Q4",
        help="报告期 (默认: 2025Q4)",
    )
    parser.add_argument(
        "-c", "--codes",
        nargs="+",
        help="直接指定基金代码，覆盖文件读取",
    )
    parser.add_argument(
        "-o", "--output",
        help="输出 JSON 文件路径 (默认输出到 stdout)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="每只基金之间的间隔秒数 (默认: 1.0)",
    )
    args = parser.parse_args()

    if args.codes:
        fund_codes = args.codes
    else:
        fund_codes = load_fund_codes(args.fund_list)

    if not fund_codes:
        print("未找到基金代码", file=sys.stderr)
        sys.exit(1)

    print(f"开始批量拉取: {len(fund_codes)} 只基金, 报告期: {args.period}")
    print("-" * 60)

    output = batch_fetch(fund_codes, args.period, args.interval)

    print("-" * 60)
    print(f"完成: 成功 {output['success_count']}/{output['total']}, 失败 {output['failed_count']}")

    json_str = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"结果已写入: {args.output}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
