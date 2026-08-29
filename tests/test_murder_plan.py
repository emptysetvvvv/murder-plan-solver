import random
import unittest

import numpy as np

from murder_plan import HORIZONTAL, VERTICAL, Action, Result, Solver, State, Strategy
from murder_plan.model import (
    A_BLANK,
    A_DIAGONAL,
    A_HORIZONTAL,
    A_INTRIGUE_2,
    A_VERTICAL,
    B_BLANK,
    B_FORBID_INTRIGUE,
    B_FORBID_MOVE,
    B_HORIZONTAL,
    B_VERTICAL,
)
from murder_plan.rules import (
    _alice_actions,
    _bob_actions,
    _effect,
    _next_states,
)
from murder_plan.solver import _matrix_game


class RuleTests(unittest.TestCase):
    def test_default_state(self):
        self.assertEqual(State(), State(0, 0, 0, 0, True, True, 3))

    def test_card_counts(self):
        alice = _alice_actions(True, True)
        bob = _bob_actions(2)
        self.assertIn(Action(A_BLANK, A_BLANK, A_BLANK), alice)
        self.assertTrue(all(action.count(A_HORIZONTAL) <= 1 for action in alice))
        self.assertTrue(all(action.count(A_DIAGONAL) <= 1 for action in alice))
        self.assertTrue(all(action.count(A_INTRIGUE_2) <= 1 for action in alice))
        self.assertTrue(all(action.count(B_FORBID_MOVE) <= 2 for action in bob))
        self.assertTrue(all(action.count(B_FORBID_INTRIGUE) <= 1 for action in bob))
        self.assertIn(Action(B_HORIZONTAL, B_HORIZONTAL, B_HORIZONTAL), bob)

    def test_movement_updates_relative_positions(self):
        state = State(x=HORIZONTAL, y=VERTICAL)
        alice = Action(A_HORIZONTAL, A_VERTICAL, A_BLANK)
        bob = Action(B_VERTICAL, B_BLANK, B_BLANK)
        effect = _effect(alice, bob, True, True, 3)
        next_state = _next_states(state, effect)[0]
        self.assertEqual(next_state.x, 0)
        self.assertEqual(next_state.y, HORIZONTAL)

    def test_forbid_move_and_intrigue(self):
        state = State(x=HORIZONTAL, y=HORIZONTAL)
        alice = Action(A_HORIZONTAL, A_BLANK, A_INTRIGUE_2)
        bob = Action(B_FORBID_MOVE, B_BLANK, B_FORBID_INTRIGUE)
        effect = _effect(alice, bob, True, True, 3)
        candidates = _next_states(state, effect)
        self.assertTrue(all(candidate.x == HORIZONTAL for candidate in candidates))
        self.assertEqual({candidate.c for candidate in candidates}, {0, 1})
        self.assertTrue(all(candidate.forbid_moves == 2 for candidate in candidates))
        self.assertTrue(all(not candidate.intrigue_2 for candidate in candidates))

    def test_finished_tracks_do_not_duplicate_states(self):
        alice = Action(A_BLANK, A_BLANK, A_BLANK)
        bob = Action(B_BLANK, B_BLANK, B_BLANK)
        effect = _effect(alice, bob, True, True, 3)
        state = State(c=4, h=2)
        self.assertEqual(_next_states(state, effect), (state,))


class SolverTests(unittest.TestCase):
    def test_matrix_game(self):
        value, strategy = _matrix_game(np.array([[1.0, 0.0], [0.0, 1.0]]))
        self.assertAlmostEqual(value, 0.5)
        np.testing.assert_allclose(strategy, [0.5, 0.5], atol=1e-9)

    def test_pick_uses_probability_intervals(self):
        first = Action(A_BLANK, A_BLANK, A_BLANK)
        second = Action(A_HORIZONTAL, A_VERTICAL, A_BLANK)
        result = Result(
            State(),
            1,
            0.5,
            (Strategy(0.2, first), Strategy(0.8, second)),
        )
        self.assertEqual(result.pick(0.19), first)
        self.assertEqual(result.pick(0.20), second)
        self.assertEqual(
            result.pick(random.Random(123).random()),
            result.pick(random.Random(123).random()),
        )

    def test_terminal_states(self):
        solver = Solver()
        self.assertEqual(solver.solve(State(), day=0).win_rate, 0.0)
        won = solver.solve(State(c=4), day=3)
        self.assertEqual(won.win_rate, 1.0)
        self.assertEqual(won.strategy, ())

    def test_average_interface(self):
        self.assertEqual(Solver().average_win_rates((0, 1)), {0: 0.0, 1: 0.0})

    def test_horizontal_vertical_symmetry(self):
        horizontal = State(x=HORIZONTAL, y=VERTICAL, c=3, h=1)
        vertical = State(x=VERTICAL, y=HORIZONTAL, c=3, h=1)
        left = Solver().solve(horizontal, day=1).win_rate
        right = Solver().solve(vertical, day=1).win_rate
        self.assertAlmostEqual(left, right, places=12)

    def test_solver_cache(self):
        solver = Solver()
        first = solver.solve(State(), day=2)
        info = solver.cache_info()
        self.assertGreater(info["values"], 0)
        self.assertGreater(info["matrix_games"], 0)
        self.assertLess(info["matrix_games"], info["values"])
        self.assertIs(solver.solve(State(), day=2), first)

        solver.clear_cache()
        self.assertEqual(
            solver.cache_info(),
            {"values": 0, "results": 0, "average_rates": 1, "matrix_games": 0},
        )

    def test_three_day_regression(self):
        result = Solver().solve(State(), day=3)
        self.assertAlmostEqual(result.win_rate, 0.134346591935461, places=12)
        self.assertAlmostEqual(
            sum(item.probability for item in result.strategy),
            1.0,
            places=12,
        )


if __name__ == "__main__":
    unittest.main()
