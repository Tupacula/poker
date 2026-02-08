"""
vision/config.py

Utilities for loading and saving vision calibration configuration.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT_DIR / "data" / "vision_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "hero_region": None,
    "board_region": None,
    "pot_region": None,
    "stack_region": None,
    "bet_to_call_region": None,
    "action_region": None,
    "hero_slots": 2,
    "board_slots": 5,
    "card_slot": {
        "w": None,
        "h": None,
        "x_spacing": 0,
        "y_spacing": 0,
    },
    "corner_crop": {
        "x": 0,
        "y": 0,
        "w": 40,
        "h": 40,
    },
}


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _merge_dict(dict(base[key]), value)
        else:
            base[key] = value
    return base


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load vision configuration from JSON, overlaying defaults.
    """
    config = copy.deepcopy(DEFAULT_CONFIG)
    path = path or DEFAULT_CONFIG_PATH
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                config = _merge_dict(config, data)
        except Exception:
            pass
    return config


def save_config(config: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """
    Persist vision configuration to JSON.
    """
    path = path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)
    return path


def get_region(config: Dict[str, Any], key: str) -> Optional[Tuple[int, int, int, int]]:
    """
    Return a region tuple (x, y, w, h) from config or None if invalid/missing.
    """
    raw = config.get(key)
    if not isinstance(raw, dict):
        return None
    try:
        x = int(raw.get("x", 0))
        y = int(raw.get("y", 0))
        w = int(raw.get("w", 0))
        h = int(raw.get("h", 0))
    except Exception:
        return None
    if w <= 0 or h <= 0:
        return None
    return (x, y, w, h)
