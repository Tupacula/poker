"""Lookup helpers for mapping a parsed table state to a solver strategy.

These functions are stubs until real lookup tables or solver integrations
are available. Interfaces are kept stable so downstream code will not need
to change when you plug in real data.
"""
import json
from pathlib import Path
from typing import Dict

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "lookups"


def load_lookup_file(name: str) -> Dict:
    """Load a JSON lookup table by name from data/lookups/<name>.json."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def lookup_strategy(table_state: Dict) -> Dict[str, float]:
    """
    Placeholder strategy lookup.

    Returns a deterministic probability distribution over actions:
      {"fold": p, "call": p, "raise": p}

    The distribution is seeded by simple features (board length, presence of Ace)
    so that tests can assert stable outputs before real solvers are wired in.
    """
    hero_cards = [c.lower() for c in table_state.get("hero_cards", [])]
    board = table_state.get("board", []) or []

    has_ace = any(c.startswith("a") for c in hero_cards)
    board_len = len(board)

    if has_ace:
        probs = {"fold": 0.1, "call": 0.2, "raise": 0.7}
    elif board_len >= 3:
        probs = {"fold": 0.25, "call": 0.6, "raise": 0.15}
    else:
        probs = {"fold": 0.4, "call": 0.5, "raise": 0.1}

    return probs


# TODO: replace lookup_strategy with real table lookup once lookups are available.
