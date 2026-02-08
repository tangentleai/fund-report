#!/usr/bin/env python3
"""
TTS服务 - MVP版本
使用Edge TTS（免费）快速验证，预留商业TTS切换接口
"""

import asyncio
import edge_tts
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DialogueSegment:
    """对话片段"""

    speaker: str  # "小明" 或 "小红"
    text: str
    start_time: float = 0.0  # 在最终音频中的起始时间


class TTSService:
    """
    TTS服务基类
    预留接口，方便后期切换到商业TTS
    """

    async def generate(self, text: str, voice: str, output_path: str) -> bool:
        """生成音频"""
        raise NotImplementedError

    async def generate_dialogue(
        self, segments: List[DialogueSegment], output_path: str
    ) -> Optional[Dict]:
        """生成对话音频"""
        raise NotImplementedError


class EdgeTTSService(TTSService):
    """
    Edge TTS 实现（MVP阶段使用）
    基于微软Edge浏览器的朗读功能
    """

    # 声音配置
    VOICES = {
        "male": "zh-CN-YunxiNeural",  # 小明 - 男声，热情自然
        "female": "zh-CN-XiaoxiaoNeural",  # 小红 - 女声，亲切自然
        "male_alt": "zh-CN-YunjianNeural",  # 备选男声
        "female_alt": "zh-CN-XiaoyiNeural",  # 备选女声
    }

    def __init__(self, rate_limit: int = 5):
        """
        Args:
            rate_limit: 每分钟最大请求数，防止被封
        """
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_reset = datetime.now()

    async def _check_rate_limit(self):
        """简单的速率限制"""
        now = datetime.now()
        if (now - self.last_reset).seconds >= 60:
            self.request_count = 0
            self.last_reset = now

        if self.request_count >= self.rate_limit:
            wait_time = 60 - (now - self.last_reset).seconds
            if wait_time > 0:
                logger.warning(f"触发速率限制，等待 {wait_time} 秒")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_reset = datetime.now()

    async def generate(
        self, text: str, voice: str = "male", output_path: str = None
    ) -> Optional[str]:
        """
        生成单段音频

        Args:
            text: 要转换的文本
            voice: 声音类型 (male/female)
            output_path: 输出文件路径

        Returns:
            成功返回文件路径，失败返回None
        """
        await self._check_rate_limit()

        if output_path is None:
            output_path = f"/tmp/tts_{hash(text)}.mp3"

        voice_name = self.VOICES.get(voice, self.VOICES["male"])

        try:
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(output_path)
            self.request_count += 1
            logger.info(f"✅ TTS生成成功: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ TTS生成失败: {e}")
            return None

    async def generate_dialogue(
        self, segments: List[DialogueSegment], output_path: str = "output.mp3"
    ) -> Optional[Dict]:
        """
        生成对话音频（多角色）

        Args:
            segments: 对话片段列表
            output_path: 最终音频输出路径

        Returns:
            包含音频路径和元数据的字典
        """
        if not segments:
            logger.error("对话片段为空")
            return None

        temp_files = []
        transcripts = []
        current_time = 0.0

        try:
            # 1. 为每个片段生成音频
            for i, segment in enumerate(segments):
                voice = "male" if segment.speaker == "小明" else "female"
                temp_path = f"/tmp/dialogue_{i}_{hash(segment.text)}.mp3"

                result = await self.generate(segment.text, voice, temp_path)
                if result:
                    temp_files.append(result)
                    duration = self._get_audio_duration(result) or len(segment.text) / 3.5
                    transcripts.append(
                        {
                            "time": round(current_time, 1),
                            "speaker": segment.speaker,
                            "text": segment.text,
                        }
                    )
                    current_time += duration
                else:
                    logger.warning(f"片段 {i} 生成失败，跳过")

            # 2. 合并音频（简化版，实际应该用ffmpeg或pydub）
            await self._merge_audio_files(temp_files, output_path)

            # 3. 清理临时文件
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink()
                except:
                    pass

            return {
                "audio_path": output_path,
                "duration": round(current_time, 1),
                "transcript": transcripts,
                "format": "mp3",
            }

        except Exception as e:
            logger.error(f"对话生成失败: {e}")
            return None

    async def _merge_audio_files(self, files: List[str], output: str):
        try:
            from pydub import AudioSegment

            combined = AudioSegment.empty()
            for file in files:
                audio = AudioSegment.from_mp3(file)
                combined += audio

            combined.export(output, format="mp3")
            logger.info(f"✅ 音频合并完成: {output}")
            return
        except Exception:
            pass

        import shutil
        import subprocess

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg and files:
            list_file = Path(output).with_suffix(".txt")
            list_content = "".join([f"file '{file}'\n" for file in files])
            list_file.write_text(list_content, encoding="utf-8")
            try:
                subprocess.run(
                    [
                        ffmpeg,
                        "-y",
                        "-f",
                        "concat",
                        "-safe",
                        "0",
                        "-i",
                        str(list_file),
                        "-c:a",
                        "libmp3lame",
                        "-q:a",
                        "2",
                        output,
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if Path(output).exists():
                    list_file.unlink(missing_ok=True)
                    return
            except Exception:
                list_file.unlink(missing_ok=True)

        if files:
            shutil.copy(files[0], output)

    def _get_audio_duration(self, file_path: str) -> Optional[float]:
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_mp3(file_path)
            return len(audio) / 1000.0
        except Exception:
            return None


class AzureTTSService(TTSService):
    """
    Azure TTS 实现（生产环境使用）
    预留接口，MVP后再实现
    """

    def __init__(self, subscription_key: str, region: str):
        self.subscription_key = subscription_key
        self.region = region
        # TODO: 实现Azure TTS
        pass

    async def generate(self, text: str, voice: str, output_path: str) -> bool:
        # TODO: 实现Azure TTS
        raise NotImplementedError("Azure TTS尚未实现")


# ============ 使用示例 ============


async def demo():
    """演示如何使用TTS服务"""

    print("=" * 60)
    print("🎙️  Edge TTS 演示")
    print("=" * 60)

    # 初始化服务
    tts = EdgeTTSService(rate_limit=10)

    # 示例1：单段音频
    print("\n1️⃣  生成单段音频...")
    result = await tts.generate(
        text="大家好，欢迎收听本期基金季报解读。",
        voice="male",
        output_path="demo_single.mp3",
    )
    if result:
        print(f"   ✅ 已保存: {result}")

    # 示例2：多角色对话
    print("\n2️⃣  生成播客对话...")
    dialogue = [
        DialogueSegment("小明", "大家好，今天我们聊一下易方达蓝筹基金2024年四季报。"),
        DialogueSegment("小红", "张坤这季度说了什么重点呢？"),
        DialogueSegment(
            "小明", "他说主要看好消费和医药板块，认为当前估值处于历史低位。"
        ),
        DialogueSegment("小红", "那对我们普通投资者有什么建议吗？"),
        DialogueSegment("小明", "建议保持长期持有，不要被短期波动影响。"),
    ]

    result = await tts.generate_dialogue(
        segments=dialogue, output_path="demo_podcast.mp3"
    )

    if result:
        print(f"\n✅ 播客生成成功！")
        print(f"   文件: {result['audio_path']}")
        print(f"   时长: {result['duration']}秒")
        print(f"\n📄 文字稿:")
        for item in result["transcript"]:
            print(
                f"   [{item['time']:>5.1f}s] {item['speaker']}: {item['text'][:30]}..."
            )

    print("\n" + "=" * 60)
    print("✨ 演示完成！")
    print("=" * 60)
    print("\n💡 生产环境建议：")
    print("   1. 安装 pydub: pip install pydub")
    print("   2. 安装 ffmpeg: brew install ffmpeg (Mac)")
    print("   3. 实现 AzureTTSService 用于正式环境")


if __name__ == "__main__":
    asyncio.run(demo())
