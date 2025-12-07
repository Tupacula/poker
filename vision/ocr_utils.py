"""OCR helpers for reading numeric and textual UI elements.

Wraps common Tesseract configuration and provides small helpers used by
`capture.py` and `card_reader.py`.
"""
import pytesseract
from PIL import Image


def image_to_text(image: Image.Image, lang: str = "eng") -> str:
    """Return OCR text for the provided PIL image using Tesseract."""
    # Users should ensure tesseract binary is installed on their system.
    return pytesseract.image_to_string(image, lang=lang)
