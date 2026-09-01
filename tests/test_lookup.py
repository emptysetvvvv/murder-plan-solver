import subprocess
import sys
import unittest

from murder_plan_lookup import (
    INITIAL_DAY,
    INITIAL_STATE,
    State,
    choose_ability,
    choose_action,
    get_strategy,
)


class LookupTests(unittest.TestCase):
    def test_strategy_and_action(self):
        result = get_strategy(INITIAL_STATE, INITIAL_DAY)
        self.assertAlmostEqual(result["win_rate"], 0.773694134114302, places=12)
        self.assertAlmostEqual(
            sum(item["probability"] for item in result["strategy"]),
            1.0,
            places=12,
        )
        self.assertIn(
            choose_action(INITIAL_STATE, INITIAL_DAY),
            [item["cards"] for item in result["strategy"]],
        )

    def test_ability(self):
        self.assertIsNone(choose_ability(INITIAL_STATE, INITIAL_DAY))
        self.assertEqual(choose_ability(State(x=0, y=1, forbid_moves=2), 8), "P")
        self.assertEqual(choose_ability(State(x=3, y=3), 8), "K")

    def test_unreachable_state(self):
        with self.assertRaises(ValueError):
            get_strategy(State(c=3), 8)
        with self.assertRaises(ValueError):
            choose_ability(State(c=3), 8)

    def test_intrigue_is_capped(self):
        state = State(x=2, y=2, c=3, h=2, intrigue_2=False, forbid_moves=2)
        self.assertEqual(get_strategy(state._replace(h=3), 6), get_strategy(state, 6))

    def test_lookup_does_not_import_solver(self):
        code = (
            "import sys; import murder_plan_lookup; "
            "print('murder_plan' in sys.modules)"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
