from __future__ import annotations

import gzip
import json
from pathlib import Path

from murder_plan import Solver, State, position
from murder_plan.rules import _next_states, _turn_data
from murder_plan.solver import _reachable_layers

# This offline builder intentionally follows murder_plan internals so the
# generated table always uses the exact rules implemented by the solver.

DAY = 8
INITIAL_STATE = State(x=position(0, 1), y=position(1, 0))
OUTPUT = Path(__file__).parent / "data" / "d8_x01_y10.json.gz"


def main() -> None:
    solver = Solver()
    solver.solve(INITIAL_STATE, DAY)
    layers = _reachable_layers((INITIAL_STATE,), DAY)
    results = []
    post_card_states: set[tuple[State, int]] = set()

    for layer_index, states in enumerate(layers):
        day = DAY - layer_index
        for state in sorted(states):
            result = solver.solve(state, day)
            strategy = [[item.probability, *item.action] for item in result.strategy]
            results.append([day, *state, result.win_rate, strategy])

            for effect in _turn_data(state).effects:
                post_card_states.add((_next_states(state, effect)[0], day))

    abilities = [
        [day, *state, solver.choose_ability(state, day)]
        for state, day in sorted(post_card_states, key=lambda item: (item[1], item[0]))
    ]
    payload = {
        "format": 2,
        "initial": [DAY, *INITIAL_STATE],
        "results": results,
        "abilities": abilities,
    }
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(gzip.compress(encoded, compresslevel=9, mtime=0))

    print(f"strategy states: {len(results)}")
    print(f"ability states: {len(abilities)}")
    print(f"uncompressed: {len(encoded)} bytes")
    print(f"compressed: {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
