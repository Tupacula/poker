import unittest

from solver import decision


class DecisionTests(unittest.TestCase):
    def test_choose_action_prefers_highest_prob(self):
        action = decision.choose_action({"fold": 0.1, "call": 0.7, "raise": 0.2})
        self.assertEqual(action, "call")

    def test_choose_action_normalizes_and_defaults(self):
        action = decision.choose_action({"fold": -1, "call": -2})
        self.assertEqual(action, "call")  # defaults to call when invalid

    def test_choose_action_breaks_ties_stably(self):
        action = decision.choose_action({"fold": 0.5, "call": 0.5})
        self.assertEqual(action, "call")  # tie-break priority: call > raise > fold


if __name__ == "__main__":
    unittest.main()
