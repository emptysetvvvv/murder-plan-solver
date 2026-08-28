from collections.abc import Iterable

import numpy as np
from scipy.optimize import linprog

from .model import Action, Result, State, Strategy
from .rules import _next_states, _turn_data, _validate_state, _winning


class Solver:
    def __init__(self, tolerance: float = 1e-9) -> None:
        self.tolerance = tolerance

    def solve(self, state: State | None = None, day: int = 7) -> Result:
        state = State() if state is None else state
        _validate_state(state)
        if day < 0:
            raise ValueError("day must be zero or greater")
        if _winning(state) or day == 0:
            return Result(state, day, float(_winning(state)), ())

        layers = _reachable_layers((state,), day)
        next_values: dict[State, float] | None = None
        first_value = 0.0
        first_strategy: tuple[Strategy, ...] = ()

        for layer_index in range(day - 1, -1, -1):
            values: dict[State, float] = {}
            for current in sorted(layers[layer_index]):
                matrix = _payoff_matrix(current, next_values)
                value, probabilities = _matrix_game(matrix)
                values[current] = value
                if layer_index == 0:
                    first_value = value
                    first_strategy = _strategy(
                        probabilities,
                        _turn_data(current).alice_actions,
                        self.tolerance,
                    )
            next_values = values

        return Result(state, day, first_value, first_strategy)

    def average_win_rate(self, day: int = 7) -> float:
        return self.average_win_rates((day,))[day]

    def average_win_rates(self, days: Iterable[int]) -> dict[int, float]:
        requested = sorted(set(days))
        if (
            not requested
            or any(not isinstance(day, int) for day in requested)
            or requested[0] < 0
        ):
            raise ValueError("days must contain non-negative integers")

        rates = {0: 0.0} if 0 in requested else {}
        max_day = requested[-1]
        if max_day == 0:
            return rates

        initial = tuple(State(x=x, y=y) for x in range(4) for y in range(4))
        layers = _reachable_layers(initial, max_day)
        next_values: dict[State, float] | None = None

        for layer_index in range(max_day - 1, -1, -1):
            values: dict[State, float] = {}
            for state in sorted(layers[layer_index]):
                matrix = _payoff_matrix(state, next_values)
                values[state] = _matrix_game(matrix)[0]
            day = max_day - layer_index
            if day in requested:
                rates[day] = sum(values[state] for state in initial) / len(initial)
            next_values = values

        return {day: rates[day] for day in requested}


def _reachable_layers(initial: tuple[State, ...], day: int) -> list[set[State]]:
    layers = [set(initial)]
    for _ in range(1, day):
        next_layer: set[State] = set()
        for state in layers[-1]:
            for effect in _turn_data(state).effects:
                next_layer.update(
                    candidate
                    for candidate in _next_states(state, effect)
                    if not _winning(candidate)
                )
        layers.append(next_layer)
    return layers


def _payoff_matrix(
    state: State,
    next_values: dict[State, float] | None,
) -> np.ndarray:
    data = _turn_data(state)
    values = np.empty(len(data.effects), dtype=float)
    for index, effect in enumerate(data.effects):
        best = 0.0
        for candidate in _next_states(state, effect):
            if _winning(candidate):
                best = 1.0
                break
            if next_values is not None:
                best = max(best, next_values[candidate])
        values[index] = best
    return values[data.effect_ids].reshape(
        len(data.alice_actions),
        len(data.bob_actions),
    )


def _matrix_game(matrix: np.ndarray) -> tuple[float, np.ndarray]:
    rows, columns = matrix.shape
    objective = np.zeros(rows + 1)
    objective[-1] = -1.0
    inequalities = np.hstack((-matrix.T, np.ones((columns, 1))))
    equality = np.zeros((1, rows + 1))
    equality[0, :rows] = 1.0
    result = linprog(
        objective,
        A_ub=inequalities,
        b_ub=np.zeros(columns),
        A_eq=equality,
        b_eq=np.ones(1),
        bounds=[(0.0, 1.0)] * rows + [(0.0, 1.0)],
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    probabilities = np.maximum(result.x[:rows], 0.0)
    probabilities /= probabilities.sum()
    value = float(np.clip(result.x[-1], 0.0, 1.0))
    return (0.0 if value < 1e-12 else value), probabilities


def _strategy(
    probabilities: np.ndarray,
    actions: tuple[Action, ...],
    tolerance: float,
) -> tuple[Strategy, ...]:
    support = [
        (float(probability), action)
        for probability, action in zip(probabilities, actions)
        if probability > tolerance
    ]
    total = sum(probability for probability, _ in support)
    return tuple(
        Strategy(probability / total, action)
        for probability, action in sorted(
            support,
            key=lambda item: (-item[0], item[1]),
        )
    )
