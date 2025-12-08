"""Decision logic that picks a discrete action from solver output."""
from typing import Dict, Literal

Action = Literal["fold", "call", "raise"]


def _normalize_probs(probs: Dict[str, float]) -> Dict[Action, float]:
    """Ensure keys/values are valid and sum to 1.0."""
    filtered = {k.lower(): float(v) for k, v in probs.items() if k.lower() in {"fold", "call", "raise"}}
    total = sum(v for v in filtered.values() if v > 0)
    if total <= 0:
        return {"fold": 0.0, "call": 1.0, "raise": 0.0}
    return {k: v / total for k, v in filtered.items()}  # type: ignore[return-value]


def choose_action(action_probs: Dict[str, float]) -> Action:
    """
    Convert a probability distribution into a single action.

    Deterministic: picks the action with max probability, breaking ties
    by preferring call > raise > fold (arbitrary but stable).
    """
    normalized = _normalize_probs(action_probs)
    priority = {"call": 2, "raise": 1, "fold": 0}
    return max(normalized.items(), key=lambda kv: (kv[1], priority[kv[0]]))[0]  # type: ignore[return-value]


def pick_action(solution: Dict, table_state: Dict) -> Action:
    """
    Backwards-compatible wrapper used by main.py.

    Expects solution to contain either:
      - "action_probs": mapping of action -> probability
      - or legacy fields (ignored for now)
    """
    probs = solution.get("action_probs") or solution
    return choose_action(probs)
