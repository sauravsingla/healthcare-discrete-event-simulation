"""Validate that an NHS external benchmark run produced publishable evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


REQUIRED_FILES = (
    "benchmark_input.csv",
    "provider_scores.csv",
    "run_metadata.json",
    "benchmark_report.md",
    "schema_inventory.json",
)


def validate(output_dir: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (output_dir / name).is_file()]
    if missing:
        raise ValueError(f"Missing benchmark outputs: {missing}")

    metadata = json.loads((output_dir / "run_metadata.json").read_text(encoding="utf-8"))
    providers = int(metadata.get("providers", 0))
    months = int(metadata.get("months", 0))
    rows = int(metadata.get("rows", 0))
    holdout_wape = metadata.get("national_holdout_wape")

    if providers < 1:
        raise ValueError("Benchmark contains no providers")
    if months < 6:
        raise ValueError(f"Benchmark covers only {months} months; at least 6 are required")
    if rows < providers:
        raise ValueError("Benchmark row count is inconsistent with provider count")
    if holdout_wape is None or not 0 <= float(holdout_wape):
        raise ValueError("National holdout WAPE is missing or invalid")

    benchmark = pd.read_csv(output_dir / "benchmark_input.csv")
    required_benchmark_columns = {"provider_code", "period", "actual", "predicted"}
    if not required_benchmark_columns.issubset(benchmark.columns):
        raise ValueError(
            "Benchmark input is missing columns: "
            f"{sorted(required_benchmark_columns.difference(benchmark.columns))}"
        )
    if benchmark.empty:
        raise ValueError("Benchmark input is empty")
    if benchmark[["actual", "predicted"]].isna().any().any():
        raise ValueError("Benchmark input contains missing actual or predicted values")

    provider_scores = pd.read_csv(output_dir / "provider_scores.csv")
    required_score_columns = {
        "provider_code",
        "holdout_months",
        "actual_total",
        "predicted_total",
        "wape",
        "throughput_error",
    }
    if not required_score_columns.issubset(provider_scores.columns):
        raise ValueError(
            "Provider scores are missing columns: "
            f"{sorted(required_score_columns.difference(provider_scores.columns))}"
        )
    if provider_scores.empty:
        raise ValueError("Provider score output is empty")
    if provider_scores["wape"].dropna().empty:
        raise ValueError("Provider score output has no valid WAPE values")

    report = (output_dir / "benchmark_report.md").read_text(encoding="utf-8")
    required_phrases = (
        "NHS MRI external benchmark",
        "National holdout WAPE",
        "not clinical validation",
    )
    absent = [phrase for phrase in required_phrases if phrase not in report]
    if absent:
        raise ValueError(f"Benchmark report is missing required statements: {absent}")

    summary = {
        "providers": providers,
        "months": months,
        "rows": rows,
        "national_holdout_wape": float(holdout_wape),
        "provider_score_rows": int(len(provider_scores)),
    }
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate outputs from the NHS external MRI benchmark"
    )
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    validate(args.output_dir)


if __name__ == "__main__":
    main()
