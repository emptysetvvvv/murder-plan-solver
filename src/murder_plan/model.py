from __future__ import annotations

import random
from dataclasses import dataclass
from typing import NamedTuple


ORIGIN = 0
HORIZONTAL = 1
VERTICAL = 2
DIAGONAL = 3

A_BLANK = 0
A_HORIZONTAL = 1
A_VERTICAL = 2
A_DIAGONAL = 3
A_INTRIGUE_1 = 4
A_INTRIGUE_2 = 5

B_BLANK = 0
B_HORIZONTAL = 1
B_VERTICAL = 2
B_FORBID_MOVE = 3
B_FORBID_INTRIGUE = 4

ALICE_CARDS = {
    A_BLANK: "blank",
    A_HORIZONTAL: "horizontal",
    A_VERTICAL: "vertical",
    A_DIAGONAL: "diagonal",
    A_INTRIGUE_1: "intrigue+1",
    A_INTRIGUE_2: "intrigue+2",
}


def position(x: int, y: int) -> int:
    if x not in (0, 1) or y not in (0, 1):
        raise ValueError("position coordinates must be 0 or 1")
    return x | (y << 1)


def _position_tuple(value: int) -> tuple[int, int]:
    return value & 1, (value >> 1) & 1


class Action(NamedTuple):
    p: int
    b: int
    k: int

    def to_dict(self) -> dict[str, str]:
        return {
            "P": ALICE_CARDS[self.p],
            "B": ALICE_CARDS[self.b],
            "K": ALICE_CARDS[self.k],
        }


class State(NamedTuple):
    x: int = ORIGIN
    y: int = ORIGIN
    c: int = 0
    h: int = 0
    diagonal: bool = True
    intrigue_2: bool = True
    forbid_moves: int = 3

    def to_dict(self) -> dict[str, object]:
        return {
            "x": list(_position_tuple(self.x)),
            "y": list(_position_tuple(self.y)),
            "c": self.c,
            "h": self.h,
            "diagonal": self.diagonal,
            "intrigue_2": self.intrigue_2,
            "forbid_moves": self.forbid_moves,
        }


@dataclass(frozen=True)
class Strategy:
    probability: float
    action: Action

    def to_dict(self) -> dict[str, object]:
        return {
            "probability": self.probability,
            "cards": self.action.to_dict(),
        }


@dataclass(frozen=True)
class Result:
    state: State
    day: int
    win_rate: float
    strategy: tuple[Strategy, ...]

    def pick(self, random_value: float | None = None) -> Action:
        if not self.strategy:
            raise ValueError("there is no action when the game is already over")
        value = random.random() if random_value is None else random_value
        if not 0 <= value < 1:
            raise ValueError("random_value must be in [0, 1)")

        total = 0.0
        for item in self.strategy:
            total += item.probability
            if value < total:
                return item.action
        return self.strategy[-1].action

    def to_dict(self) -> dict[str, object]:
        return {
            "day": self.day,
            "state": self.state.to_dict(),
            "win_rate": self.win_rate,
            "strategy": [item.to_dict() for item in self.strategy],
        }
