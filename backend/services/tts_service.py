from typing import Dict, List, Optional

from tts_service import DialogueSegment, EdgeTTSService


async def synthesize_dialogue(
    segments: List[DialogueSegment], output_path: str
) -> Optional[Dict]:
    service = EdgeTTSService(rate_limit=10)
    result = await service.generate_dialogue(segments, output_path=output_path)
    return result
