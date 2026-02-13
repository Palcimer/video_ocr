"""FastAPI 서버: OCR 작업 관리 및 SSE 진행률 스트리밍."""

import asyncio
import logging
import os
import tempfile
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from backend.models import DialogueResult, OcrProgressEvent, OcrRequest
from backend.ocr_service import (
    cleanup_crops,
    create_crop_dir,
    generate_job_id,
    run_ocr_pipeline,
)

logger = logging.getLogger(__name__)

CROP_BASE_DIR = os.path.join(tempfile.gettempdir(), "video_ocr_crops")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory 작업 저장소 (단일 사용자 데스크톱 앱)
jobs: dict[str, dict] = {}


@app.get("/health")
async def health():
    """서버 상태 확인."""
    return {"status": "ok"}


@app.post("/ocr/start")
async def ocr_start(request: OcrRequest):
    """OCR 작업을 시작하고 job_id를 반환한다."""
    video_path = request.video_path
    if not Path(video_path).is_file():
        raise HTTPException(status_code=400, detail="파일을 찾을 수 없습니다")
    if not video_path.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="MP4 파일만 지원합니다")

    job_id = generate_job_id()
    crop_dir = create_crop_dir(CROP_BASE_DIR, job_id)
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    jobs[job_id] = {
        "queue": queue,
        "status": "running",
        "crop_dir": crop_dir,
        "dialogues": [],
    }

    def run_in_thread():
        def on_progress(event: OcrProgressEvent):
            loop.call_soon_threadsafe(queue.put_nowait, event)

        try:
            results = run_ocr_pipeline(
                video_path, request.lang, crop_dir, on_progress,
            )
            jobs[job_id]["dialogues"] = results
            jobs[job_id]["status"] = "done"
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except Exception as e:
            logger.exception("OCR 파이프라인 오류")
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
            loop.call_soon_threadsafe(queue.put_nowait, None)

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/ocr/progress/{job_id}")
async def ocr_progress(job_id: str):
    """SSE로 OCR 진행률을 스트리밍한다."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    queue = jobs[job_id]["queue"]

    async def event_stream():
        while True:
            event = await queue.get()
            if event is None:
                status = jobs[job_id]["status"]
                if status == "error":
                    error_msg = jobs[job_id].get("error", "알 수 없는 오류")
                    yield f"event: error\ndata: {error_msg}\n\n"
                else:
                    dialogues = jobs[job_id]["dialogues"]
                    data = [d.model_dump() for d in dialogues]
                    import json
                    yield f"event: complete\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                break
            yield f"event: progress\ndata: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/ocr/crops/{job_id}/{filename}")
async def get_crop_image(job_id: str, filename: str):
    """crop 이미지 파일을 서빙한다."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    filepath = os.path.join(jobs[job_id]["crop_dir"], filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

    return FileResponse(filepath, media_type="image/png")


@app.delete("/ocr/crops/{job_id}")
async def delete_crops(job_id: str):
    """crop 이미지 임시 디렉토리를 삭제한다."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    cleanup_crops(jobs[job_id]["crop_dir"])
    del jobs[job_id]

    return {"status": "deleted"}
