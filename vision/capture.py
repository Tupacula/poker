"""
vision/capture.py

Responsible for:
  - Taking a screenshot from a Playwright page
  - Running card detection on that screenshot
  - Packaging the result into a raw dictionary that main.py can normalize

This module currently only parses hero and board cards using template matching.
Numeric fields such as pot, stack, and bet_to_call are left as None for now.
You can later extend this file to call OCR helpers to populate those values.
"""

from typing import Dict, List, Tuple
import io

from PIL import Image

from . import card_reader

# Detection = (card_code, (x, y, w, h))
Detection = Tuple[str, Tuple[int, int, int, int]]


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

    # Sort by y (vertical) position
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

    # Sort each group horizontally by x
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


def capture_state_from_playwright(page) -> Dict:
    """
    Capture and parse table state from a Playwright page.

    Steps:
      1. Take a PNG screenshot of the full page.
      2. Convert the screenshot into a PIL Image.
      3. Run card detection and packaging via _capture_state_from_image.

    This function is the entry point used by main.run_single_decision_step.
    """
    png_bytes = page.screenshot(full_page=True)
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return _capture_state_from_image(image)


def capture_state_from_image(image: Image.Image) -> Dict:
    """
    Public helper for offline testing.

    You can load an image from disk in a notebook or a small script and call:

        state = capture_state_from_image(Image.open("example.png"))

    to debug card detection without involving Playwright.
    """
    return _capture_state_from_image(image)
