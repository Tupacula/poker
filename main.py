"""
main.py

Orchestration loop for the poker bot.

High level pipeline:

    Screenshot -> Parse State -> Query Solver -> Execute Action

This file is intended to be as close as possible to the "final" structure.
Where functionality is not yet implemented (for example, real solver lookup),
it is clearly marked as a placeholder with TODO comments.

Dependencies:
  - Playwright for browser control
  - vision.capture for reading table state from screenshots
  - automation.browser_control for clicking Fold / Call / Raise in the DOM
"""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from playwright.sync_api import sync_playwright

from vision import capture
from automation import browser_control


# Type alias for the three basic actions we support
Action = Literal["fold", "call", "raise"]


@dataclass
class TableState:
    """
    Normalized representation of the table state.

    This wraps whatever raw dictionary comes back from vision.capture
    into a typed object that is easier to work with and extend.
    """

    hero_cards: List[str]
    board: List[str]
    pot: Optional[float]
    to_act: str
    stack: Optional[float]
    bet_to_call: Optional[float]
    raw: Dict  # raw vision output for debugging or future extensions


def normalize_state(raw_state: Dict) -> TableState:
    """
    Convert raw state dictionary from vision.capture into a TableState object.

    This function should remain very thin. If you add more fields to the
    capture output (for example, opponent stacks, bets, etc.) you can
    expose them here without changing the rest of the code.
    """
    return TableState(
        hero_cards=list(raw_state.get("hero_cards", [])),
        board=list(raw_state.get("board", [])),
        pot=raw_state.get("pot"),
        to_act=raw_state.get("to_act", "hero"),
        stack=raw_state.get("stack"),
        bet_to_call=raw_state.get("bet_to_call"),
        raw=raw_state,
    )


def choose_action_placeholder(state: TableState) -> Action:
    """
    Placeholder decision logic.

    TODO: Replace this with a real solver lookup when:
      - Card templates are in place
      - GTO lookup tables or a live solver integration exists

    For now, this function implements a trivial rule-based policy so
    that the rest of the pipeline can be exercised end to end:

      - If hero has any Ace, "raise"
      - Else if there is a flop (at least 3 board cards), "call"
      - Else "fold"

    This is intentionally simple and obviously non-GTO so it is easy
    to remember that it is a placeholder.
    """
    hero = [card.lower() for card in state.hero_cards]

    if any(card.startswith("a") for card in hero):
        return "raise"

    if len(state.board) >= 3:
        return "call"

    return "fold"


def decide_action(state: TableState) -> Action:
    """
    Entry point for the decision logic.

    Eventually, this should:
      1. Map the parsed state into the solver's abstraction
      2. Query a precomputed solution or live solver
      3. Sample or pick an action according to GTO frequencies

    For now, this function delegates to choose_action_placeholder,
    which is clearly marked as a stub. When you add real solver
    integration, you should replace the call below.
    """
    return choose_action_placeholder(state)


def run_single_decision_step(page) -> None:
    """
    Perform one full perception -> decision -> action loop.

    Steps:
      1. Capture screenshot from the Playwright page
      2. Let vision.capture parse cards and other state
      3. Normalize the raw state into a TableState
      4. Decide an action (currently using placeholder logic)
      5. Click the corresponding UI button via DOM
    """
    # 1. Capture table state from a Playwright screenshot
    raw_state = capture.capture_state_from_playwright(page)

    # 2. Normalize for downstream logic
    state = normalize_state(raw_state)

    # 3. Decide what to do
    action = decide_action(state)

    # 4. Execute the action in the browser via DOM clicks
    browser_control.click_action_playwright(page, action)


def main() -> None:
    """
    Top-level entry point for running the bot.

    This function is responsible for:
      - Spinning up a Playwright browser instance
      - Navigating to the poker table URL
      - Running the decision loop a fixed number of times (for now)

    Notes:
      - The loop count and delays are placeholders. Once you integrate
        with a real app, you will likely:
          * Trigger decisions only when it is your turn to act
          * Use event-based logic instead of a simple for-loop
    """
    TABLE_URL = "http://localhost:8000"  # TODO: replace with your real app URL
    DECISION_STEPS = 10                  # TODO: adjust or replace with hand-based logic
    STEP_DELAY_SECONDS = 1.0             # simple throttle between actions

    with sync_playwright() as p:
        # Launch a visible browser so you can see what is happening.
        # Set headless=True when you no longer need to observe it.
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to the poker table
        page.goto(TABLE_URL)

        # Optional: wait for the UI to finish loading.
        # For a real app, you might want to wait for specific selectors.
        page.wait_for_timeout(2000)

        # Simple fixed-length loop for now.
        # You can later change this to "while True" or per-hand triggers.
        import time

        for _ in range(DECISION_STEPS):
            run_single_decision_step(page)
            time.sleep(STEP_DELAY_SECONDS)

        browser.close()


if __name__ == "__main__":
    main()
