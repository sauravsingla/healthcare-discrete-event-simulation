"""Command-line runner for reproducible simulation experiments."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .config import calibrate_daily_demand, load_config
from .model import run_replications, summarise


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run healthcare MRI capacity scenarios")
    parser.add_argument("--config", required=True, help="Path to scenario YAML")
    parser.add_argument("--replications", type=positive_int, default=20)
    parser.add_argument("--demand-csv", help="Optional standardised monthly activity CSV")
    parser.add_argument("--output", default="outputs/results.csv")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.demand_csv:
        config = replace(config, daily_demand=calibrate_daily_demand(args.demand_csv))
        config.validate()

    results = run_replications(config, args.replications)
    output = Path(args.output)
    if output.exists() and output.is_dir():
        raise IsADirectoryError(f"Output path is a directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    print(json.dumps(summarise(results), indent=2, sort_keys=True))
    print(f"Saved replication results to {output}")


if __name__ == "__main__":
    main()
