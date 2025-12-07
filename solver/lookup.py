"""Load presolved GTO tables and query them for a given table state."""
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "lookups"


def find_solution(table_state: dict) -> dict:
    """Find the closest precomputed solution for the supplied table state.

    Returns a dict representing strategy (probabilities for fold/call/raise,
    or a discrete action). This is a stub that returns a deterministic
    recommendation for development.
    """
    # TODO: implement nearest-key lookup by hero hand and board texture
    return {"action_probs": {"fold": 0.0, "call": 1.0, "raise": 0.0}}


def load_lookup_file(name: str) -> dict:
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
