"""Build and score a derived NHS MRI benchmark from downloaded public releases."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROVIDER_ALIASES = ("provider code", "organisation code", "organization code", "org code")
PERIOD_ALIASES = ("period", "month", "reporting period", "date")
MODALITY_ALIASES = ("modality", "test name", "diagnostic test", "activity type")
ACTIVITY_ALIASES = ("activity", "total activity", "tests", "number of tests", "count")
MRI_PATTERN = re.compile(r"\b(mri|magnetic resonance)\b", re.IGNORECASE)


def normalise(value: object) -> str:
    return " ".join(str(value).lower().replace("_", " ").replace("-", " ").split())


def find_column(columns: list[str], aliases: tuple[str, ...]) -> str | None:
    normalised = {column: normalise(column) for column in columns}
    for alias in aliases:
        target = normalise(alias)
        for column, value in normalised.items():
            if value == target or target in value:
                return column
    return None


def read_tables(root: Path) -> tuple[list[tuple[str, pd.DataFrame]], list[dict[str, Any]]]:
    tables: list[tuple[str, pd.DataFrame]] = []
    inventory: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "download_receipt.json":
            continue
        try:
            if path.suffix.lower() == ".csv":
                frame = pd.read_csv(path, low_memory=False)
                label = str(path.relative_to(root))
                tables.append((label, frame))
                inventory.append(
                    {"table": label, "rows": len(frame), "columns": list(map(str, frame.columns))}
                )
            elif path.suffix.lower() in {".xlsx", ".xls"}:
                book = pd.ExcelFile(path)
                for sheet in book.sheet_names:
                    frame = pd.read_excel(path, sheet_name=sheet)
                    label = f"{path.relative_to(root)}::{sheet}"
                    tables.append((label, frame))
                    inventory.append(
                        {
                            "table": label,
                            "rows": len(frame),
                            "columns": list(map(str, frame.columns)),
                        }
                    )
        except Exception as exc:  # schema evidence must survive unreadable ancillary files
            inventory.append({"table": str(path.relative_to(root)), "error": type(exc).__name__})
    return tables, inventory


def extract_activity(tables: list[tuple[str, pd.DataFrame]]) -> tuple[pd.DataFrame, str]:
    candidates: list[tuple[int, str, pd.DataFrame, dict[str, str]]] = []
    for label, frame in tables:
        columns = list(map(str, frame.columns))
        mapping = {
            "provider": find_column(columns, PROVIDER_ALIASES),
            "period": find_column(columns, PERIOD_ALIASES),
            "modality": find_column(columns, MODALITY_ALIASES),
            "activity": find_column(columns, ACTIVITY_ALIASES),
        }
        if all(mapping.values()):
            modality = frame[mapping["modality"]].astype(str)
            score = int(modality.str.contains(MRI_PATTERN, na=False).sum())
            if score:
                candidates.append((score, label, frame, mapping))
    if not candidates:
        raise ValueError(
            "No table contained identifiable provider, period, modality and activity columns with MRI rows"
        )
    _, label, frame, mapping = max(candidates, key=lambda item: item[0])
    result = frame.loc[
        frame[mapping["modality"]].astype(str).str.contains(MRI_PATTERN, na=False),
        [mapping["provider"], mapping["period"], mapping["activity"]],
    ].copy()
    result.columns = ["provider_code", "period", "actual"]
    result["provider_code"] = result["provider_code"].astype(str).str.strip().str.upper()
    result["period"] = (
        pd.to_datetime(result["period"], errors="coerce").dt.to_period("M").astype(str)
    )
    result["actual"] = pd.to_numeric(result["actual"], errors="coerce")
    result = result.dropna(subset=["actual"])
    result = result[result["provider_code"].ne("") & result["period"].ne("NaT")]
    result = result.groupby(["provider_code", "period"], as_index=False)["actual"].sum()
    if result.empty or result["period"].nunique() < 6:
        raise ValueError("MRI activity extraction produced fewer than six valid months")
    return result.sort_values(["provider_code", "period"], ignore_index=True), label


def add_predictions(activity: pd.DataFrame) -> tuple[pd.DataFrame, str, dict[str, float]]:
    frame = activity.copy()
    grouped = frame.groupby("provider_code", sort=False)["actual"]
    frame["lag_1"] = grouped.shift(1)
    frame["trailing_3"] = grouped.transform(
        lambda values: values.shift(1).rolling(3, min_periods=1).mean()
    )
    periods = sorted(frame["period"].unique())
    validation = set(periods[-4:-2]) if len(periods) >= 6 else set(periods[-2:])
    scores: dict[str, float] = {}
    for candidate in ("lag_1", "trailing_3"):
        sample = frame[frame["period"].isin(validation)].dropna(subset=[candidate])
        denominator = sample["actual"].abs().sum()
        scores[candidate] = (
            float((sample["actual"] - sample[candidate]).abs().sum() / denominator)
            if denominator
            else float("inf")
        )
    selected = min(scores, key=scores.get)
    frame["predicted"] = frame[selected]
    frame = frame.dropna(subset=["predicted"]).reset_index(drop=True)
    return frame, selected, scores


def optional_capacity(tables: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame | None:
    for _, frame in tables:
        columns = list(map(str, frame.columns))
        provider = find_column(columns, PROVIDER_ALIASES)
        modality = find_column(columns, MODALITY_ALIASES)
        count = find_column(columns, ("asset count", "number of assets", "scanner count", "count"))
        if provider and modality and count:
            rows = frame[frame[modality].astype(str).str.contains(MRI_PATTERN, na=False)].copy()
            rows["provider_code"] = rows[provider].astype(str).str.strip().str.upper()
            rows["mri_scanners"] = pd.to_numeric(rows[count], errors="coerce")
            result = rows.groupby("provider_code", as_index=False)["mri_scanners"].sum()
            return result[result["mri_scanners"].gt(0)]
    return None


def score_providers(frame: pd.DataFrame, holdout_months: int = 2) -> pd.DataFrame:
    periods = sorted(frame["period"].unique())
    holdout = set(periods[-holdout_months:])
    sample = frame[frame["period"].isin(holdout)]
    rows: list[dict[str, Any]] = []
    for provider, group in sample.groupby("provider_code", sort=True):
        actual = group["actual"].sum()
        predicted = group["predicted"].sum()
        row: dict[str, Any] = {
            "provider_code": provider,
            "holdout_months": group["period"].nunique(),
            "actual_total": float(actual),
            "predicted_total": float(predicted),
            "wape": float((group["actual"] - group["predicted"]).abs().sum() / abs(actual))
            if actual
            else np.nan,
            "throughput_error": float(abs(predicted - actual) / abs(actual)) if actual else np.nan,
        }
        if "mri_scanners" in group:
            scanners = pd.to_numeric(group["mri_scanners"], errors="coerce").dropna()
            if not scanners.empty and scanners.iloc[0] > 0:
                row["actual_per_scanner"] = float(actual / scanners.iloc[0])
        rows.append(row)
    return pd.DataFrame(rows).sort_values("provider_code", ignore_index=True)


def run(raw_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    tables, inventory = read_tables(raw_dir)
    activity, source_table = extract_activity(tables)
    benchmark, baseline, validation_scores = add_predictions(activity)
    capacity = optional_capacity(tables)
    capacity_matches = 0
    if capacity is not None:
        before = len(benchmark)
        benchmark = benchmark.merge(
            capacity, on="provider_code", how="left", validate="many_to_one"
        )
        assert len(benchmark) == before
        capacity_matches = int(benchmark["mri_scanners"].notna().sum())
    scores = score_providers(benchmark)
    benchmark.to_csv(output_dir / "benchmark_input.csv", index=False)
    scores.to_csv(output_dir / "provider_scores.csv", index=False)
    (output_dir / "schema_inventory.json").write_text(
        json.dumps(inventory, indent=2), encoding="utf-8"
    )
    holdout_periods = sorted(benchmark["period"].unique())[-2:]
    national_actual = float(benchmark[benchmark["period"].isin(holdout_periods)]["actual"].sum())
    national_predicted = float(
        benchmark[benchmark["period"].isin(holdout_periods)]["predicted"].sum()
    )
    metadata = {
        "activity_source_table": source_table,
        "baseline_selected": baseline,
        "validation_wape": validation_scores,
        "providers": int(benchmark["provider_code"].nunique()),
        "months": int(benchmark["period"].nunique()),
        "rows": int(len(benchmark)),
        "capacity_joined_rows": capacity_matches,
        "national_holdout_actual": national_actual,
        "national_holdout_predicted": national_predicted,
        "national_holdout_wape": float(
            abs(national_predicted - national_actual) / abs(national_actual)
        )
        if national_actual
        else None,
        "claim_limit": "External operational benchmark only; not clinical validation or causal inference.",
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    lines = [
        "# NHS MRI external benchmark",
        "",
        f"- Activity source: `{source_table}`",
        f"- Providers: {metadata['providers']}",
        f"- Months: {metadata['months']}",
        f"- Selected leakage-free baseline: `{baseline}`",
        f"- National holdout WAPE: {metadata['national_holdout_wape']:.4f}"
        if metadata["national_holdout_wape"] is not None
        else "- National holdout WAPE: unavailable",
        f"- Rows matched to MRI scanner capacity: {capacity_matches}",
        "",
        "Results are derived from public operational data and are not clinical validation.",
    ]
    (output_dir / "benchmark_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete NHS MRI public-data benchmark")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/nhs_public"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/nhs_end_to_end"))
    args = parser.parse_args()
    run(args.raw_dir, args.output_dir)


if __name__ == "__main__":
    main()
