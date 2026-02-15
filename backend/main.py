import asyncio
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.database import (
    add_user_fund,
    batch_import_funds,
    create_podcast_task,
    delete_fund,
    delete_podcast,
    delete_user_fund,
    get_latest_podcast,
    get_podcast,
    get_podcast_status,
    init_db,
    list_user_funds,
    list_all_funds,
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


class BatchImportRequest(BaseModel):
    fund_codes: list[str]


class GeneratePodcastRequest(BaseModel):
    fund_code: str
    device_id: str
    report_period: str = REPORT_PERIOD


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


@app.post("/api/funds/batch-import")
def api_batch_import_funds(payload: BatchImportRequest):
    logger.info(f"批量导入基金: {len(payload.fund_codes)} 个")
    results = batch_import_funds(payload.fund_codes)
    logger.info(f"导入完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个")
    return {"data": results}


@app.get("/api/funds/all")
def api_list_all_funds():
    return {"data": list_all_funds()}


@app.delete("/api/funds/manage/{code}")
def api_delete_fund(code: str):
    logger.info(f"删除基金: {code}")
    success = delete_fund(code)
    if not success:
        raise HTTPException(status_code=404, detail="基金不存在")
    return {"data": {"success": True, "code": code}}


@app.post("/api/podcasts/generate")
async def api_generate_podcast(payload: GeneratePodcastRequest):
    report_period = payload.report_period or REPORT_PERIOD
    logger.info(f"收到生成播客请求: fund_code={payload.fund_code}, report_period={report_period}")
    existing = get_latest_podcast(payload.fund_code, report_period)
    if existing and existing["status"] == "completed":
        logger.info(f"播客已完成，直接返回: id={existing['id']}")
        return {"data": existing}
    
    task_id = None
    if existing:
        logger.info(f"重新生成播客: id={existing['id']}, status={existing['status']}")
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
        title = f"{payload.fund_code} {report_period} 季报解读"
        task_id = create_podcast_task(payload.fund_code, report_period, title)
        logger.info(f"创建新播客任务: id={task_id}")
    
    logger.info(f"启动生成任务: task_id={task_id}, fund_code={payload.fund_code}, report_period={report_period}")
    asyncio.create_task(do_generate(task_id, payload.fund_code, report_period))
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
async def api_get_podcast_status(podcast_id: int):
    podcast = get_podcast_status(podcast_id)
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return {"data": podcast}


@app.delete("/api/podcasts/{podcast_id}")
async def api_delete_podcast(podcast_id: int):
    podcast = delete_podcast(podcast_id)
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    if podcast.get("audio_url"):
        audio_path = audio_dir / Path(podcast["audio_url"]).name
        if audio_path.exists():
            try:
                audio_path.unlink()
                logger.info(f"删除音频文件: {audio_path}")
            except Exception as e:
                logger.warning(f"删除音频文件失败: {e}")
    
    return {"data": {"success": True, "id": podcast_id}}


@app.get("/api/funds/{fund_code}/report/{report_period}")
async def api_get_report_viewpoint(fund_code: str, report_period: str):
    try:
        viewpoint, fund_info = get_report_viewpoint(fund_code, report_period)
        return {
            "data": {
                "fund_code": fund_code,
                "report_period": report_period,
                "viewpoint": viewpoint,
                "fund_info": fund_info
            }
        }
    except Exception as e:
        logger.error(f"获取报告观点失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def do_generate(task_id: int, fund_code: str, report_period: str):
    logger.info(f"开始生成播客: task_id={task_id}, fund_code={fund_code}, report_period={report_period}")
    try:
        update_podcast(task_id, {"status": "generating"})
        logger.info(f"更新状态为 generating: task_id={task_id}")
        viewpoint, fund_info = get_report_viewpoint(fund_code, report_period)
        logger.info(f"获取观点完成: has_viewpoint={bool(viewpoint)}, fund_name={fund_info.get('name')}")
        if not viewpoint:
            raise ValueError("未能提取观点")
        segments = generate_dialogue_segments(
            fund_name=fund_info["name"],
            manager=fund_info["manager"],
            report_period=report_period,
            viewpoint=viewpoint,
        )
        logger.info(f"生成对话段完成: segments_count={len(segments)}")
        audio_filename = f"{fund_code}_{report_period}_{int(datetime.utcnow().timestamp())}.mp3"
        audio_path = audio_dir / audio_filename
        logger.info(f"开始合成音频: path={audio_path}")
        tts_result = await synthesize_dialogue(segments, str(audio_path))
        logger.info(f"音频合成完成: result={bool(tts_result)}")
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
                "title": f"{fund_info['name']} {report_period} 季报解读",
            },
        )
        logger.info(f"播客生成完成: task_id={task_id}, audio_url={audio_url}")
    except Exception as exc:
        logger.error(f"播客生成失败: task_id={task_id}, error={str(exc)}", exc_info=True)
        update_podcast(task_id, {"status": "failed", "error_msg": str(exc)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
