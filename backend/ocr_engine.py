"""OCR 엔진: 비디오 프레임 전처리 및 텍스트 인식."""

from collections.abc import Generator

import cv2
import easyocr
import numpy as np
import pytesseract

from backend.image_processing import (
    HAMMING_THRESHOLD,
    UPSCALE_FACTOR,
    create_mask,
    detect_bubble,
    detect_bubble_rects,
    dhash,
    get_bubble_side,
    get_name_region,
    hamming_distance,
    thresholding,
)

# --- OCR 설정 상수 ---
TESSERACT_PSM_BLOCK = 6
TESSERACT_PSM_LINE = 7
TESSERACT_OEM = 1
DEFAULT_LANG = "kor"

DIALOGUE_CONFIG = (
    f"--oem {TESSERACT_OEM} --psm {TESSERACT_PSM_BLOCK}"
    " -c preserve_interword_spaces=1"
)
NAME_CONFIG = (
    f"--oem {TESSERACT_OEM} --psm {TESSERACT_PSM_LINE}"
    " -c preserve_interword_spaces=1"
)


def create_easyocr_reader(lang: str = DEFAULT_LANG) -> easyocr.Reader:
    """EasyOCR Reader를 생성한다. 로딩이 느리므로 한 번만 호출한다."""
    lang_list = ["ko"] if lang == "kor" else [lang]
    return easyocr.Reader(lang_list, gpu=True)


def get_total_frame_count(video_path: str) -> int:
    """비디오의 총 프레임 수를 반환한다."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"비디오를 열 수 없습니다: {video_path}")
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return count


def _crop_bubble_region(raw_frame: np.ndarray, contour) -> np.ndarray:
    """원본 프레임에서 말풍선 바운딩 렉트 영역을 크롭한다.

    thresholding에서 UPSCALE_FACTOR(2배) 업스케일하므로
    좌표를 원본 스케일로 역변환한다.
    """
    x, y, w, h = detect_bubble_rects(contour)
    scale = int(UPSCALE_FACTOR)
    ox, oy = x // scale, y // scale
    ow, oh = w // scale, h // scale
    return raw_frame[oy:oy + oh, ox:ox + ow]


def preprocess_video_frames(
    video_path: str,
) -> Generator[tuple[np.ndarray, np.ndarray, np.ndarray], None, None]:
    """비디오에서 대사가 전환된 프레임을 하나씩 yield한다.

    Yields:
        (masked_frame, name_roi, bubble_crop) 튜플
        - masked_frame: 이진화 + 마스크 적용된 프레임 (OCR 입력용)
        - name_roi: 캐릭터명 영역 크롭 (원본 프레임 기준)
        - bubble_crop: 말풍선 영역 크롭 (원본 프레임 기준, 팝업 표시용)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"비디오를 열 수 없습니다: {video_path}")

    prev_bubble_contours = []
    prev_frame = None

    try:
        while True:
            ret, raw = cap.read()
            if not ret:
                break

            frame = thresholding(raw)
            bubble_contours = detect_bubble(frame)

            if len(bubble_contours) == 0:
                prev_bubble_contours = []
                prev_frame = frame
                continue

            # 이전 말풍선이 있으면 변화 비교
            if len(prev_bubble_contours) > 0 and prev_frame is not None:
                x1, y1, w1, h1 = detect_bubble_rects(bubble_contours[0])
                x2, y2, w2, h2 = detect_bubble_rects(prev_bubble_contours[0])
                prev_hash = dhash(prev_frame[y2:y2 + h2, x2:x2 + w2])
                curr_hash = dhash(frame[y1:y1 + h1, x1:x1 + w1])
                dist = hamming_distance(prev_hash, curr_hash)
                if dist <= HAMMING_THRESHOLD:
                    continue

            # 대사 전환 감지됨
            mask = create_mask(bubble_contours, frame.shape)
            masked = cv2.bitwise_and(frame, frame, mask=mask)
            side = get_bubble_side(bubble_contours[0], frame.shape[1])
            name_roi = get_name_region(raw, side)
            bubble_crop = _crop_bubble_region(raw, bubble_contours[0])

            prev_bubble_contours = bubble_contours
            prev_frame = frame

            yield masked, name_roi, bubble_crop
    finally:
        cap.release()


def _clean_ocr_text(raw_text: str) -> str:
    """OCR 결과에서 빈 줄을 제거하고 공백을 정리한다."""
    return "\n".join(
        line.strip() for line in raw_text.splitlines() if line.strip()
    )


def ocr_frame(
    frame: np.ndarray,
    name_roi: np.ndarray,
    lang: str,
    reader: easyocr.Reader,
) -> dict[str, str]:
    """단일 프레임에서 대사와 화자명을 OCR로 인식한다.

    Returns:
        {"speaker": str, "text": str}
    """
    # 대사 OCR: Tesseract 우선
    text = pytesseract.image_to_string(frame, lang=lang, config=DIALOGUE_CONFIG)
    text = _clean_ocr_text(text)
    if len(text) == 0:
        result = reader.readtext(frame)
        text = " ".join(res[1] for res in result)

    # 화자명 OCR: thresholding 후 인식
    name_th = thresholding(name_roi)
    name = pytesseract.image_to_string(name_th, lang=lang, config=NAME_CONFIG)
    name = name.strip()
    if len(name) == 0:
        name_result = reader.readtext(name_th)
        name = " ".join(res[1] for res in name_result)

    return {"speaker": name, "text": text}
