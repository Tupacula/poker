import unittest

from solver import lookup


class LookupTests(unittest.TestCase):
    def test_lookup_strategy_returns_all_actions(self):
        state = {"hero_cards": ["As", "Kd"], "board": ["2c", "7h", "Jh"]}
        probs = lookup.lookup_strategy(state)
        self.assertIn("fold", probs)
        self.assertIn("call", probs)
        self.assertIn("raise", probs)
        total = sum(probs.values())
        self.assertGreater(total, 0)


if __name__ == "__main__":
    unittest.main()
