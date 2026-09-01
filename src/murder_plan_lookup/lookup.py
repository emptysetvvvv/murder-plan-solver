from __future__ import annotations

import gzip
import json
import random
from importlib import resources
from typing import NamedTuple


CARDS = (
    "blank",
    "horizontal",
    "vertical",
    "diagonal",
    "intrigue+1",
    "intrigue+2",
)


def position(x: int, y: int) -> int:
    if x not in (0, 1) or y not in (0, 1):
        raise ValueError("position coordinates must be 0 or 1")
    return x | (y << 1)


class State(NamedTuple):
    x: int = 0
    y: int = 0
    c: int = 0
    h: int = 0
    diagonal: bool = True
    intrigue_2: bool = True
    forbid_moves: int = 3


def _cards(action: list[int]) -> dict[str, str]:
    return {"P": CARDS[action[0]], "B": CARDS[action[1]], "K": CARDS[action[2]]}


def _lookup_key(state: State, day: int) -> tuple[State, int]:
    return state._replace(c=min(state.c, 4), h=min(state.h, 2)), day


data_file = resources.files("murder_plan_lookup").joinpath(
    "data/d8_x01_y10.json.gz"
)
data = json.loads(gzip.decompress(data_file.read_bytes()))
if data.get("format") != 2:
    raise ValueError("unsupported lookup table format")

INITIAL_DAY = data["initial"][0]
INITIAL_STATE = State(*data["initial"][1:])
_STRATEGIES = {
    (State(*row[1:8]), row[0]): (row[8], row[9])
    for row in data["results"]
}
_ABILITIES = {
    (State(*row[1:8]), row[0]): row[8]
    for row in data["abilities"]
}
del data


def _find_strategy(state: State, day: int) -> tuple[float, list]:
    try:
        return _STRATEGIES[_lookup_key(state, day)]
    except KeyError as exc:
        raise ValueError("state is outside the fixed lookup table") from exc


def get_strategy(
    state: State,
    day: int,
) -> dict[str, object]:
    win_rate, strategy = _find_strategy(state, day)
    return {
        "win_rate": win_rate,
        "strategy": [
            {"probability": probability, "cards": _cards(action)}
            for probability, *action in strategy
        ],
    }


def choose_action(
    state: State,
    day: int,
) -> dict[str, str]:
    _, strategy = _find_strategy(state, day)
    choice = random.choices(strategy, weights=[item[0] for item in strategy])[0]
    return _cards(choice[1:])


def choose_ability(post_card_state: State, day: int) -> str | None:
    try:
        return _ABILITIES[_lookup_key(post_card_state, day)]
    except KeyError as exc:
        raise ValueError("post-card state is outside the fixed lookup table") from exc
