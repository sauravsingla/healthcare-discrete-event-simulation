"""Benchmark the corrected advanced simulation across demand and scanner scales."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd

from healthcare_des import AdvancedScenarioConfig, run_advanced_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--replications", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("outputs/advanced_benchmark.csv"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows: list[dict[str, float | int | str]] = []
    for demand in (35.0, 70.0, 140.0):
        for machines in (1, 2, 4, 8, 12, 20):
            for replication in range(args.replications):
                config = replace(
                    AdvancedScenarioConfig(),
                    name=f"demand-{int(demand)}-mri-{machines}",
                    days=args.days,
                    daily_demand=demand,
                    mri_machines=machines,
                    bootstrap_samples=100,
                    seed=17,
                )
                started = time.perf_counter()
                result, patients, state = run_advanced_once(config, replication=replication)
                elapsed = time.perf_counter() - started
                row = asdict(result)
                row.update(
                    {
                        "daily_demand": demand,
                        "mri_machines": machines,
                        "elapsed_seconds": elapsed,
                        "patient_rows": len(patients),
                        "state_rows": len(state),
                    }
                )
                rows.append(row)

    frame = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    metadata = {
        "days": args.days,
        "replications": args.replications,
        "scenarios": int(frame["scenario"].nunique()),
        "rows": len(frame),
    }
    args.output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(frame.groupby(["daily_demand", "mri_machines"])["elapsed_seconds"].agg(["mean", "max"]))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
