"""Optional interface to a live solver (e.g., PioSolver) for querying GTO.

This module is intentionally minimal. In a full implementation it would
manage a subprocess or TCP connection to a solver, translate table states to
solver input, and parse the solver's responses.
"""


def query_solver(table_state: dict) -> dict:
    """Query an external solver and return a normalized solution dict.

    For now this is a placeholder.
    """
    return {"action_probs": {"fold": 0.0, "call": 1.0, "raise": 0.0}}
