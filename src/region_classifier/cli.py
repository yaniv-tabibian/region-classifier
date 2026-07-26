"""Command-line entry point: ``region-sim --config configs/two_circles.yaml``."""

from __future__ import annotations

import argparse
import sys

from .config import SimConfig
from .simulator import Tick, run

_COLOR = {"In A": "\033[92m", "In B": "\033[94m", "Outside": "\033[90m"}
_RESET = "\033[0m"


def _make_console_reporter(validate: bool, color: bool):
    state: dict[str, str | None] = {"last": None}

    def report(t: Tick) -> None:
        tag = t.label
        if color:
            tag = f"{_COLOR.get(t.label, '')}{t.label:<8}{_RESET}"
        else:
            tag = f"{t.label:<8}"
        line = f"\rt={t.t:6.1f}s  d_a={t.d_a:6.2f}  d_b={t.d_b:6.2f}  ->  {tag}"
        if validate and t.truth is not None:
            mark = "OK" if t.label == t.truth else f"!= {t.truth}"
            line += f"   (truth: {t.truth:<8} {mark})"
        sys.stdout.write(line)
        if t.label != state["last"]:  # newline only on a state change
            sys.stdout.write("\n")
            state["last"] = t.label
        sys.stdout.flush()

    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="region-sim",
        description="Real-time In A / In B / Outside classification of a moving "
        "GPS sensor from shortest-distance-to-boundary streams.",
    )
    ap.add_argument("--config", required=True, help="path to a YAML scenario file")
    ap.add_argument(
        "--duration", type=float, default=None, help="override duration in seconds"
    )
    ap.add_argument("--dt", type=float, default=None, help="override time step")
    ap.add_argument("--seed", type=int, default=None, help="override RNG seed")
    ap.add_argument(
        "--no-realtime",
        action="store_true",
        help="run as fast as possible (no wall-clock pacing)",
    )
    ap.add_argument(
        "--validate",
        action="store_true",
        help="compare against ground truth and print accuracy",
    )
    ap.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    ap.add_argument(
        "--plot",
        action="store_true",
        help="live matplotlib view (needs the 'viz' extra)",
    )
    ap.add_argument(
        "--save-gif",
        default=None,
        help="render the run to a GIF at this path instead of showing",
    )
    args = ap.parse_args(argv)

    try:
        config = SimConfig.load(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    if args.duration is not None:
        config.duration_s = args.duration
    if args.dt is not None:
        config.dt = args.dt
    if args.seed is not None:
        config.seed = args.seed

    if args.plot or args.save_gif:
        try:
            from .visualize import run_live
        except ImportError:
            print(
                "matplotlib is required for --plot/--save-gif: "
                "pip install 'region-classifier[viz]'",
                file=sys.stderr,
            )
            return 2
        run_live(config, save_gif=args.save_gif)
        return 0

    reporter = _make_console_reporter(args.validate, color=not args.no_color)
    try:
        stats = run(
            config,
            reporter=reporter,
            realtime=not args.no_realtime,
            validate=args.validate,
        )
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130

    if args.validate:
        print(
            f"\naccuracy vs ground truth: {stats.accuracy:6.2%} "
            f"over {stats.ticks} ticks"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
