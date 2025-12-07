"""Master controller for the poker bot.

High-level flow:
  - capture current table state (cards, stacks, action)
  - lookup or compute GTO recommendation
  - execute action with automation layer
"""
from typing import Dict, Any

from vision import capture
from solver import lookup, decision
from automation import browser_control


VALID_ACTIONS = {"fold", "call", "raise"}


def _safe_get_table_state() -> Dict[str, Any]:
    state = capture.get_table_state()
    if not isinstance(state, dict):
        raise TypeError(f"capture.get_table_state must return a dict, got {type(state)!r}")
    return state


def _safe_pick_action(table_state: Dict[str, Any]) -> str:
    solution = lookup.find_solution(table_state)
    action = decision.pick_action(solution, table_state)
    if action not in VALID_ACTIONS:
        return "call"
    return action


def run_once() -> None:
    table_state = _safe_get_table_state()

    hero = table_state.get("hero_cards") or []
    board = table_state.get("board") or []
    if not hero or not board:
        return

    action = _safe_pick_action(table_state)
    browser_control.execute_action(action)


def run_loop(interval_seconds: float = 1.0) -> None:
    import time

    while True:
        run_once()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_once()
