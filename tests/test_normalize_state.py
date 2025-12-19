import unittest

from main import normalize_state


class NormalizeStateTests(unittest.TestCase):
    def test_defaults_and_preflop_street(self):
        state = normalize_state({})
        self.assertEqual(state.board, [])
        self.assertEqual(state.hero_cards, [])
        self.assertEqual(state.street, "preflop")
        self.assertIsNone(state.pot)
        self.assertIsNone(state.stack)
        self.assertIsNone(state.bet_to_call)

    def test_street_derivation(self):
        for board, expected in [
            ([], "preflop"),
            (["As", "Kd", "Qh"], "flop"),
            (["As", "Kd", "Qh", "2c"], "turn"),
            (["As", "Kd", "Qh", "2c", "3d"], "river"),
        ]:
            state = normalize_state({"board": board})
            self.assertEqual(state.street, expected)


if __name__ == "__main__":
    unittest.main()
