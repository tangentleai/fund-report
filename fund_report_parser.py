#!/usr/bin/env python3
"""
基金季报解析 Demo
提取基金经理观点并转换为播客脚本
"""

import re
import json
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any

# 测试用基金列表
TEST_FUNDS = [
    {"code": "005827", "name": "易方达蓝筹精选混合", "manager": "张坤"},
    {"code": "003095", "name": "中欧医疗健康混合A", "manager": "葛兰"},
    {"code": "161725", "name": "招商中证白酒指数", "manager": "侯昊"},
]


def download_fund_report(fund_code: str, fund_name: str) -> Optional[str]:
    """
    下载基金季报PDF
    注意：这里使用模拟数据，实际需要从AKShare或天天基金获取真实PDF链接
    """
    print(f"\n📥 正在获取 {fund_name}({fund_code}) 的季报...")

    # 模拟PDF下载（实际项目中使用AKShare获取真实链接）
    # 这里返回示例文本用于测试解析逻辑
    return None


def parse_pdf_content(pdf_text: str) -> Dict[str, Any]:
    """
    解析PDF内容，提取关键信息
    """
    result: Dict[str, Any] = {
        "fund_name": None,
        "report_date": None,
        "manager_viewpoint": None,
        "market_analysis": None,
        "future_outlook": None,
    }

    # 1. 提取基金名称
    name_pattern = r"基金简称[：:]\s*([^\n]+)"
    match = re.search(name_pattern, pdf_text)
    if match:
        result["fund_name"] = match.group(1).strip()

    # 2. 提取报告日期
    date_patterns = [
        r"报告期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)",
        r"(\d{4})年第([一二三四])季度报告",
        r"截至\s*(\d{4}年\d{1,2}月\d{1,2}日)",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, pdf_text)
        if match:
            result["report_date"] = match.group(0)
            break

    # 3. 提取基金经理观点 - 核心逻辑
    viewpoint = extract_manager_viewpoint(pdf_text)
    result["manager_viewpoint"] = viewpoint

    return result


def extract_manager_viewpoint(text: str) -> Optional[str]:
    """
    提取基金经理观点章节
    季报结构相对固定，重点提取"投资策略和运作分析"部分
    """
    # 清理文本
    text = clean_text(text)

    # 多种匹配模式（按优先级）
    patterns = [
        # 模式1: 精确匹配"报告期内基金投资策略和运作分析"
        r"报告期内基金投资策略和运作分析\s*[：:]?\s*\n?\s*([^§]+?)(?=\s*(?:§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
        # 模式2: 匹配"投资策略和运作分析"长段落
        r"投资策略和运作分析\s*[：:]?\s*([\s\S]{200,4000}?)(?=\s*(?:§|第[五六七八]节|第五节|重要提示|投资组合报告|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
        # 模式3: 匹配"管理人报告"下的内容
        r"管理人报告.*?基金经理.*?\n\s*([^§]+?)(?=\s*(?:§|第[五六]节|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标))",
        # 模式4: 匹配"4\.1"或"4.2"基金管理人运用固有资金投资情况前的内容
        r"4\.\d+\s*基金管理人.*?\n\s*([\s\S]{200,3000}?)(?=4\.\d+|§|第[五六]节|报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警|重大事项提示|财务指标)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            viewpoint = match.group(1).strip()
            # 进一步清洗
            viewpoint = post_clean(viewpoint)
            if validate_viewpoint(viewpoint):
                return viewpoint

    # 如果都没匹配到，尝试兜底方案：找大段连续的投资相关文本
    fallback = fallback_extract(text)
    if not fallback:
        return None
    fallback = post_clean(fallback)
    return fallback if validate_viewpoint(fallback) else None


def clean_text(text: str) -> str:
    """文本预处理"""
    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 去掉页眉页脚 (如 "第 X 页 共 Y 页")
    text = re.sub(r"第\s*\d+\s*页\s*共\s*\d+\s*页", "", text)
    text = re.sub(r"Page\s*\d+\s*of\s*\d+", "", text, flags=re.IGNORECASE)

    # 去掉页码 (如 "- 3 -" 或 "—3—")
    text = re.sub(r"[\-–—]\s*\d+\s*[\-–—]", "", text)

    # 合并单行换行，保留段落换行
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r" +", " ", text)

    # 合并多个换行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def post_clean(text: str) -> str:
    """观点提取后清洗"""
    # 去掉常见的废话开头
    useless_prefixes = [
        "报告期内，",
        "本报告期内，",
        "本基金",
        "2024年",
    ]
    for prefix in useless_prefixes:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()

    # 去掉表格残留
    text = re.sub(r"\|\s*[^\|]+\s*\|", "", text)

    # 去掉基金经理简介等噪音
    noise_patterns = [
        r"姓名\s+\w+\s+职务\s+基金经理",
        r"4\.\d+\s*基金经理.*?简介",
        r"4\.\d+\s*管理人对报告期内.*?说明",
        r"投资策略和运作分析\s*[：:]?\s*\n?",
        r"[\u4e00-\u9fffA-Za-z0-9（）()·\-]{6,}证券投资基金\d{4}年第[一二三四1234]季度报告",
        r"[\u4e00-\u9fffA-Za-z0-9（）()·\-]{6,}证券投资基金\d{4}年中期报告",
        r"[\u4e00-\u9fffA-Za-z0-9（）()·\-]{6,}证券投资基金\d{4}年度报告",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    stop_pattern = (
        r"(报告期内基金的业绩表现|基金的业绩表现|基金持有人数|基金资产净值预警"
        r"|重大事项提示|财务指标|投资组合报告|财务会计报告)"
    )
    text = re.split(stop_pattern, text, maxsplit=1)[0]
    text = re.sub(r"(4\.\d+|第[一二三四五六七八]节)\s*$", "", text).strip()

    # 清理行
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # 过滤掉太短的行
        if len(line) < 3:
            continue
        # 过滤掉只有数字或标点的行
        if re.match(r"^[\d\s\.\-—]+$", line):
            continue
        # 过滤掉基金经理信息行
        if re.match(r"^姓名|职务|基金经理", line):
            continue
        # 保留有实质内容的行
        if len(line) > 10 or re.search(r"[\u4e00-\u9fff]{3,}", line):
            cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()

    # 最终清理
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def validate_viewpoint(text: str) -> bool:
    """验证提取的观点是否有效"""
    if not text or len(text) < 50:
        return False

    # 检查是否包含投资相关关键词
    investment_keywords = [
        "市场",
        "行业",
        "配置",
        "投资",
        "策略",
        "风险",
        "机会",
        "股票",
        "债券",
        "仓位",
        "估值",
        "盈利",
        "增长",
        "经济",
    ]

    keyword_count = sum(1 for kw in investment_keywords if kw in text)
    return keyword_count >= 2  # 至少包含2个投资关键词


def fallback_extract(text: str) -> Optional[str]:
    """兜底提取方案"""
    # 查找包含投资关键词的最长连续段落
    paragraphs = re.split(r"\n{2,}", text)

    best_paragraph = None
    best_score = 0

    for para in paragraphs:
        if len(para) < 100 or len(para) > 5000:
            continue

        # 评分：包含的投资关键词越多、文本越长，分数越高
        score = len(para)
        investment_keywords = ["策略", "投资", "市场", "配置", "行业", "风险"]
        score += sum(50 for kw in investment_keywords if kw in para)

        if score > best_score:
            best_score = score
            best_paragraph = para

    return best_paragraph.strip() if best_paragraph else None


def generate_podcast_script(viewpoint: str, fund_name: str, manager: str) -> str:
    """
    将基金经理观点转换为播客对话脚本
    """
    # 这里简化处理，实际应该调用AI模型
    script = f"""
【播客脚本】{fund_name} 季报解读

主持人小明：大家好，欢迎收听本期基金季报解读。今天我们聊的是{fund_name}，基金经理是{manager}。

主持人小红：先来看基金经理在最新季报中的观点：

{viewpoint[:500]}...

主持人小明：从这段话可以看出，基金经理对后市的态度...

主持人小红：那我们对普通投资者有什么建议呢？
...
"""
    return script


def test_with_sample():
    """使用模拟数据测试解析逻辑"""

    # 模拟季报文本（实际是从PDF提取的）
    sample_report = """
易方达蓝筹精选混合型证券投资基金
2024年第4季度报告

§1 重要提示
基金管理人的董事会及董事保证本报告所载资料不存在虚假记载...

§4 管理人报告
4.1 基金经理(或基金经理小组)简介
姓名 张坤 职务 基金经理

4.2 管理人对报告期内本基金投资策略和运作分析的说明

报告期内，A股市场呈现震荡走势，沪深300指数上涨...本基金保持较高的股票仓位，重点配置了消费、医药等行业的优质企业。

从长期看，中国经济的基本面依然稳固，优质企业的护城河仍在加深。我们认为当前市场的估值水平处于历史较低位置，为长期投资者提供了较好的布局机会。

在操作上，本基金维持了对优质企业的长期持有，并根据基本面变化进行了适度调整。

§5 投资组合报告
5.1 报告期末基金资产组合情况
...
"""

    print("=" * 60)
    print("🧪 测试基金季报解析")
    print("=" * 60)

    result = parse_pdf_content(sample_report)

    print(f"\n✅ 解析结果：")
    print(f"   基金名称: {result['fund_name']}")
    print(f"   报告日期: {result['report_date']}")
    print(f"\n📝 基金经理观点:")
    print(
        f"   {result['manager_viewpoint'][:300]}..."
        if result["manager_viewpoint"]
        else "   未提取到观点"
    )

    if result["manager_viewpoint"]:
        print(f"\n🎙️  播客脚本预览:")
        script = generate_podcast_script(
            result["manager_viewpoint"], "易方达蓝筹精选混合", "张坤"
        )
        print(script[:500] + "...")

    return result


def test_real_fund(fund_code: str, fund_name: str, manager: str):
    """
    测试真实基金数据（需要AKShare）
    """
    try:
        import akshare as ak

        print(f"\n{'=' * 60}")
        print(f"🔍 获取真实数据: {fund_name}({fund_code})")
        print(f"{'=' * 60}")

        # 获取基金公告列表
        try:
            announcement_df = ak.fund_announcement_personnel_em(symbol=fund_code)
            print(f"✅ 成功获取公告列表，共 {len(announcement_df)} 条")
            print(f"\n最近几条公告：")
            print(announcement_df.head(3)[["名称", "发布时间"]].to_string(index=False))
        except Exception as e:
            print(f"⚠️  获取公告列表失败: {e}")
            return None

        # 注意：实际PDF下载需要解析公告链接
        print(f"\n💡 提示: 实际项目中需要从公告链接下载PDF并解析")

    except ImportError:
        print("❌ 未安装 AKShare，请运行: pip install akshare")
        return None

    return None


if __name__ == "__main__":
    # 1. 先用模拟数据测试解析逻辑
    print("\n" + "=" * 60)
    print("第一步：测试解析逻辑")
    print("=" * 60)
    test_with_sample()

    # 2. 尝试获取真实数据（如果安装了AKShare）
    print("\n" + "=" * 60)
    print("第二步：测试真实数据获取")
    print("=" * 60)

    try:
        test_real_fund("005827", "易方达蓝筹精选混合", "张坤")
    except Exception as e:
        print(f"⚠️  真实数据测试跳过: {e}")

    print("\n" + "=" * 60)
    print("✨ Demo 完成！")
    print("=" * 60)
    print("\n下一步建议：")
    print("1. 安装 AKShare: pip install akshare")
    print("2. 实现真实PDF下载逻辑")
    print("3. 接入AI模型生成播客脚本")
    print("4. 集成TTS生成音频")
