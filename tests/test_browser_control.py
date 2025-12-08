import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from automation import browser_control


class DummyLocator:
    def __init__(self, should_raise: bool = False):
        self.clicked = False
        self.should_raise = should_raise

    def click(self, timeout: int = 2000):
        if self.should_raise:
            raise Exception("text click failed")
        self.clicked = True


class BrowserControlTests(unittest.TestCase):
    def test_click_prefers_id_selector(self):
        page = Mock()
        page.click.return_value = None  # id click succeeds

        browser_control.click_action_playwright(page, "fold")

        page.click.assert_called_once_with("#fold", timeout=2000)
        page.get_by_text.assert_not_called()

    def test_falls_back_to_text_locator(self):
        page = Mock()
        page.click.side_effect = Exception("id not found")
        locator = DummyLocator()
        page.get_by_text.return_value = locator

        browser_control.click_action_playwright(page, "call")

        page.click.assert_called_once_with("#call", timeout=2000)
        page.get_by_text.assert_called_once_with("Call", exact=True)
        self.assertTrue(locator.clicked)

    def test_invalid_action_raises_value_error(self):
        page = Mock()
        with self.assertRaises(ValueError):
            browser_control.click_action_playwright(page, "check")  # type: ignore[arg-type]

    def test_raises_when_nothing_found(self):
        page = Mock()
        page.click.side_effect = Exception("id not found")
        page.get_by_text.return_value = DummyLocator(should_raise=True)

        with self.assertRaises(RuntimeError):
            browser_control.click_action_playwright(page, "fold")


if __name__ == "__main__":
    unittest.main()
