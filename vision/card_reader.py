"""
vision/card_reader.py

Responsible for:
  - Detecting individual cards in a screenshot
  - Using OpenCV template matching against card templates
  - Exposing simple APIs for hole/board detection

Expected template setup:
  - Directory: data/templates/
  - Files: one image per card, such as "As.png", "Kd.png", "2c.png", etc.
    where the stem of the filename (without extension) is the card code.

Runtime behavior:
  - If no templates are found, find_cards will return an empty list.
    This allows you to run the pipeline before templates are ready.
"""

from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore
    CV2_AVAILABLE = False

# Detection = (card_code, (x, y, w, h))
Detection = Tuple[str, Tuple[int, int, int, int]]

# Project root is assumed to be one level up from this file's parent:
#   <project_root> / vision / card_reader.py
ROOT_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT_DIR / "data" / "templates"


class TemplateStore:
    """
    Lazy loader for card templates.

    Templates are loaded once on first access, then cached in memory.

    Each entry in templates is a tuple:
      (card_code, template_image_gray)
    """

    templates_loaded: bool = False
    templates: List[Tuple[str, np.ndarray]] = []

    @classmethod
    def _load_templates(cls) -> None:
        """
        Load all card templates from TEMPLATE_DIR.

        This method is intentionally tolerant:
          - If TEMPLATE_DIR does not exist, it simply records an empty list.
          - If individual files cannot be read, they are skipped.
        """
        cls.templates = []

        if not CV2_AVAILABLE or not TEMPLATE_DIR.exists():
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

            code = path.stem  # for example "As", "Kd", "2c"
            cls.templates.append((code, img))

        cls.templates_loaded = True

    @classmethod
    def get_templates(cls) -> List[Tuple[str, np.ndarray]]:
        """
        Return the list of loaded templates, loading them on first use.
        """
        if not cls.templates_loaded:
            cls._load_templates()
        return cls.templates


def _pil_to_gray(image: Image.Image) -> np.ndarray:
    """
    Convert a PIL Image to a grayscale numpy array suitable for OpenCV.

    If 'image' is already a numpy array, it is wrapped into a PIL Image first
    to normalize the conversion behavior.
    """
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image)
    image = image.convert("L")
    return np.array(image)


def _match_templates(
    image_gray: np.ndarray,
    threshold: float = 0.8,
) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
    """
    Run template matching for all loaded card templates.

    Returns a list of:
      (card_code, score, (x, y, w, h))

    where score is the normalized cross correlation from cv2.matchTemplate.

    The 'threshold' parameter controls how strict we are about matches.
    You can tune this later once you have real templates and screenshots.
    """
    detections: List[Tuple[str, float, Tuple[int, int, int, int]]] = []

    if not CV2_AVAILABLE:
        return []

    templates = TemplateStore.get_templates()
    if not templates:
        return []

    for code, tmpl in templates:
        th, tw = tmpl.shape[:2]

        # Skip if template is larger than the image
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
    """
    Compute intersection over union for two bounding boxes.

    Boxes are given as (x, y, w, h).
    """
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

    inter_area = float(inter_x2 - inter_x1) * float(inter_y2 - inter_y1)
    area_a = float(aw * ah)
    area_b = float(bw * bh)
    union = area_a + area_b - inter_area
    if union <= 0.0:
        return 0.0

    return inter_area / union


def _nms(
    dets: List[Tuple[str, float, Tuple[int, int, int, int]]],
    iou_threshold: float = 0.3,
) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
    """
    Non-maximum suppression to remove overlapping detections.

    Input:
      dets - list of (card_code, score, bbox)
    Output:
      list of filtered detections, keeping only the highest scoring
      detection for overlapping boxes.
    """
    if not dets:
        return []

    # Sort by score, descending
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


def _split_board_and_hero(detections: List[Detection]) -> Tuple[List[str], List[str]]:
    """
    Heuristic split of detections into board and hero rows based on y-position.

    Board is assumed to appear above hero cards. Within each row, detections
    are sorted by x so the output order is left-to-right.
    """
    if not detections:
        return [], []

    sorted_by_y = sorted(detections, key=lambda d: d[1][1])
    ys = [bbox[1] for _, bbox in sorted_by_y]
    median_y = sorted(ys)[len(ys) // 2]

    board, hero = [], []
    for code, (x, y, w, h) in sorted_by_y:
        if y <= median_y:
            board.append((code, (x, y, w, h)))
        else:
            hero.append((code, (x, y, w, h)))

    board_sorted = [code for code, bbox in sorted(board, key=lambda d: d[1][0])]
    hero_sorted = [code for code, bbox in sorted(hero, key=lambda d: d[1][0])]
    return board_sorted, hero_sorted


def find_cards(image: Image.Image) -> List[Detection]:
    """
    Detect cards in the given image using template matching.

    Returns:
      A list of (card_code, (x, y, w, h)) tuples.

    If no templates are present in data/templates, this function will
    return an empty list. That allows you to run the rest of the pipeline
    before you have card templates ready.
    """
    gray = _pil_to_gray(image)
    raw_dets = _match_templates(gray)
    nms_dets = _nms(raw_dets)

    final: List[Detection] = []
    for code, score, bbox in nms_dets:
        final.append((code, bbox))

    return final


def detect_hole_cards(image: Image.Image) -> List[str]:
    """
    Public API to detect hero hole cards.

    Returns list of codes like ["As", "Kd"] in left-to-right order.
    Uses heuristic row split; refine once table layout is known.
    """
    detections = find_cards(image)
    _, hero = _split_board_and_hero(detections)
    return hero


def detect_board_cards(image: Image.Image) -> List[str]:
    """
    Public API to detect board cards.

    Returns list of 0..5 codes in left-to-right order.
    Uses heuristic row split; refine once table layout is known.
    """
    detections = find_cards(image)
    board, _ = _split_board_and_hero(detections)
    return board


# TODO: replace the simple heuristic split and template matching thresholds
# with layout-aware regions once real templates and UI coordinates are available. 
