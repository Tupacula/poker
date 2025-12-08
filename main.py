"""
main.py

Orchestration loop for the poker bot.

Pipeline:
    Screenshot -> Parse State -> Query Solver -> Execute Action
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

from playwright.sync_api import sync_playwright

from vision import capture
from solver import lookup, decision
from automation import browser_control

# Type alias for the three basic actions we support
Action = Literal["fold", "call", "raise"]

# Simple configuration block
TABLE_URL = "http://localhost:8000"  # TODO: replace with your real app URL
LOOP_DELAY_SECONDS = 1.0             # throttle between actions
HEADLESS = False                     # set True when you do not need to observe
DECISION_STEPS = 10                  # adjust or replace with hand-based logic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pokerbot")


@dataclass
class TableState:
    """
    Normalized representation of the table state.
    """

    hero_cards: List[str]
    board: List[str]
    pot: Optional[float]
    to_act: str
    stack: Optional[float]
    bet_to_call: Optional[float]
    raw: Dict  # raw vision output for debugging or future extensions


def normalize_state(raw_state: Dict) -> TableState:
    """Convert raw state dictionary from vision.capture into a TableState object."""
    return TableState(
        hero_cards=list(raw_state.get("hero_cards", [])),
        board=list(raw_state.get("board", [])),
        pot=raw_state.get("pot"),
        to_act=raw_state.get("to_act", "hero"),
        stack=raw_state.get("stack"),
        bet_to_call=raw_state.get("bet_to_call"),
        raw=raw_state,
    )


def decide_action(state: TableState) -> Action:
    """
    Entry point for the decision logic.

    For now, uses solver.lookup.lookup_strategy (stub) and solver.decision.choose_action.
    """
    probs = lookup.lookup_strategy(state.__dict__)
    action = decision.choose_action(probs)
    return action


def run_single_decision_step(page, dry_run: bool = False) -> None:
    """
    Perform one full perception -> decision -> action loop.

    Steps:
      1. Capture screenshot from the Playwright page
      2. Let vision.capture parse cards and other state
      3. Normalize the raw state into a TableState
      4. Decide an action
      5. Click the corresponding UI button via DOM (skipped if dry_run)
    """
    raw_state = capture.capture_state_from_playwright(page)
    state = normalize_state(raw_state)
    action = decide_action(state)

    logger.info("State hero=%s board=%s pot=%s stack=%s bet_to_call=%s -> action=%s",
                state.hero_cards, state.board, state.pot, state.stack, state.bet_to_call, action)

    if dry_run:
        return

    browser_control.click_action_playwright(page, action)


def main() -> None:
    """
    Top-level entry point for running the bot.

    Robustness notes:
      - Exceptions within the loop are logged and skipped so a single failure
        does not crash the process.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        page.goto(TABLE_URL)
        page.wait_for_timeout(2000)

        for _ in range(DECISION_STEPS):
            try:
                run_single_decision_step(page)
            except Exception as exc:
                logger.exception("Decision step failed: %s", exc)
            time.sleep(LOOP_DELAY_SECONDS)

        browser.close()


if __name__ == "__main__":
    main()
