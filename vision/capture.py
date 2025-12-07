from typing import Dict, List, Tuple

import pyautogui
from PIL import Image

from . import card_reader


def _split_board_and_hero(detections: List[Tuple[str, Tuple[int, int, int, int]]]):
    if not detections:
        return [], []

    detections_sorted = sorted(detections, key=lambda d: d[1][1])
    ys = [d[1][1] for d in detections_sorted]
    median_y = sorted(ys)[len(ys) // 2]

    board = [d for d in detections_sorted if d[1][1] <= median_y]
    hero = [d for d in detections_sorted if d[1][1] > median_y]

    board = sorted(board, key=lambda d: d[1][0])
    hero = sorted(hero, key=lambda d: d[1][0])

    board_codes = [code for code, _ in board]
    hero_codes = [code for code, _ in hero]

    return board_codes, hero_codes


def capture_table() -> Dict:
    screenshot: Image.Image = pyautogui.screenshot()
    detections = card_reader.find_cards(screenshot)

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
