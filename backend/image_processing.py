"""이미지 전처리 및 말풍선 검출 함수."""

import cv2
import numpy as np

# --- 이미지 전처리 상수 ---
UPSCALE_FACTOR = 2.0
BLUR_KERNEL = (5, 5)
BINARY_THRESHOLD = 210
# --- 말풍선 검출 비율 상수 (2560x1440 기준 비율) ---
BUBBLE_X_MIN_RATIO = 0.2695    # 690 / 2560
BUBBLE_X_MAX_RATIO = 0.3711    # 950 / 2560
BUBBLE_Y_MAX_RATIO = 0.3472    # 500 / 1440
BUBBLE_MIN_AREA_RATIO = 0.0244  # 90000 / (2560*1440)

# --- 캐릭터명 영역 비율 (2560x1440 기준) ---
NAME_REGIONS = {
    "left":  (280 / 2560, 1257 / 1440, 550 / 2560, 1346 / 1440),
    "right": (2049 / 2560, 1258 / 1440, 2277 / 2560, 1345 / 1440),
}

# --- 프레임 변화 감지 상수 ---
DHASH_SIZE = 8
HAMMING_THRESHOLD = 6


def thresholding(image: np.ndarray) -> np.ndarray:
    """그레이스케일 변환 → 업스케일 → 블러 → 이진화."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    upscaled = cv2.resize(
        gray, None, fx=UPSCALE_FACTOR, fy=UPSCALE_FACTOR,
        interpolation=cv2.INTER_CUBIC,
    )
    blurred = cv2.GaussianBlur(upscaled, BLUR_KERNEL, 0)
    _, binary = cv2.threshold(
        blurred, BINARY_THRESHOLD, 255, cv2.THRESH_BINARY,
    )
    return binary


def detect_bubble(image: np.ndarray) -> list:
    """이진화된 이미지에서 말풍선 윤곽선을 검출한다."""
    img_h, img_w = image.shape[:2]
    total_pixels = img_h * img_w

    x_min = int(img_w * BUBBLE_X_MIN_RATIO)
    x_max = int(img_w * BUBBLE_X_MAX_RATIO)
    y_max = int(img_h * BUBBLE_Y_MAX_RATIO)
    min_area = int(total_pixels * BUBBLE_MIN_AREA_RATIO)

    contours, _ = cv2.findContours(
        image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,
    )

    bubble_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if area > min_area and x_min <= x <= x_max and y < y_max:
            bubble_contours.append(contour)

    return bubble_contours


def detect_bubble_rects(contour) -> tuple[int, int, int, int]:
    """윤곽선의 바운딩 렉트를 반환한다."""
    return cv2.boundingRect(contour)


def get_bubble_side(contour, img_w: int) -> str:
    """말풍선이 화면 좌측/우측 중 어디에 있는지 판별한다."""
    x, _, w, _ = cv2.boundingRect(contour)
    center_x = x + w / 2
    return "left" if center_x < img_w / 2 else "right"


def get_name_region(frame: np.ndarray, side: str) -> np.ndarray:
    """프레임에서 캐릭터명 영역을 크롭한다."""
    img_h, img_w = frame.shape[:2]
    x1_r, y1_r, x2_r, y2_r = NAME_REGIONS[side]
    x1, y1 = int(img_w * x1_r), int(img_h * y1_r)
    x2, y2 = int(img_w * x2_r), int(img_h * y2_r)
    return frame[y1:y2, x1:x2]


def create_mask(contours: list, image_shape: tuple) -> np.ndarray:
    """윤곽선 리스트로 마스크 이미지를 생성한다."""
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, contours, -1, 255, -1)
    return mask


def dhash(gray_roi: np.ndarray, hash_size: int = DHASH_SIZE) -> int:
    """그레이스케일 ROI의 차이 해시(dhash)를 계산한다."""
    resized = cv2.resize(
        gray_roi, (hash_size + 1, hash_size),
        interpolation=cv2.INTER_AREA,
    )
    diff = resized[:, 1:] > resized[:, :-1]
    bits = diff.flatten()
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h


def hamming_distance(h1: int, h2: int) -> int:
    """두 해시 간의 해밍 거리를 계산한다."""
    return (h1 ^ h2).bit_count()
