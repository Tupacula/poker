"""Decision logic that picks a discrete action from solver output.

For GTO-based play we often sample the discrete option according to
probabilities; here we return the highest-probability action.
"""
from typing import Dict


def pick_action(solution: Dict, table_state: Dict) -> str:
    """Pick a discrete action: 'fold', 'call' or 'raise'.

    `solution` is expected to contain an `action_probs` mapping.
    """
    probs = solution.get("action_probs", {})
    if not probs:
        return "call"
    # Choose the action with maximum probability (deterministic for now)
    return max(probs.items(), key=lambda kv: kv[1])[0]
