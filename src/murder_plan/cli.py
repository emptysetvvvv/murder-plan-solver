from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from .model import Result, State, position
from .solver import Solver


def _position(text: str) -> int:
    try:
        x, y = (int(value) for value in text.split(","))
        return position(x, y)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("position must look like 0,0 or 1,0") from exc


def _days(text: str) -> tuple[int, ...]:
    try:
        if "-" in text:
            start, end = (int(value) for value in text.split("-", 1))
            if start > end:
                raise ValueError
            return tuple(range(start, end + 1))
        return tuple(int(value) for value in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("days must look like 3-8 or 3,5,7") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Solve the Murder Plan game")
    commands = parser.add_subparsers(dest="command", required=True)

    solve = commands.add_parser("solve", help="solve one state")
    solve.add_argument("--day", type=int, default=7, help="remaining days (default: 7)")
    solve.add_argument("--x", type=_position, default=0, help="Brain position, e.g. 1,0")
    solve.add_argument("--y", type=_position, default=0, help="Killer position, e.g. 0,1")
    solve.add_argument("--c", type=int, default=0, help="Killer intrigue")
    solve.add_argument("--h", type=int, default=0, help="Key Person intrigue")
    solve.add_argument(
        "--diagonal",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="whether Alice still has diagonal movement",
    )
    solve.add_argument(
        "--intrigue-2",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="whether Alice still has intrigue+2",
    )
    solve.add_argument("--forbid-moves", type=int, default=3)
    solve.add_argument("--random", dest="random_value", type=float)
    solve.add_argument("--seed", type=int)
    solve.add_argument("--json", type=Path, dest="json_path")

    average = commands.add_parser("average", help="average over 16 random positions")
    average.add_argument("--days", type=_days, default=_days("3-8"))
    average.add_argument("--json", type=Path, dest="json_path")
    return parser


def _write_json(path: Path | None, data: dict[str, object]) -> None:
    if path:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _print_result(result: Result, random_value: float | None) -> None:
    print(f"Alice win rate: {result.win_rate:.6%}\n")
    if not result.strategy:
        print("No action: the game is already over or no days remain.")
        return

    print(f"{'Probability':>11}  {'P':<16} {'B':<16} {'K':<16}")
    for item in result.strategy:
        cards = item.action.to_dict()
        print(
            f"{item.probability:>10.4%}  "
            f"{cards['P']:<16} {cards['B']:<16} {cards['K']:<16}"
        )

    if random_value is None:
        raise RuntimeError("missing random value")
    action = result.pick(random_value)
    cards = action.to_dict()
    print(f"\nRandom value: {random_value:.12f}")
    print(f"Selected: P={cards['P']}, B={cards['B']}, K={cards['K']}")


def _solve(args: argparse.Namespace) -> None:
    state = State(
        x=args.x,
        y=args.y,
        c=args.c,
        h=args.h,
        diagonal=args.diagonal,
        intrigue_2=args.intrigue_2,
        forbid_moves=args.forbid_moves,
    )
    print("Solving...")
    started = time.perf_counter()
    result = Solver().solve(state, args.day)
    if args.random_value is not None and args.seed is not None:
        raise ValueError("pass --random or --seed, not both")
    random_value = None
    if result.strategy:
        random_value = (
            random.Random(args.seed).random()
            if args.random_value is None
            else args.random_value
        )
    _print_result(result, random_value)
    print(f"Elapsed: {time.perf_counter() - started:.2f}s")

    data = result.to_dict()
    if result.strategy:
        data["random_value"] = random_value
        data["selected_action"] = result.pick(random_value).to_dict()
    _write_json(args.json_path, data)


def _average(args: argparse.Namespace) -> None:
    print("Solving...")
    started = time.perf_counter()
    rates = Solver().average_win_rates(args.days)
    print(f"{'Day':>3}  {'Average Alice win rate':>22}")
    for day, rate in rates.items():
        print(f"{day:>3}  {rate:>21.6%}")
    print(f"Elapsed: {time.perf_counter() - started:.2f}s")
    _write_json(args.json_path, {str(day): rate for day, rate in rates.items()})


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        _solve(args) if args.command == "solve" else _average(args)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc


if __name__ == "__main__":
    main()
