# Murder Plan Solver

A finite-horizon zero-sum game solver for the **Murder Plan** scenario in
*Tragedy Looper*. It uses backward induction and linear programming to compute
Alice's optimal win rate and mixed strategy.

This is an unofficial fan-made project and is not affiliated with the
publisher or rights holders of *Tragedy Looper*.

## Installation

```bash
conda env create -f environment.yml
conda activate tragedy_looper
```

If the environment already exists:

```bash
python -m pip install -e .
```

## Python API

```python
from murder_plan import Solver, State, position

state = State(
    x=position(1, 0),  # Brain relative to the Key Person
    y=position(0, 1),  # Killer relative to the Key Person
    c=0,               # Killer intrigue
    h=0,               # Key Person intrigue
)

solver = Solver()
result = solver.solve(state, day=3)

print(result.win_rate)
print(result.strategy)
print(result.pick(0.42))
print(result.to_dict())
```

`day` is the number of remaining days. `State()` uses the default initial
state: both characters are at `(0, 0)`, both intrigue values are zero, and all
limited-use cards are available.

Call `result.pick()` for a random action, or pass a value in `[0, 1)` for a
reproducible selection. For a fixed seed:

```python
import random

rng = random.Random(123)
action = result.pick(rng.random())
```

Calculate average win rates over all 16 initial position pairs:

```python
rates = solver.average_win_rates(range(3, 9))
```

A `Solver` instance keeps an in-memory cache of previously computed
`(state, day)` values. Reuse the same instance for repeated or consecutive
queries. Call `solver.clear_cache()` to release it.

## Command Line

```bash
# Solve a state and select an action
murder-plan solve --day 3 --x 1,0 --y 0,1 --random 0.42

# Save a result as JSON
murder-plan solve --day 3 --seed 123 --json result.json

# Calculate average win rates
murder-plan average --days 3-8
murder-plan average --days 3-8 --json average.json
```

Run `murder-plan --help` or a subcommand with `--help` for all options.

## Tests

```bash
python -m unittest discover -s tests -v
```
