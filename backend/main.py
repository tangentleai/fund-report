import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.database import (
    add_user_fund,
    create_podcast_task,
    delete_user_fund,
    get_latest_podcast,
    get_podcast,
    get_podcast_status,
    init_db,
    list_user_funds,
    search_funds,
    update_podcast,
)
from backend.services.ai_service import generate_dialogue_segments
from backend.services.report_parser import get_report_viewpoint
from backend.services.tts_service import synthesize_dialogue

REPORT_PERIOD = "2024Q4"


class AddFundRequest(BaseModel):
    device_id: str
    fund_code: str


class GeneratePodcastRequest(BaseModel):
    fund_code: str
    device_id: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audio_dir = Path(__file__).resolve().parent / "audio"
audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/funds/search")
def api_search_funds(q: Optional[str] = None):
    return {"data": search_funds(q or "")}


@app.post("/api/funds")
def api_add_fund(payload: AddFundRequest):
    add_user_fund(payload.device_id, payload.fund_code)
    return {"data": True}


@app.get("/api/funds")
def api_list_funds(device_id: str):
    return {"data": list_user_funds(device_id)}


@app.delete("/api/funds/{code}")
def api_delete_fund(code: str, device_id: str):
    delete_user_fund(device_id, code)
    return {"data": True}


@app.post("/api/podcasts/generate")
def api_generate_podcast(payload: GeneratePodcastRequest):
    existing = get_latest_podcast(payload.fund_code, REPORT_PERIOD)
    if existing and existing["status"] == "completed":
        return {"data": existing}
    if existing and existing["status"] in {"pending", "generating"}:
        return {"data": existing}
    if existing and existing["status"] == "failed":
        update_podcast(
            existing["id"],
            {
                "status": "pending",
                "error_msg": None,
                "audio_url": None,
                "duration": None,
                "transcript": None,
            },
        )
        task_id = existing["id"]
    else:
        title = f"{payload.fund_code} {REPORT_PERIOD} 季报解读"
        task_id = create_podcast_task(payload.fund_code, REPORT_PERIOD, title)
    asyncio.create_task(do_generate(task_id, payload.fund_code))
    return {
        "data": {
            "id": task_id,
            "status": "generating",
            "estimated_time": 120,
        }
    }


@app.get("/api/podcasts/{podcast_id}")
def api_get_podcast(podcast_id: int):
    podcast = get_podcast(podcast_id)
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return {"data": podcast}


@app.get("/api/podcasts/{podcast_id}/status")
def api_get_podcast_status(podcast_id: int):
    podcast = get_podcast_status(podcast_id)
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return {"data": podcast}


async def do_generate(task_id: int, fund_code: str):
    try:
        update_podcast(task_id, {"status": "generating"})
        viewpoint, fund_info = get_report_viewpoint(fund_code, REPORT_PERIOD)
        if not viewpoint:
            raise ValueError("未能提取观点")
        segments = generate_dialogue_segments(
            fund_name=fund_info["name"],
            manager=fund_info["manager"],
            report_period=REPORT_PERIOD,
            viewpoint=viewpoint,
        )
        audio_filename = f"{fund_code}_{REPORT_PERIOD}_{int(datetime.utcnow().timestamp())}.mp3"
        audio_path = audio_dir / audio_filename
        tts_result = await synthesize_dialogue(segments, str(audio_path))
        if not tts_result:
            raise ValueError("音频生成失败")
        audio_url = f"/audio/{audio_filename}"
        update_podcast(
            task_id,
            {
                "status": "completed",
                "audio_url": audio_url,
                "duration": tts_result["duration"],
                "transcript": tts_result["transcript"],
                "title": f"{fund_info['name']} {REPORT_PERIOD} 季报解读",
            },
        )
    except Exception as exc:
        update_podcast(task_id, {"status": "failed", "error_msg": str(exc)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
