from typing import Dict, List, Tuple
import io

from PIL import Image

from . import card_reader

Detection = Tuple[str, Tuple[int, int, int, int]]


def _split_board_and_hero(detections: List[Detection]):
    if not detections:
        return [], []

    detections_sorted = sorted(detections, key=lambda d: d[1][1])
    ys = [bbox[1] for _, bbox in detections_sorted]
    median_y = sorted(ys)[len(ys) // 2]

    board = []
    hero = []
    for code, (x, y, w, h) in detections_sorted:
        if y <= median_y:
            board.append((code, (x, y, w, h)))
        else:
            hero.append((code, (x, y, w, h)))

    board_sorted = [code for code, bbox in sorted(board, key=lambda d: d[1][0])]
    hero_sorted = [code for code, bbox in sorted(hero, key=lambda d: d[1][0])]
    return board_sorted, hero_sorted


def _capture_state_from_image(image: Image.Image) -> Dict:
    detections = card_reader.find_cards(image)
    board_codes, hero_codes = _split_board_and_hero(detections)

    state = {
        "hero_cards": hero_codes,
        "board": board_codes,
        "raw_detections": detections,
        "pot": None,
        "to_act": "hero",
        "stack": None,
        "bet_to_call": None,
    }
    return state


def capture_state_from_playwright(page) -> Dict:
    png_bytes = page.screenshot(full_page=True)
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return _capture_state_from_image(image)


def capture_state_from_selenium(driver) -> Dict:
    png_bytes = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return _capture_state_from_image(image)


def capture_state_from_image(image: Image.Image) -> Dict:
    return _capture_state_from_image(image)
