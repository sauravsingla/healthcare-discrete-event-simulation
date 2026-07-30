"""Command-line benchmark for the corrected advanced simulation engine."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd

from .advanced_model import AdvancedScenarioConfig, run_advanced_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark the advanced healthcare DES across demand and MRI capacity scales."
    )
    parser.add_argument("--days", type=int, default=7, help="Measurement days per run.")
    parser.add_argument("--replications", type=int, default=3, help="Replications per scenario.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/advanced_benchmark.csv"),
        help="CSV output path; metadata is written beside it as JSON.",
    )
    args = parser.parse_args()
    if args.days <= 0:
        parser.error("--days must be positive")
    if args.replications <= 0:
        parser.error("--replications must be positive")
    return args


def run_benchmark(days: int, replications: int) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for demand in (35.0, 70.0, 140.0):
        for machines in (1, 2, 4, 8, 12, 20):
            for replication in range(replications):
                config = replace(
                    AdvancedScenarioConfig(),
                    name=f"demand-{int(demand)}-mri-{machines}",
                    days=days,
                    daily_demand=demand,
                    mri_machines=machines,
                    bootstrap_samples=100,
                    seed=17,
                )
                started = time.perf_counter()
                result, patients, state = run_advanced_once(config, replication=replication)
                row = asdict(result)
                row.update(
                    {
                        "daily_demand": demand,
                        "mri_machines": machines,
                        "elapsed_seconds": time.perf_counter() - started,
                        "patient_rows": len(patients),
                        "state_rows": len(state),
                    }
                )
                rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    frame = run_benchmark(args.days, args.replications)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    metadata = {
        "days": args.days,
        "replications": args.replications,
        "scenarios": int(frame["scenario"].nunique()),
        "rows": len(frame),
    }
    args.output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    summary = frame.groupby(["daily_demand", "mri_machines"])["elapsed_seconds"].agg(
        ["mean", "max"]
    )
    print(summary)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
