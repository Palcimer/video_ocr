"""OCR 파이프라인 오케스트레이션."""

import os
import shutil
import uuid
from collections.abc import Callable

import cv2

from backend.models import DialogueResult, OcrProgressEvent
from backend.ocr_engine import (
    create_easyocr_reader,
    get_total_frame_count,
    ocr_frame,
    preprocess_video_frames,
)

CROP_IMAGE_FORMAT = "crop_{index:04d}.png"


def generate_job_id() -> str:
    """고유 작업 ID를 생성한다."""
    return uuid.uuid4().hex[:12]


def create_crop_dir(base_dir: str, job_id: str) -> str:
    """crop 이미지 저장용 임시 디렉토리를 생성한다."""
    crop_dir = os.path.join(base_dir, job_id)
    os.makedirs(crop_dir, exist_ok=True)
    return crop_dir


def cleanup_crops(crop_dir: str) -> None:
    """crop 이미지 임시 디렉토리를 삭제한다."""
    if os.path.isdir(crop_dir):
        shutil.rmtree(crop_dir)


def _save_crop_image(crop_dir: str, index: int, image) -> str:
    """crop 이미지를 PNG로 저장하고 파일명을 반환한다."""
    filename = CROP_IMAGE_FORMAT.format(index=index)
    filepath = os.path.join(crop_dir, filename)
    cv2.imwrite(filepath, image)
    return filename


ProgressCallback = Callable[[OcrProgressEvent], None]


def run_ocr_pipeline(
    video_path: str,
    lang: str,
    crop_dir: str,
    on_progress: ProgressCallback,
) -> list[DialogueResult]:
    """비디오 OCR 파이프라인을 실행한다.

    1단계(scan): 비디오에서 대사 전환 프레임을 수집한다.
    2단계(ocr): 수집된 프레임에 OCR을 실행한다.

    Args:
        video_path: MP4 파일 경로
        lang: OCR 언어 코드 (기본 "kor")
        crop_dir: crop 이미지 저장 디렉토리
        on_progress: 진행률 콜백 함수
    """
    total_video_frames = get_total_frame_count(video_path)

    # 1단계: 프레임 스캔
    collected_frames = []
    frame_index = 0
    for masked, name_roi, bubble_crop in preprocess_video_frames(video_path):
        collected_frames.append((masked, name_roi, bubble_crop))
        frame_index += 1
        on_progress(OcrProgressEvent(
            phase="scan",
            current=frame_index,
            total=total_video_frames,
        ))

    # 2단계: OCR 실행
    total_dialogues = len(collected_frames)
    reader = create_easyocr_reader(lang)
    results = []

    for i, (masked, name_roi, bubble_crop) in enumerate(collected_frames):
        crop_filename = _save_crop_image(crop_dir, i, bubble_crop)
        ocr_result = ocr_frame(masked, name_roi, lang, reader)
        text = ocr_result["text"]

        dialogue = DialogueResult(
            index=i,
            speaker=ocr_result["speaker"],
            text=text,
            crop_filename=crop_filename,
        )
        # 앞 대사와 비교해서 같은 대사는 삭제
        prev_text = results[len(results) - 1].text
        if text.startswith(prev_text) :
            results.pop()

        results.append(dialogue)

        on_progress(OcrProgressEvent(
            phase="ocr",
            current=i + 1,
            total=total_dialogues,
            dialogue=dialogue,
        ))

    return results
