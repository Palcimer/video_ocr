# 리팩토링: 이미지 작업 남김

import argparse
import json
import sys
import pytesseract
import cv2
import traceback
import numpy as np
import easyocr

# thresholding
def thresholding(image):
    # 그레이스케일
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 업스케일(2배)
    image = cv2.resize(image, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    # 블러 처리
    image = cv2.GaussianBlur(image, (5, 5), 0)
    # 이진화
    _, thresholded_image = cv2.threshold(
        image,
        210,
        255,
        cv2.THRESH_BINARY
    )
    return thresholded_image

# 말풍선 검출
def detect_bubble(image):
    img_h, img_w = image.shape[:2]
    total_pixels = img_h * img_w

    # 가로 최소 위치, 가로 최대 위치, 세로 최대 위치, 최소 면적 
    x_min = int(img_w * 0.2695)   # 690 / 2560
    x_max = int(img_w * 0.3711)   # 950 / 2560
    y_max = int(img_h * 0.3472)   # 500 / 1440
    min_area = int(total_pixels * 0.0244)  # 90000 / (2560*1440)

    # 윤곽 추출
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    bubble_contours = []
    for i in contours:
        x, y, w, h = cv2.boundingRect(i)
        if cv2.contourArea(i) > min_area and x_min <= x <= x_max and y < y_max:
            bubble_contours.append(i)
    return bubble_contours

# 말풍선 boundingRect 검출
def detect_bubble_rects(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return x, y, w, h

# 말풍선 좌우 판별
def get_bubble_side(contour, img_w):
    x, _, w, _ = cv2.boundingRect(contour)
    center_x = x + w / 2
    return 'left' if center_x < img_w / 2 else 'right'

# 캐릭터명 영역 크롭 (2560x1440 기준 비율)
# mask_name_left.png:  x=280, y=1257, w=270, h=89
# mask_name_right.png: x=2049, y=1258, w=228, h=87
NAME_REGIONS = {
    'left':  (280 / 2560, 1257 / 1440, 550 / 2560, 1346 / 1440),
    'right': (2049 / 2560, 1258 / 1440, 2277 / 2560, 1345 / 1440),
}

# 캐릭터명 영역 크롭
def get_name_region(frame, side):
    img_h, img_w = frame.shape[:2]
    x1_r, y1_r, x2_r, y2_r = NAME_REGIONS[side]
    x1, y1 = int(img_w * x1_r), int(img_h * y1_r)
    x2, y2 = int(img_w * x2_r), int(img_h * y2_r)
    return frame[y1:y2, x1:x2]

# 마스크 생성
def create_mask(contours, image_shape):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, contours, -1, 255, -1) # -1: 안쪽 채우기
    return mask

# 이미지 전처리
def preprocess(img):
    th = thresholding(img)
    bubble_contours = detect_bubble(th)

    # 말풍선으로 마스크 만들기
    mask = create_mask(bubble_contours, th.shape)

    # 마스크 적용
    th = cv2.bitwise_and(th, th, mask=mask)

    cv2.imshow("mask", mask)
    cv2.imshow("th", th)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 글자 획을 약간 정리(과하면 뭉개짐)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    cv2.imwrite("preprocessed3.png", th)

    return th


# 비디오 전처리
def preprocess_video(video):
    cap = cv2.VideoCapture(video)
    to_ocr_frames = []  # (thresholded_frame, name_region) 튜플 리스트
    ret, raw = cap.read()
    frame = thresholding(raw)
    bubble_contours = detect_bubble(frame)
    if len(bubble_contours) > 0:
       mask = create_mask(bubble_contours, frame.shape)
       masked = cv2.bitwise_and(frame, frame, mask=mask)
       side = get_bubble_side(bubble_contours[0], frame.shape[1])
       name_roi = get_name_region(raw, side)
       to_ocr_frames.append((masked, name_roi))
    prev_bubble_contours = bubble_contours
    prev_frame = frame
    i = 0

    while(1):
        ret, raw = cap.read()
        if not ret:
            break

        frame = thresholding(raw)
        bubble_contours = detect_bubble(frame)

        # 말풍선 없으면 건너뛰기
        if len(bubble_contours) == 0:
            prev_bubble_contours = []
            continue

        # 말풍선 변화 비교 (이전 말풍선이 있을 때만)
        if len(prev_bubble_contours) > 0:
            x1, y1, w1, h1 = detect_bubble_rects(bubble_contours[0])
            x2, y2, w2, h2 = detect_bubble_rects(prev_bubble_contours[0])
            prev_frame_dhash = dhash(prev_frame[y2:y2+h2, x2:x2+w2])
            curr_frame_dhash = dhash(frame[y1:y1+h1, x1:x1+w1])
            if prev_frame_dhash is not None:
                dist = hamming_distance(prev_frame_dhash, curr_frame_dhash)
                if dist <= 6:
                    continue

        # 변화가 있음(말풍선 추가/전환)
        mask = create_mask(bubble_contours, frame.shape)
        masked = cv2.bitwise_and(frame, frame, mask=mask)
        side = get_bubble_side(bubble_contours[0], frame.shape[1])
        name_roi = get_name_region(raw, side)
        cv2.imwrite(f"name_{i}.png", name_roi)
        to_ocr_frames.append((masked, name_roi))
        prev_bubble_contours = bubble_contours
        prev_frame = frame
        cv2.imwrite(f"frame_180_{i}.png", masked)
        i += 1

    print(len(to_ocr_frames))
    return to_ocr_frames

def run_ocr(image_path: str, roi, lang: str):
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Cannot read image: {image_path}")

    if roi:
        x, y, w, h = roi
        img = img[y:y+h, x:x+w]

    proc = preprocess(img)

    # PSM은 UI 텍스트 형태에 따라 성능이 갈림:
    # 6: uniform block of text
    # 7: single text line
    config = "--oem 1 --psm 6 -c preserve_interword_spaces=1"
    text = pytesseract.image_to_string(proc, lang=lang, config=config)

    # 간단 후처리: 공백 정리
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return text

def run_ocr_video(image_path: str, roi, lang: str):
    if image_path is None:
        raise RuntimeError(f"Cannot read image: {image_path}")

    proc = preprocess_video(image_path)

    # PSM은 UI 텍스트 형태에 따라 성능이 갈림:
    # 6: uniform block of text
    # 7: single text line
    config = "--oem 1 --psm 6 -c preserve_interword_spaces=1"
    name_config = "--oem 1 --psm 7 -c preserve_interword_spaces=1"
    reader = easyocr.Reader(['ko'], gpu=True)
    results = []

    for frame, name_roi in proc:
        # 대사 OCR
        text = pytesseract.image_to_string(frame, lang=lang, config=config)
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if len(text) == 0:
            print("No text detected")
            result = reader.readtext(frame)
            print("EasyOCR result:", result)
            text = ' '.join([res[1] for res in result])

        # 캐릭터명 OCR (thresholding 적용)
        name_th = thresholding(name_roi)
        name = pytesseract.image_to_string(name_th, lang=lang, config=name_config)
        name = name.strip()
        if len(name) == 0:
            name_result = reader.readtext(name_th)
            name = ' '.join([res[1] for res in name_result])

        results.append({"name": name, "text": text})
        print(f"[{name}] {text}")

    return results

def dhash(gray_roi: np.ndarray, hash_size: int = 8) -> int:
    """
    gray_roi: grayscale ROI (H,W), dtype uint8
    returns: 64-bit hash as python int (hash_size=8일 때)
    """
    # (hash_size+1, hash_size)로 리사이즈 (가로로 1 더 크게)
    resized = cv2.resize(gray_roi, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)

    # 인접 픽셀 비교: 오른쪽이 더 밝으면 True
    diff = resized[:, 1:] > resized[:, :-1]   # shape: (hash_size, hash_size), bool

    # bool 배열을 64비트 정수로 패킹
    # (행 우선) 비트열로 만든 뒤 int로 변환
    bits = diff.flatten()
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h

def hamming_distance(h1: int, h2: int) -> int:
    return (h1 ^ h2).bit_count()  # Python 3.8+는 int.bit_count() 사용 가능

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--roi", default=None)
    ap.add_argument("--lang", default="kor")  # kor, eng, kor+eng
    args = ap.parse_args()

    try:
        if args.image.endswith(('.mp4', '.avi', '.mov')):
            text = run_ocr_video(args.image, roi, args.lang)
        else:
            text = run_ocr(args.image, roi, args.lang)
        print(json.dumps({"ok": True, "text": text}, ensure_ascii=False))
    except Exception as e:
        traceback.print_exc()
        # print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
