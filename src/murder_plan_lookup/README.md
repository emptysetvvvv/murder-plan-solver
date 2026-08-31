# Fixed Game Lookup

This package provides direct lookup for one fixed *Murder Plan* game:

- 8 remaining days;
- Brain position `x = (0, 1)`;
- Killer position `y = (1, 0)`;
- zero initial intrigue;
- all limited cards available.

`murder_plan_lookup` is a strategy oracle. It only reads a precomputed JSON
table and returns stored decisions. It does not resolve cards, movement,
blocking, intrigue, or limited-card consumption. The caller must calculate the
current state before each query.

The runtime package does not import or call `murder_plan.Solver`, NumPy, or
SciPy.

## Start a game

```python
from murder_plan_lookup import INITIAL_DAY, INITIAL_STATE

state = INITIAL_STATE
day = INITIAL_DAY
```

The package loads the table once when it is imported.

## Select Alice's cards

```python
from murder_plan_lookup import choose_action

action = choose_action(state, day)
```

`action` contains one explicit card for the Key Person (`P`), Brain (`B`), and
Killer (`K`). The action is sampled from the stored optimal mixed strategy.

Example return value:

```python
{
    "P": "intrigue+1",
    "B": "vertical",
    "K": "horizontal",
}
```

## Resolve the cards

The caller waits for Bob's cards, resolves movement and intrigue, and creates
the state immediately before the Brain's ability:

```python
from murder_plan_lookup import State, position

post_card_state = State(
    x=position(0, 0),
    y=position(1, 0),
    c=0,
    h=0,
    diagonal=True,
    intrigue_2=True,
    forbid_moves=2,
)
```

`position(x, y)` is a position relative to the Key Person on the 2x2 map. Both
coordinates must be `0` or `1`; they are not absolute board coordinates.
`position(0, 0)` means the same location as the Key Person.

This state must include all movement, card-based intrigue, and limited-card
consumption from the current day. Limited cards are consumed even when their
effects are blocked.

## Select the Brain target

```python
from murder_plan_lookup import choose_ability

target = choose_ability(post_card_state, day)
```

Brain targets are stored directly in the table; no game-tree calculation occurs
here. Possible return values are:

```python
"K"   # Killer
"P"   # Key Person
None  # Brain or no further action; JSON equivalent: null
```

The caller applies the target, checks whether the game has ended, and supplies
the resulting state in the next query if play continues.

## Inspect the complete strategy

```python
from murder_plan_lookup import get_strategy

result = get_strategy(state, day)
```

`result["win_rate"]` is Alice's optimal win probability. `result["strategy"]`
contains the complete stored probability distribution as ordinary dictionaries.

Example return value:

```python
{
    "win_rate": 0.773694134114302,
    "strategy": [
        {
            "probability": 0.21,
            "cards": {
                "P": "intrigue+1",
                "B": "vertical",
                "K": "horizontal",
            },
        },
    ],
}
```

## Input boundary

The table accepts states reachable from the fixed initial game. A state outside
that game tree raises `ValueError`.

## Build the data

The committed data file is ready to use. Maintainers can regenerate it after a
rule or solver change:

```bash
python -m murder_plan_lookup.build_table
```

Table generation uses the exact solver offline. Normal lookup never imports
the solver package.

## Performance

One cold-process measurement in the development environment produced:

| Step | Time |
| --- | ---: |
| Import and load `murder_plan_lookup` | 0.166 s |
| First strategy and Brain queries | 0.000031 s |

Times depend on the machine and filesystem cache. The compressed JSON file is
about 1.23 MB and contains 17,639 start-of-day strategies and 26,678 post-card
Brain targets.
