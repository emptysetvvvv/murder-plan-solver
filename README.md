# Murder Plan Solver

An exact finite-horizon solver for the **Murder Plan** scenario in
*Tragedy Looper*. It uses backward induction and linear programming to compute
Alice's optimal win rate and mixed strategy against optimal play by Bob.

This is an unofficial fan-made project and is not affiliated with the
publisher or rights holders of *Tragedy Looper*.

Ready to test your skills? The AI mastermind from this solver 
is now live in the BTX-132: *Laplace’s Witch* script — 
come and challenge it at [tragic-aiplay.cn](https://tragic-aiplay.cn)

使用该策略的 AI 剧作家已实装，前往 [tragic-aiplay.cn](https://tragic-aiplay.cn) 的 BTX-132《拉普拉斯的魔女》挑战它吧！

## Quick Start

Create the Conda environment and install the package:

```bash
conda env create -f environment.yml
conda activate tragedy_looper
```

If the environment already exists, install the package in editable mode:

```bash
python -m pip install -e .
```

Solve one state from the command line:

```bash
murder-plan solve --day 8 --x 0,1 --y 1,0 --random 0.42
```

The command prints Alice's optimal win rate, the complete mixed strategy, and
one selected action.

The same workflow is available through Python:

```python
from murder_plan import Solver, State, position

solver = Solver()
state = State(x=position(0, 1), y=position(1, 0))
day = 8

result = solver.solve(state, day)          # Win rate and mixed strategy
action = solver.choose_action(state, day)  # One sampled action
```

The separate `murder_plan_lookup` package provides direct disk lookup for the
fixed eight-day game above. See its [integration guide](src/murder_plan_lookup/README.md).

## Model and State

The model contains a Key Person (`P`), Brain (`B`), and Killer (`K`) on a 2 x 2
map. Alice tries to complete the murder plan, while Bob tries to prevent it.
Alice wins when the Killer reaches four intrigue, or when the Killer meets the
Key Person after the Key Person reaches two intrigue.

`day` is the number of days remaining, including the current day.

| Field | Meaning | Values | Default |
| --- | --- | --- | --- |
| `x` | Brain position relative to the Key Person | `position(0 or 1, 0 or 1)` | `position(0, 0)` |
| `y` | Killer position relative to the Key Person | `position(0 or 1, 0 or 1)` | `position(0, 0)` |
| `c` | Killer intrigue | `0` to `4` | `0` |
| `h` | Key Person intrigue | `0` to `2` | `0` |
| `diagonal` | Alice still has the limited diagonal card | `bool` | `True` |
| `intrigue_2` | Alice still has the limited intrigue +2 card | `bool` | `True` |
| `forbid_moves` | Bob's remaining limited forbid-move cards | `0` to `3` | `3` |

Limited cards are consumed when played even if their effects are blocked. The
state passed to the solver must include this consumption.

## Python API

### Full strategy and win rate

```python
result = solver.solve(state, day)

print(result.win_rate)
for item in result.strategy:
    print(item.probability, item.action.to_dict())
```

`Result.strategy` contains every action in the support of Alice's optimal mixed
strategy. Each action assigns one card to `P`, `B`, and `K`. `result.to_dict()`
returns a JSON-serializable representation of the result.

### Select one card action

```python
action = solver.choose_action(state, day)
print(action.to_dict())
```

The method samples one concrete action from the optimal mixed strategy. Pass a
number in `[0, 1)` to make the selection reproducible:

```python
action = solver.choose_action(state, day, random_value=0.42)
```

### Select the Brain ability target

Call `choose_ability()` after both players' cards have resolved and before the
Brain adds intrigue:

```python
post_card_state = State(
    x=position(0, 0),
    y=position(0, 0),
    c=3,
    h=1,
    diagonal=False,
    intrigue_2=True,
    forbid_moves=2,
)

target = solver.choose_ability(post_card_state, day)
```

`post_card_state` must already include all movement, card-based intrigue, and
limited-card consumption from the current day. The return value is:

- `"K"`: add intrigue to the Killer
- `"P"`: add intrigue to the Key Person
- `None`: target the Brain, or take no further action because the game is over

When several targets have the same value, the priority is Killer, Key Person,
then Brain.

### Average initial win rates

```python
rates = solver.average_win_rates(range(3, 9))
```

This returns the mean Alice win rate over all 16 initial relative-position
pairs for each requested day.

### Cache reuse

The first solve may take time because the game tree is evaluated on demand.
Reuse one `Solver` instance throughout a game so later calls can use its
in-memory state and matrix caches:

```python
solver = Solver()
result = solver.solve(state, day)
next_action = solver.choose_action(next_state, day - 1)

print(solver.cache_info())
solver.clear_cache()
```

The solver cache is kept in memory only. Fixed-game lookup is provided by the
separate `murder_plan_lookup` package.

## Command Line

Solve a state and optionally save the complete result as JSON:

```bash
murder-plan solve \
  --day 8 \
  --x 0,1 \
  --y 1,0 \
  --random 0.42 \
  --json result.json
```

Compute average initial win rates:

```bash
murder-plan average --days 3-8 --json average.json
```

Use `murder-plan --help` or a subcommand with `--help` for all state and output
options.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

Released under the MIT License. See [LICENSE](LICENSE).
