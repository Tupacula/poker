import io
import unittest
from PIL import Image

from vision import capture


class DummyPage:
    def __init__(self, closed: bool = False, image: Image.Image = None, raise_on_shot: bool = False):
        self._closed = closed
        self._image = image or Image.new("RGB", (100, 50), color="red")
        self._raise = raise_on_shot

    def is_closed(self):
        return self._closed

    def screenshot(self, full_page: bool = True):
        if self._raise:
            raise RuntimeError("boom")
        buf = io.BytesIO()
        self._image.save(buf, format="PNG")
        return buf.getvalue()


class CaptureTests(unittest.TestCase):
    def test_screenshot_raises_when_page_closed(self):
        page = DummyPage(closed=True)
        with self.assertRaises(capture.CaptureError):
            capture.screenshot_page(page)

    def test_screenshot_raises_when_screenshot_fails(self):
        page = DummyPage(raise_on_shot=True)
        with self.assertRaises(capture.CaptureError):
            capture.screenshot_page(page)

    def test_screenshot_crops_region(self):
        img = Image.new("RGB", (200, 100), color="blue")
        page = DummyPage(image=img)
        region = (10, 20, 30, 40)
        cropped = capture.screenshot_page(page, region=region)
        self.assertEqual(cropped.size, (region[2], region[3]))


if __name__ == "__main__":
    unittest.main()
