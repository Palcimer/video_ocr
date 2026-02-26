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
    "left":  (280 / 2560, 1257 / 1440, 750 / 2560, 1346 / 1440),
    "right": (1749 / 2560, 1258 / 1440, 2277 / 2560, 1345 / 1440),
}
NAME_COLOR_LOWER = np.array([190, 70, 50], np.uint8)
NAME_COLOR_UPPER = np.array([255, 255, 255], np.uint8)
NAME_CORNER_APPROX_EPSILON = 0.04   # 둘레 대비 허용 오차 비율
NAME_CORNER_MAX_AREA_RATIO = 0.05   # ROI 면적 대비 코너 삼각형 최대 면적 비율

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
    """프레임에서 캐릭터명 영역을 크롭하여 반환한다.

    코너 삼각형 마커를 검출해 실제 텍스트 범위를 결정한다.
    삼각형을 찾지 못하면 전체 ROI를 반환한다.
    """

    # 영역 1차 크롭
    img_h, img_w = frame.shape[:2]
    x1_r, y1_r, x2_r, y2_r = NAME_REGIONS[side]
    x1, y1 = int(img_w * x1_r), int(img_h * y1_r)
    x2, y2 = int(img_w * x2_r), int(img_h * y2_r)
    roi = frame[y1:y2, x1:x2]
    roi_h, roi_w = roi.shape[:2]

    # 마커 컬러 범위로 마스크 생성
    color_mask = cv2.inRange(roi, NAME_COLOR_LOWER, NAME_COLOR_UPPER)
    masked_roi = cv2.bitwise_and(roi, roi, mask=color_mask)

    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 2차 크롭 위치 변수
    text_x_start = 0
    text_x_end = 0

    max_corner_area = roi_h * roi_w * NAME_CORNER_MAX_AREA_RATIO

    for contour in contours:
        # 마커 크기의 컨투어만 필터링
        if cv2.contourArea(contour) > max_corner_area:
            continue
        # 삼각형 모양의 컨투어만 필터링
        peri = cv2.arcLength(contour, True)
        if peri == 0:
            continue
        approx = cv2.approxPolyDP(contour, NAME_CORNER_APPROX_EPSILON * peri, True)
        if len(approx) != 3:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        # 왼쪽 캐릭터명일 경우 시작 마커는 0에 위치/끝 마커는 가장 x가 큰 컨투어의 x에 위치
        if side == "left":
            text_x_start = 0 + w
            text_x_end = max(x, text_x_end)
        # 오른쪽 캐릭터명일 경우 시작 마커는 가장 x가 작은 컨투어의 x에 위치/끝 마커는 오른쪽 끝에 위치
        else:
            text_x_start = min(x + w, text_x_end)
            text_x_end = roi_w - w

    if text_x_start >= text_x_end:
        return masked_roi

    return masked_roi[:, text_x_start:text_x_end]



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
