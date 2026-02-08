import json
import os
from pathlib import Path
from typing import List

from openai import OpenAI

from tts_service import DialogueSegment


def generate_dialogue_segments(
    fund_name: str,
    manager: str,
    report_period: str,
    viewpoint: str,
) -> List[DialogueSegment]:
    _load_env()
    api_key = os.environ.get("ARK_API_KEY")
    if api_key:
        segments = _generate_with_ark(
            api_key=api_key,
            fund_name=fund_name,
            manager=manager,
            report_period=report_period,
            viewpoint=viewpoint,
        )
        if segments:
            return segments
    return _generate_fallback_segments(fund_name, manager, report_period, viewpoint)


def _load_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _generate_with_ark(
    api_key: str,
    fund_name: str,
    manager: str,
    report_period: str,
    viewpoint: str,
) -> List[DialogueSegment]:
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )
    model = os.environ.get("ARK_MODEL", "ep-20260208171328-jgc8q")
    prompt = (
        "请基于以下基金经理观点，生成双人播客对话。"
        "要求：用中文、通俗、段落清晰。"
        "输出严格JSON数组，每项包含speaker和text字段。"
        f"基金：{fund_name}，基金经理：{manager}，报告期：{report_period}。"
        f"观点：{viewpoint}"
    )
    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
        tools=[
            {
                "type": "web_search",
                "max_keyword": 2,
            }
        ],
    )
    content = response.output_text
    try:
        items = json.loads(content)
    except json.JSONDecodeError:
        return []
    segments = []
    for item in items:
        speaker = item.get("speaker") or "小明"
        text = item.get("text") or ""
        if text.strip():
            segments.append(DialogueSegment(speaker=speaker, text=text.strip()))
    return segments


def _generate_fallback_segments(
    fund_name: str,
    manager: str,
    report_period: str,
    viewpoint: str,
) -> List[DialogueSegment]:
    intro = (
        f"大家好，欢迎收听本期基金季报解读。今天我们聊的是{fund_name}，"
        f"基金经理是{manager}，报告期为{report_period}。"
    )
    summary = viewpoint.strip().replace("\n", " ")
    summary = summary[:240] + "..." if len(summary) > 240 else summary
    segments = [
        DialogueSegment(speaker="小明", text=intro),
        DialogueSegment(speaker="小红", text="我们先来看看基金经理的核心观点。"),
        DialogueSegment(speaker="小明", text=summary),
        DialogueSegment(speaker="小红", text="整体来看，这份观点强调了行业与估值的取舍。"),
        DialogueSegment(speaker="小明", text="以上就是本期解读内容，感谢收听。"),
    ]
    return segments
