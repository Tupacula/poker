from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT_DIR / "data" / "templates"


class TemplateStore:
    templates_loaded = False
    templates = []

    @classmethod
    def load(cls) -> None:
        if cls.templates_loaded:
            return
        cls.templates = []
        if not TEMPLATE_DIR.exists():
            cls.templates_loaded = True
            return
        exts = {".png", ".jpg", ".jpeg"}
        for path in TEMPLATE_DIR.iterdir():
            if path.suffix.lower() not in exts:
                continue
            code = path.stem
            img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            h, w = img.shape[:2]
            cls.templates.append((code, img, w, h))
        cls.templates_loaded = True


def _to_gray_array(image) -> np.ndarray:
    if isinstance(image, Image.Image):
        arr = np.array(image.convert("RGB"))
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        return arr
    if isinstance(image, np.ndarray):
        if image.ndim == 2:
            return image
        if image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image.shape[2] == 4:
            bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    raise TypeError("image must be a PIL.Image or numpy array")


def _nms_boxes(boxes: List[Tuple[int, int, int, int]], scores: List[float], iou_thresh: float = 0.3):
    if not boxes:
        return []
    boxes_np = np.array(boxes, dtype=float)
    scores_np = np.array(scores, dtype=float)

    x1 = boxes_np[:, 0]
    y1 = boxes_np[:, 1]
    x2 = boxes_np[:, 0] + boxes_np[:, 2]
    y2 = boxes_np[:, 1] + boxes_np[:, 3]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores_np.argsort()[::-1]

    keep_indices = []
    while order.size > 0:
        i = order[0]
        keep_indices.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

        inds = np.where(iou <= iou_thresh)[0]
        order = order[inds + 1]
    return [boxes[k] for k in keep_indices], [scores[k] for k in keep_indices]


def find_cards(image, match_threshold: float = 0.8) -> List[Tuple[str, Tuple[int, int, int, int]]]:
    TemplateStore.load()
    if not TemplateStore.templates:
        return []

    gray = _to_gray_array(image)
    detections = []
    scores = []

    for code, tmpl, tw, th in TemplateStore.templates:
        res = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= match_threshold)
        for pt_y, pt_x in zip(*loc):
            x = int(pt_x)
            y = int(pt_y)
            detections.append((code, (x, y, tw, th)))
            scores.append(float(res[pt_y, pt_x]))

    if not detections:
        return []

    boxes = [bbox for _, bbox in detections]
    boxes_nms, scores_nms = _nms_boxes(boxes, scores)

    final = []
    used = set()
    for bbox, score in zip(boxes_nms, scores_nms):
        for idx, (code, bb) in enumerate(detections):
            if idx in used:
                continue
            if bb == bbox:
                used.add(idx)
                final.append((code, bbox))
                break
    return final
