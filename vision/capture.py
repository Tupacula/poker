"""
vision/capture.py

Responsible for:
  - Taking a screenshot from a Playwright page
  - Running card detection on that screenshot
  - Packaging the result into a raw dictionary that main.py can normalize

Numeric fields such as pot, stack, and bet_to_call are left as None for now.
You can later extend this file to call OCR helpers to populate those values.
"""

from typing import Dict, List, Optional, Tuple
import io
import logging
import time
from pathlib import Path

from PIL import Image

from . import card_reader
from .config import get_region, load_config

# Detection = (card_code, (x, y, w, h))
Detection = Tuple[str, Tuple[int, int, int, int]]

# Optional static fallbacks; prefer DOM-derived regions when available.
HERO_REGION_FALLBACK: Optional[Tuple[int, int, int, int]] = None
BOARD_REGION_FALLBACK: Optional[Tuple[int, int, int, int]] = None

logger = logging.getLogger(__name__)


class CaptureError(RuntimeError):
    """Raised when a screenshot cannot be taken or parsed."""


def screenshot_page(page, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
    """
    Take a screenshot of the Playwright page and return a PIL Image.

    Parameters:
      page   - Playwright page
      region - optional (x, y, w, h) to crop after capture

    Raises CaptureError if the page is closed or screenshot fails.
    """
    if page is None or getattr(page, "is_closed", lambda: True)():
        raise CaptureError("Cannot capture screenshot: page is not ready or already closed")

    try:
        png_bytes = page.screenshot(full_page=True)
    except Exception as exc:
        raise CaptureError(f"Failed to take screenshot: {exc}") from exc

    try:
        image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception as exc:
        raise CaptureError(f"Failed to decode screenshot into image: {exc}") from exc

    if region:
        image = crop_region(image, region)

    return image


def crop_region(image: Image.Image, region: Tuple[int, int, int, int]) -> Image.Image:
    """
    Crop a PIL Image to the given region (x, y, w, h).
    """
    x, y, w, h = region
    return image.crop((x, y, x + w, y + h))


def get_full_page_image(page) -> Image.Image:
    """Helper alias to capture the entire page as a PIL Image."""
    return screenshot_page(page)


def get_table_region(page, region: Tuple[int, int, int, int]) -> Image.Image:
    """
    Capture and return only the table region as a PIL Image.
    Useful once you know the bounding box of the poker table.
    """
    return screenshot_page(page, region=region)


def _split_board_and_hero(detections: List[Detection]) -> Tuple[List[str], List[str]]:
    """
    Split detected cards into board and hero cards based on vertical position.

    Assumptions:
      - Board cards are visually above hero cards on the screen.
      - Both sets of cards are roughly in horizontal rows.

    Strategy:
      1. Sort detections by y coordinate.
      2. Use the median y as a rough separator line.
      3. Cards above or equal to that line are "board", below are "hero".
      4. Within each group, sort by x for left-to-right ordering.
    """
    if not detections:
        return [], []

    detections_sorted = sorted(detections, key=lambda d: d[1][1])

    ys = [bbox[1] for _, bbox in detections_sorted]
    median_y = sorted(ys)[len(ys) // 2]

    board: List[Detection] = []
    hero: List[Detection] = []

    for code, (x, y, w, h) in detections_sorted:
        if y <= median_y:
            board.append((code, (x, y, w, h)))
        else:
            hero.append((code, (x, y, w, h)))

    board_sorted = [code for code, bbox in sorted(board, key=lambda d: d[1][0])]
    hero_sorted = [code for code, bbox in sorted(hero, key=lambda d: d[1][0])]

    return board_sorted, hero_sorted


def _capture_state_from_image(image: Image.Image) -> Dict:
    """
    Core implementation that works off a PIL image.

    This allows:
      - Playwright based capture
      - Offline testing by loading images from disk

    Returns a raw dictionary with the keys that main.normalize_state expects.
    Numeric fields are currently left as None until OCR is wired in.
    """
    detections: List[Detection] = card_reader.find_cards(image)

    board_codes, hero_codes = _split_board_and_hero(detections)

    state: Dict = {
        "hero_cards": hero_codes,
        "board": board_codes,
        "raw_detections": detections,
        # The following are intentionally None for now.
        # TODO: use OCR to fill these once you have stable regions and ocr_utils.
        "pot": None,
        "to_act": "hero",
        "stack": None,
        "bet_to_call": None,
    }
    return state


def _get_bounding_box(page, selector: str) -> Optional[Tuple[int, int, int, int]]:
    """
    Return a bounding box (x, y, w, h) for a DOM element, if available.
    """
    if not hasattr(page, "query_selector"):
        return None
    try:
        elem = page.query_selector(selector)
        if elem is None:
            return None
        box = elem.bounding_box()
        if not box:
            return None
        return (
            int(box.get("x", 0)),
            int(box.get("y", 0)),
            int(box.get("width", 0)),
            int(box.get("height", 0)),
        )
    except Exception as exc:  # pragma: no cover - depends on Playwright runtime
        logger.debug("Failed to get bounding box for %s: %s", selector, exc)
        return None


def _resolve_regions(page) -> Dict[str, Optional[Tuple[int, int, int, int]]]:
    """
    Find hero/board regions, preferring config -> DOM -> fallbacks.
    """
    config = load_config()
    hero_region = get_region(config, "hero_region") or _get_bounding_box(page, "#hero") or HERO_REGION_FALLBACK
    board_region = get_region(config, "board_region") or _get_bounding_box(page, "#board") or BOARD_REGION_FALLBACK
    regions: Dict[str, Optional[Tuple[int, int, int, int]]] = {
        "hero_region": hero_region,
        "board_region": board_region,
        "pot_region": get_region(config, "pot_region"),
        "stack_region": get_region(config, "stack_region"),
        "bet_to_call_region": get_region(config, "bet_to_call_region"),
        "action_region": get_region(config, "action_region"),
    }
    return regions


def _save_image(image: Image.Image, path: Path) -> None:
    """Save a PIL Image to disk, ensuring parent directories exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def capture_state_from_playwright(page, dump_dir: Optional[str] = None) -> Dict:
    """
    Capture and parse table state from a Playwright page.

    Steps:
      1. Take a PNG screenshot of the full page.
      2. Convert the screenshot into a PIL Image.
      3. Run card detection and packaging via _capture_state_from_image.

    This function is the entry point used by main.run_single_decision_step.
    """
    image = screenshot_page(page)
    regions = _resolve_regions(page)
    state = _capture_state_from_image(image)
    state.update(regions)

    if dump_dir:
        timestamp = int(time.time() * 1000)
        dump_path = Path(dump_dir)

        screenshot_path = dump_path / f"frame_{timestamp}.png"
        _save_image(image, screenshot_path)
        state["screenshot_path"] = str(screenshot_path)

        hero_region = regions.get("hero_region")
        if hero_region:
            hero_crop = crop_region(image, hero_region)
            hero_path = dump_path / f"frame_{timestamp}_hero.png"
            _save_image(hero_crop, hero_path)
            state["hero_crop_path"] = str(hero_path)

        board_region = regions.get("board_region")
        if board_region:
            board_crop = crop_region(image, board_region)
            board_path = dump_path / f"frame_{timestamp}_board.png"
            _save_image(board_crop, board_path)
            state["board_crop_path"] = str(board_path)

    return state


def capture_state_from_image(image: Image.Image) -> Dict:
    """
    Public helper for offline testing.

    You can load an image from disk in a notebook or a small script and call:

        state = capture_state_from_image(Image.open("example.png"))

    to debug card detection without involving Playwright.
    """
    return _capture_state_from_image(image)
