from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT_DIR / "data" / "templates"

Detection = Tuple[str, Tuple[int, int, int, int]]


class TemplateStore:
    templates_loaded = False
    templates: List[Tuple[str, np.ndarray]] = []

    @classmethod
    def _load_templates(cls) -> None:
        cls.templates = []
        if not TEMPLATE_DIR.exists():
            cls.templates_loaded = True
            return
        for path in TEMPLATE_DIR.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue
            img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            code = path.stem
            cls.templates.append((code, img))
        cls.templates_loaded = True

    @classmethod
    def get_templates(cls) -> List[Tuple[str, np.ndarray]]:
        if not cls.templates_loaded:
            cls._load_templates()
        return cls.templates


def _pil_to_gray(image: Image.Image) -> np.ndarray:
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image)
    image = image.convert("L")
    return np.array(image)


def _match_templates(
    image_gray: np.ndarray,
    threshold: float = 0.8,
) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
    detections: List[Tuple[str, float, Tuple[int, int, int, int]]] = []
    templates = TemplateStore.get_templates()
    if not templates:
        return []

    for code, tmpl in templates:
        th, tw = tmpl.shape[:2]
        if image_gray.shape[0] < th or image_gray.shape[1] < tw:
            continue
        result = cv2.matchTemplate(image_gray, tmpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= threshold)
        for y, x in zip(ys, xs):
            score = float(result[y, x])
            bbox = (int(x), int(y), int(tw), int(th))
            detections.append((code, score, bbox))
    return detections


def _iou(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b

    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh

    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = aw * ah
    area_b = bw * bh
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


def _nms(
    dets: List[Tuple[str, float, Tuple[int, int, int, int]]],
    iou_threshold: float = 0.3,
) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
    if not dets:
        return []

    dets_sorted = sorted(dets, key=lambda d: d[1], reverse=True)
    kept: List[Tuple[str, float, Tuple[int, int, int, int]]] = []

    while dets_sorted:
        best = dets_sorted.pop(0)
        kept.append(best)
        _, _, best_box = best
        remaining = []
        for det in dets_sorted:
            _, _, box = det
            if _iou(best_box, box) < iou_threshold:
                remaining.append(det)
        dets_sorted = remaining
    return kept


def find_cards(image: Image.Image) -> List[Detection]:
    gray = _pil_to_gray(image)
    raw_dets = _match_templates(gray)
    nms_dets = _nms(raw_dets)

    final: List[Detection] = []
    for code, score, bbox in nms_dets:
        final.append((code, bbox))
    return final
