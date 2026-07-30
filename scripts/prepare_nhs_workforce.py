"""Prepare NHS imaging workforce data and join it to MRI benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

IMAGING_PATTERN = r"radiograph|radiology|imaging|diagnostic"


def normalise_name(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def find_column(
    columns: list[str],
    alternatives: tuple[tuple[str, ...], ...],
    *,
    required: bool = True,
) -> str | None:
    normalised = {column: normalise_name(column) for column in columns}
    for keywords in alternatives:
        for column, value in normalised.items():
            if all(keyword in value for keyword in keywords):
                return column
    if required:
        raise ValueError(f"Could not identify column matching any of: {alternatives}")
    return None


def prepare_workforce(source: Path, output: Path) -> pd.DataFrame:
    """Create a deterministic provider-year imaging workforce table."""
    frame = pd.read_csv(source, low_memory=False)
    columns = list(frame.columns)
    provider_col = find_column(
        columns,
        (("provider", "code"), ("organisation", "code"), ("org", "code")),
    )
    year_col = find_column(
        columns,
        (("reporting", "year"), ("financial", "year"), ("year",)),
    )
    fte_col = find_column(
        columns,
        (("fte",), ("full", "time", "equivalent"), ("workforce", "count")),
    )
    category_col = find_column(
        columns,
        (("staff", "group"), ("workforce", "category"), ("occupation",)),
        required=False,
    )

    workforce = frame.copy()
    if category_col is not None:
        workforce = workforce[
            workforce[category_col]
            .astype(str)
            .str.contains(IMAGING_PATTERN, case=False, na=False, regex=True)
        ].copy()
    if workforce.empty:
        raise ValueError("No imaging workforce rows found in the supplied file")

    workforce["provider_code"] = workforce[provider_col].astype(str).str.strip().str.upper()
    workforce["reporting_year"] = workforce[year_col].astype(str).str.strip().str[:4]
    workforce["imaging_workforce_fte"] = pd.to_numeric(workforce[fte_col], errors="coerce")
    workforce = workforce.dropna(subset=["imaging_workforce_fte"])
    workforce = workforce[workforce["provider_code"].ne("") & workforce["reporting_year"].ne("")]
    if workforce.empty:
        raise ValueError("No valid provider-year workforce rows remain after cleaning")

    result = (
        workforce.groupby(["provider_code", "reporting_year"], as_index=False)
        .agg(imaging_workforce_fte=("imaging_workforce_fte", "sum"))
        .sort_values(["provider_code", "reporting_year"], ignore_index=True)
    )
    result["workforce_status"] = "valid"
    result.loc[result["imaging_workforce_fte"].eq(0), "workforce_status"] = "zero"
    result.loc[result["imaging_workforce_fte"].lt(0), "workforce_status"] = "invalid_negative"
    result.loc[result["imaging_workforce_fte"].gt(10000), "workforce_status"] = "implausible_high"

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def join_benchmark(
    benchmark_source: Path,
    workforce_source: Path,
    output: Path,
) -> pd.DataFrame:
    """Join provider-month MRI benchmark observations to provider-year workforce."""
    benchmark = pd.read_csv(benchmark_source, low_memory=False)
    workforce = pd.read_csv(workforce_source, low_memory=False)
    required_benchmark = {"provider_code", "period"}
    required_workforce = {
        "provider_code",
        "reporting_year",
        "imaging_workforce_fte",
    }
    if not required_benchmark.issubset(benchmark.columns):
        missing = sorted(required_benchmark.difference(benchmark.columns))
        raise ValueError(f"Benchmark file is missing required columns: {missing}")
    if not required_workforce.issubset(workforce.columns):
        missing = sorted(required_workforce.difference(workforce.columns))
        raise ValueError(f"Workforce file is missing required columns: {missing}")

    benchmark = benchmark.copy()
    workforce = workforce.copy()
    benchmark["provider_code"] = benchmark["provider_code"].astype(str).str.strip().str.upper()
    workforce["provider_code"] = workforce["provider_code"].astype(str).str.strip().str.upper()
    benchmark["reporting_year"] = benchmark["period"].astype(str).str[:4]
    workforce["reporting_year"] = workforce["reporting_year"].astype(str).str[:4]

    result = benchmark.merge(
        workforce,
        on=["provider_code", "reporting_year"],
        how="left",
        validate="many_to_one",
    )
    result["workforce_join_status"] = (
        result["imaging_workforce_fte"].notna().map({True: "matched", False: "missing"})
    )
    valid_fte = result["imaging_workforce_fte"].gt(0)
    for source_column, output_column in (
        ("mri_activity", "mri_activity_per_workforce_fte"),
        ("actual", "actual_per_workforce_fte"),
        ("predicted", "predicted_per_workforce_fte"),
        ("mri_scanners", "scanners_per_workforce_fte"),
        ("backlog", "backlog_per_workforce_fte"),
    ):
        if source_column in result.columns:
            result[output_column] = pd.NA
            result.loc[valid_fte, output_column] = (
                pd.to_numeric(result.loc[valid_fte, source_column], errors="coerce")
                / result.loc[valid_fte, "imaging_workforce_fte"]
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare NHS imaging workforce data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("source", type=Path)
    prepare_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_imaging_workforce.csv"),
    )

    join_parser = subparsers.add_parser("join")
    join_parser.add_argument("benchmark", type=Path)
    join_parser.add_argument("workforce", type=Path)
    join_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_mri_with_workforce.csv"),
    )

    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_workforce(args.source, args.output)
    else:
        result = join_benchmark(args.benchmark, args.workforce, args.output)
    print(f"Saved {len(result)} rows to {args.output}")


if __name__ == "__main__":
    main()
