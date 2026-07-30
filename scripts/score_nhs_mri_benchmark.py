"""Score provider-level NHS MRI benchmark observations with temporal holdouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"provider_code", "period", "actual", "predicted"}


def _safe_mape(actual: pd.Series, predicted: pd.Series) -> float:
    mask = actual.ne(0) & actual.notna() & predicted.notna()
    if not mask.any():
        return float("nan")
    return float(((actual[mask] - predicted[mask]).abs() / actual[mask].abs()).mean())


def _wape(actual: pd.Series, predicted: pd.Series) -> float:
    denominator = actual.abs().sum()
    if denominator == 0:
        return float("nan")
    return float((actual - predicted).abs().sum() / denominator)


def _correlation(actual: pd.Series, predicted: pd.Series) -> float:
    valid = pd.concat([actual, predicted], axis=1).dropna()
    if len(valid) < 2 or valid.iloc[:, 0].nunique() < 2 or valid.iloc[:, 1].nunique() < 2:
        return float("nan")
    return float(valid.iloc[:, 0].corr(valid.iloc[:, 1]))


def _direction_accuracy(actual: pd.Series, predicted: pd.Series) -> float:
    actual_direction = np.sign(actual.diff())
    predicted_direction = np.sign(predicted.diff())
    valid = actual_direction.notna() & predicted_direction.notna()
    if not valid.any():
        return float("nan")
    return float((actual_direction[valid] == predicted_direction[valid]).mean())


def assign_split(period: pd.Series, validation_months: int, holdout_months: int) -> pd.Series:
    parsed = pd.to_datetime(period, errors="coerce").dt.to_period("M")
    if parsed.isna().any():
        raise ValueError("All periods must be parseable as calendar months")
    unique_periods = sorted(parsed.unique())
    required = validation_months + holdout_months + 1
    if len(unique_periods) < required:
        raise ValueError(
            f"At least {required} distinct months are required for calibration, validation and holdout"
        )
    validation_start = unique_periods[-(validation_months + holdout_months)]
    holdout_start = unique_periods[-holdout_months]
    split = pd.Series("calibration", index=period.index, dtype="object")
    split.loc[parsed >= validation_start] = "validation"
    split.loc[parsed >= holdout_start] = "holdout"
    return split


def score(
    source: Path,
    output_csv: Path,
    output_json: Path,
    *,
    min_months: int = 6,
    validation_months: int = 2,
    holdout_months: int = 2,
) -> pd.DataFrame:
    frame = pd.read_csv(source, low_memory=False)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Benchmark file is missing required columns: {missing}")

    frame = frame.copy()
    frame["provider_code"] = frame["provider_code"].astype(str).str.strip().str.upper()
    frame["period"] = pd.to_datetime(frame["period"], errors="coerce").dt.to_period("M").astype(str)
    frame["actual"] = pd.to_numeric(frame["actual"], errors="coerce")
    frame["predicted"] = pd.to_numeric(frame["predicted"], errors="coerce")
    frame = frame.dropna(subset=["actual", "predicted"])
    frame = frame[frame["provider_code"].ne("") & frame["period"].ne("NaT")]
    if frame.empty:
        raise ValueError("No valid benchmark observations remain after cleaning")

    frame = frame.sort_values(["provider_code", "period"], ignore_index=True)
    frame["split"] = assign_split(frame["period"], validation_months, holdout_months)

    rows: list[dict[str, object]] = []
    exclusions: list[dict[str, object]] = []
    for provider_code, provider in frame.groupby("provider_code", sort=True):
        distinct_months = provider["period"].nunique()
        holdout = provider[provider["split"].eq("holdout")].copy()
        if distinct_months < min_months:
            exclusions.append(
                {
                    "provider_code": provider_code,
                    "reason": "insufficient_months",
                    "observed_months": int(distinct_months),
                }
            )
            continue
        if holdout.empty:
            exclusions.append(
                {
                    "provider_code": provider_code,
                    "reason": "no_holdout_observations",
                    "observed_months": int(distinct_months),
                }
            )
            continue

        actual = holdout["actual"]
        predicted = holdout["predicted"]
        row: dict[str, object] = {
            "provider_code": provider_code,
            "holdout_months": int(holdout["period"].nunique()),
            "actual_total": float(actual.sum()),
            "predicted_total": float(predicted.sum()),
            "wape": _wape(actual, predicted),
            "mape": _safe_mape(actual, predicted),
            "annualised_throughput_error": float(
                abs(predicted.sum() - actual.sum()) / abs(actual.sum())
            )
            if actual.sum() != 0
            else float("nan"),
            "seasonal_correlation": _correlation(actual, predicted),
            "direction_accuracy": _direction_accuracy(actual, predicted),
        }
        if "mri_scanners" in holdout.columns:
            scanners = pd.to_numeric(holdout["mri_scanners"], errors="coerce")
            valid = scanners.gt(0)
            row["actual_per_scanner"] = (
                float((actual[valid] / scanners[valid]).mean()) if valid.any() else float("nan")
            )
            row["predicted_per_scanner"] = (
                float((predicted[valid] / scanners[valid]).mean()) if valid.any() else float("nan")
            )
        rows.append(row)

    result = pd.DataFrame(rows).sort_values("provider_code", ignore_index=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False)

    metadata = {
        "source": str(source),
        "min_months": min_months,
        "validation_months": validation_months,
        "holdout_months": holdout_months,
        "included_providers": int(len(result)),
        "excluded_providers": exclusions,
        "claim_limit": "External operational benchmark only; not clinical validation.",
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Score NHS MRI provider benchmark observations")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/nhs_mri_benchmark.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("outputs/nhs_mri_benchmark.json"))
    parser.add_argument("--min-months", type=int, default=6)
    parser.add_argument("--validation-months", type=int, default=2)
    parser.add_argument("--holdout-months", type=int, default=2)
    args = parser.parse_args()
    result = score(
        args.source,
        args.output_csv,
        args.output_json,
        min_months=args.min_months,
        validation_months=args.validation_months,
        holdout_months=args.holdout_months,
    )
    print(f"Saved scores for {len(result)} providers")


if __name__ == "__main__":
    main()
