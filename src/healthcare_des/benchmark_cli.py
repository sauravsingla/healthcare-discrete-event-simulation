"""Command-line interface for reproducible multi-scenario benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .benchmark import benchmark_scenarios
from .config import load_config


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark standard healthcare capacity scenarios"
    )
    parser.add_argument("--config", required=True, help="Path to baseline scenario YAML")
    parser.add_argument("--replications", type=positive_int, default=20)
    parser.add_argument("--output", default="outputs/benchmark.csv")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = Path(args.output)
    if output.exists() and output.is_dir():
        raise ValueError(f"Output path is a directory: {output}")

    base = load_config(args.config)
    results = benchmark_scenarios(base, replications=args.replications)
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)

    columns = [
        "name",
        "mean_wait_minutes",
        "p90_system_minutes",
        "completed_within_120_pct",
        "throughput_per_day",
        "mean_wait_minutes_vs_baseline_pct",
        "throughput_per_day_vs_baseline_pct",
    ]
    print(results[columns].to_string(index=False))
    print(f"Saved benchmark results to {output}")


if __name__ == "__main__":
    main()
