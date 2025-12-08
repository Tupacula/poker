"""OCR helpers for reading numeric and textual UI elements.

Wraps common Tesseract configuration and provides small helpers used by
`capture.py` and `card_reader.py`.
"""
from typing import Dict, Optional, Tuple

import pytesseract
from PIL import Image


DEFAULT_TESS_CONFIG = {
    "lang": "eng",
    "oem": 3,  # default engine
    "psm": 6,  # assume a block of text
}


def build_tesseract_config(
    lang: str = DEFAULT_TESS_CONFIG["lang"],
    oem: int = DEFAULT_TESS_CONFIG["oem"],
    psm: int = DEFAULT_TESS_CONFIG["psm"],
    extra: Optional[str] = None,
) -> str:
    """
    Build the Tesseract CLI config string.

    Returns something like: "-l eng --oem 3 --psm 6"
    """
    parts = [f"-l {lang}", f"--oem {oem}", f"--psm {psm}"]
    if extra:
        parts.append(extra)
    return " ".join(parts)


def read_text_from_region(
    image: Image.Image,
    region: Optional[Tuple[int, int, int, int]] = None,
    config: Optional[str] = None,
) -> str:
    """
    Run OCR on the provided PIL image (optionally cropped to region).

    Parameters:
      image  - PIL Image
      region - optional (x, y, w, h) crop before OCR
      config - optional tesseract config string; if None, uses defaults
    """
    cfg = config or build_tesseract_config()
    img = image.crop((region[0], region[1], region[0] + region[2], region[1] + region[3])) if region else image
    try:
        return pytesseract.image_to_string(img, config=cfg)
    except Exception:
        # Keep failures non-fatal; callers can decide how to handle empty strings.
        return ""


# TODO: add specific helpers (read_pot, read_stack, read_bet_size) once UI text is known.
