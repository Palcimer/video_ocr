"""FastAPI 요청/응답 Pydantic 모델."""

from pydantic import BaseModel


class OcrRequest(BaseModel):
    """OCR 시작 요청."""

    video_path: str
    lang: str = "kor"


class DialogueResult(BaseModel):
    """단일 대사 OCR 결과."""

    index: int
    speaker: str
    text: str
    crop_filename: str


class OcrProgressEvent(BaseModel):
    """OCR 진행률 SSE 이벤트 데이터."""

    phase: str  # "scan" | "ocr"
    current: int
    total: int
    dialogue: DialogueResult | None = None
