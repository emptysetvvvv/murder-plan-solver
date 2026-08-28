from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import NamedTuple

import numpy as np

from .model import (
    A_BLANK,
    A_DIAGONAL,
    A_HORIZONTAL,
    A_INTRIGUE_1,
    A_INTRIGUE_2,
    A_VERTICAL,
    B_BLANK,
    B_FORBID_INTRIGUE,
    B_FORBID_MOVE,
    B_HORIZONTAL,
    B_VERTICAL,
    DIAGONAL,
    HORIZONTAL,
    ORIGIN,
    VERTICAL,
    Action,
    State,
)


_ALICE_MOVES = (ORIGIN, HORIZONTAL, VERTICAL, DIAGONAL, ORIGIN, ORIGIN)
_BOB_MOVES = (ORIGIN, HORIZONTAL, VERTICAL, ORIGIN, ORIGIN)
_INTRIGUE = (0, 0, 0, 0, 1, 2)


class _Effect(NamedTuple):
    dx: int
    dy: int
    dc: int
    dh: int
    diagonal: bool
    intrigue_2: bool
    forbid_moves: int


@dataclass(frozen=True)
class _TurnData:
    alice_actions: tuple[Action, ...]
    bob_actions: tuple[Action, ...]
    effects: tuple[_Effect, ...]
    effect_ids: np.ndarray


def _winning(state: State) -> bool:
    return state.c == 4 or (state.y == ORIGIN and state.h == 2)


def _validate_state(state: State) -> None:
    if state.x not in range(4) or state.y not in range(4):
        raise ValueError("x and y must be positions from 0 to 3")
    if state.c not in range(5):
        raise ValueError("c must be between 0 and 4")
    if state.h not in range(3):
        raise ValueError("h must be between 0 and 2")
    if state.forbid_moves not in range(4):
        raise ValueError("forbid_moves must be between 0 and 3")
    if not isinstance(state.diagonal, bool) or not isinstance(state.intrigue_2, bool):
        raise ValueError("diagonal and intrigue_2 must be booleans")


@lru_cache(maxsize=None)
def _alice_actions(diagonal: bool, intrigue_2: bool) -> tuple[Action, ...]:
    counts = {A_BLANK: 3, A_HORIZONTAL: 1, A_VERTICAL: 1, A_INTRIGUE_1: 1}
    if diagonal:
        counts[A_DIAGONAL] = 1
    if intrigue_2:
        counts[A_INTRIGUE_2] = 1
    return _actions(counts)


@lru_cache(maxsize=None)
def _bob_actions(forbid_moves: int) -> tuple[Action, ...]:
    counts = {B_BLANK: 3, B_HORIZONTAL: 3, B_VERTICAL: 3, B_FORBID_INTRIGUE: 1}
    if forbid_moves:
        counts[B_FORBID_MOVE] = forbid_moves
    return _actions(counts)


def _actions(counts: dict[int, int]) -> tuple[Action, ...]:
    result = []
    for cards in product(sorted(counts), repeat=3):
        used = Counter(cards)
        if all(used[card] <= counts[card] for card in used):
            result.append(Action(*cards))
    return tuple(result)


def _move(alice_card: int, bob_card: int) -> int:
    if bob_card == B_FORBID_MOVE:
        return ORIGIN
    alice = _ALICE_MOVES[alice_card]
    bob = _BOB_MOVES[bob_card]
    return alice if alice == bob else alice ^ bob


def _effect(
    alice: Action,
    bob: Action,
    diagonal: bool,
    intrigue_2: bool,
    forbid_moves: int,
) -> _Effect:
    p_move = _move(alice.p, bob.p)
    b_move = _move(alice.b, bob.b)
    k_move = _move(alice.k, bob.k)
    dc = _INTRIGUE[alice.k]
    dh = _INTRIGUE[alice.p]
    if bob.k == B_FORBID_INTRIGUE:
        dc = 0
    if bob.p == B_FORBID_INTRIGUE:
        dh = 0
    return _Effect(
        b_move ^ p_move,
        k_move ^ p_move,
        dc,
        dh,
        diagonal and A_DIAGONAL not in alice,
        intrigue_2 and A_INTRIGUE_2 not in alice,
        forbid_moves - bob.count(B_FORBID_MOVE),
    )


@lru_cache(maxsize=None)
def _turn_data_for_inventory(
    diagonal: bool,
    intrigue_2: bool,
    forbid_moves: int,
) -> _TurnData:
    alice_actions = _alice_actions(diagonal, intrigue_2)
    bob_actions = _bob_actions(forbid_moves)
    effects: list[_Effect] = []
    effect_ids: list[int] = []
    ids: dict[_Effect, int] = {}

    for alice in alice_actions:
        for bob in bob_actions:
            effect = _effect(alice, bob, diagonal, intrigue_2, forbid_moves)
            if effect not in ids:
                ids[effect] = len(effects)
                effects.append(effect)
            effect_ids.append(ids[effect])

    return _TurnData(
        alice_actions,
        bob_actions,
        tuple(effects),
        np.asarray(effect_ids, dtype=np.intp),
    )


def _turn_data(state: State) -> _TurnData:
    return _turn_data_for_inventory(
        state.diagonal,
        state.intrigue_2,
        state.forbid_moves,
    )


def _next_states(state: State, effect: _Effect) -> tuple[State, ...]:
    x = state.x ^ effect.dx
    y = state.y ^ effect.dy
    c = min(4, state.c + effect.dc)
    h = min(2, state.h + effect.dh)
    base = State(x, y, c, h, effect.diagonal, effect.intrigue_2, effect.forbid_moves)
    result = [base]
    if x == y and c < 4:
        result.append(State(x, y, c + 1, h, effect.diagonal, effect.intrigue_2, effect.forbid_moves))
    if x == ORIGIN and h < 2:
        result.append(State(x, y, c, h + 1, effect.diagonal, effect.intrigue_2, effect.forbid_moves))
    return tuple(result)
