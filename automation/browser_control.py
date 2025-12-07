"""
automation/browser_control.py

Responsible for:
  - Executing actions in the browser using Playwright
  - Mapping abstract actions ("fold", "call", "raise") to DOM clicks

This module intentionally does not know anything about computer vision
or solvers. It just knows how to click the correct UI elements once
an action has been chosen.

For the simulator:
  - The HTML uses button ids: #fold, #call, #raise
    so we target those by default. :contentReference[oaicite:1]{index=1}

For your friend's app:
  - You will likely need to update the CSS selectors or text locators
    in click_action_playwright once you know how that app marks up
    its action buttons.
"""

from typing import Literal

# Keep this alias aligned with main.Action for clarity.
Action = Literal["fold", "call", "raise"]


def click_action_playwright(page, action: Action) -> None:
    """
    Click the appropriate action button in the browser using Playwright.

    Parameters:
      page   - Playwright page object
      action - one of "fold", "call", "raise"

    Strategy:
      1. Try to click by id (for the simulator).
      2. If that fails, fall back to a text-based locator.
      3. If everything fails, raise a RuntimeError so it is obvious.

    TODO:
      When targeting a real app, update the selectors below to use
      that app's actual markup (ids, classes, data attributes, etc.).
    """
    action_lower = action.lower()

    if action_lower not in {"fold", "call", "raise"}:
        raise ValueError(f"Unknown action: {action}")

    # Helper to try a CSS selector, then a text locator.
    def try_click_by_id_or_text(button_id: str, button_text: str) -> bool:
        # First try id selector
        try:
            page.click(f"#{button_id}", timeout=2000)
            return True
        except Exception:
            pass

        # Then try text locator
        try:
            page.get_by_text(button_text, exact=True).click(timeout=2000)
            return True
        except Exception:
            return False

    if action_lower == "fold":
        if try_click_by_id_or_text("fold", "Fold"):
            return
    elif action_lower == "call":
        if try_click_by_id_or_text("call", "Call"):
            return
    elif action_lower == "raise":
        if try_click_by_id_or_text("raise", "Raise"):
            return

    # If we reach this point, we could not find the button.
    raise RuntimeError(f"Could not locate UI element for action '{action_lower}'")
