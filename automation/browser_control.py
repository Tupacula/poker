"""Browser / UI automation helpers.

This module provides simple functions to click the Fold/Call/Raise buttons.
For initial testing it uses `pyautogui` to click coordinates defined in
`ui_coords.json`. When integrating into a specific site prefer Playwright or
Selenium for robust DOM-targeted interactions.
"""
import json
from pathlib import Path
import time

try:
    import pyautogui
except Exception:
    pyautogui = None


CONFIG_PATH = Path(__file__).resolve().parents[1] / "automation" / "ui_coords.json"


def load_coords():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_action(action: str):
    """Execute action string: 'fold' | 'call' | 'raise'."""
    coords = load_coords()
    btn = coords.get(action)
    if not btn:
        print(f"No coordinates for action '{action}' — not clicking.")
        return
    x, y = btn
    if pyautogui:
        pyautogui.moveTo(x, y)
        pyautogui.click()
    else:
        print(f"pyautogui not installed; would click at {(x, y)}")
    time.sleep(0.2)
