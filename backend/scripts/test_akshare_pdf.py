import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services.report_parser import get_report_viewpoint


def main():
    parser = argparse.ArgumentParser(description="测试AKShare季报下载与PDF解析")
    parser.add_argument("--fund-code", required=True, help="基金代码，如 005827")
    parser.add_argument("--report-period", default="2024Q4", help="报告期，如 2024Q4")
    args = parser.parse_args()

    viewpoint, fund = get_report_viewpoint(args.fund_code, args.report_period)
    if fund["name"] == args.fund_code and fund["manager"] == "未知":
        print("提示: 未找到基金基础信息，已使用代码作为名称")
    print(f"基金: {fund['name']}({fund['code']}) 经理: {fund['manager']}")
    print(f"观点预览: {viewpoint}")


if __name__ == "__main__":
    main()
