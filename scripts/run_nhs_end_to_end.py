"""Build and score a derived NHS MRI benchmark from downloaded public releases."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROVIDER_ALIASES = (
    "provider code",
    "provider",
    "organisation code",
    "organisation",
    "organization code",
    "organization",
    "org code",
    "trust code",
    "provider org code",
)
PERIOD_ALIASES = (
    "period",
    "month",
    "reporting period",
    "reporting month",
    "activity month",
    "date",
)
MODALITY_ALIASES = (
    "modality",
    "test name",
    "diagnostic test",
    "activity type",
    "imaging modality",
    "procedure",
)
ACTIVITY_ALIASES = (
    "activity",
    "total activity",
    "tests",
    "number of tests",
    "count",
    "total",
    "value",
)
MRI_PATTERN = re.compile(r"\b(mri|magnetic resonance(?: imaging)?)\b", re.IGNORECASE)
MONTH_PATTERN = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b[\s_\-/]*(20\d{2})",
    re.IGNORECASE,
)


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


def infer_period(value: object) -> str | None:
    text = str(value)
    match = MONTH_PATTERN.search(text)
    if match:
        parsed = pd.to_datetime(f"{match.group(1)} {match.group(2)}", errors="coerce")
        if not pd.isna(parsed):
            return str(parsed.to_period("M"))
    parsed = pd.to_datetime(text, errors="coerce")
    if not pd.isna(parsed):
        return str(parsed.to_period("M"))
    return None


def _header_score(values: list[object]) -> int:
    columns = [str(value) for value in values if not pd.isna(value)]
    if not columns:
        return 0
    score = 0
    score += 3 if find_column(columns, PROVIDER_ALIASES) else 0
    score += 2 if find_column(columns, MODALITY_ALIASES) else 0
    score += 2 if find_column(columns, PERIOD_ALIASES) else 0
    score += 1 if find_column(columns, ACTIVITY_ALIASES) else 0
    score += sum(bool(MRI_PATTERN.search(column)) for column in columns)
    score += sum(infer_period(column) is not None for column in columns)
    return score


def _read_excel_sheet(path: Path, sheet: str) -> tuple[pd.DataFrame, int]:
    preview = pd.read_excel(path, sheet_name=sheet, header=None, nrows=20)
    scores = [_header_score(list(preview.iloc[index])) for index in range(len(preview))]
    header_row = int(np.argmax(scores)) if scores and max(scores) > 0 else 0
    frame = pd.read_excel(path, sheet_name=sheet, header=header_row)
    frame = frame.dropna(axis=0, how="all").dropna(axis=1, how="all")
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame, header_row


def _read_csv(path: Path) -> tuple[pd.DataFrame, int]:
    preview = pd.read_csv(path, header=None, nrows=20, low_memory=False)
    scores = [_header_score(list(preview.iloc[index])) for index in range(len(preview))]
    header_row = int(np.argmax(scores)) if scores and max(scores) > 0 else 0
    frame = pd.read_csv(path, header=header_row, low_memory=False)
    frame = frame.dropna(axis=0, how="all").dropna(axis=1, how="all")
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame, header_row


def read_tables(root: Path) -> tuple[list[tuple[str, pd.DataFrame]], list[dict[str, Any]]]:
    tables: list[tuple[str, pd.DataFrame]] = []
    inventory: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "download_receipt.json":
            continue
        try:
            if path.suffix.lower() == ".csv":
                frame, header_row = _read_csv(path)
                label = str(path.relative_to(root))
                tables.append((label, frame))
                inventory.append(
                    {
                        "table": label,
                        "header_row": header_row,
                        "rows": len(frame),
                        "columns": list(map(str, frame.columns)),
                    }
                )
            elif path.suffix.lower() in {".xlsx", ".xls"}:
                book = pd.ExcelFile(path)
                for sheet in book.sheet_names:
                    frame, header_row = _read_excel_sheet(path, sheet)
                    label = f"{path.relative_to(root)}::{sheet}"
                    tables.append((label, frame))
                    inventory.append(
                        {
                            "table": label,
                            "header_row": header_row,
                            "rows": len(frame),
                            "columns": list(map(str, frame.columns)),
                        }
                    )
        except Exception as exc:
            inventory.append(
                {
                    "table": str(path.relative_to(root)),
                    "error": type(exc).__name__,
                    "message": str(exc)[:500],
                }
            )
    return tables, inventory


def _clean_activity(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["provider_code"] = result["provider_code"].astype(str).str.strip().str.upper()
    result["period"] = pd.to_datetime(result["period"], errors="coerce").dt.to_period("M").astype(str)
    result["actual"] = pd.to_numeric(result["actual"], errors="coerce")
    result = result.dropna(subset=["actual"])
    result = result[result["provider_code"].ne("") & result["provider_code"].ne("NAN")]
    result = result[result["period"].ne("NaT")]
    return result[["provider_code", "period", "actual"]]


def _extract_long(label: str, frame: pd.DataFrame) -> pd.DataFrame | None:
    columns = list(map(str, frame.columns))
    provider = find_column(columns, PROVIDER_ALIASES)
    modality = find_column(columns, MODALITY_ALIASES)
    activity = find_column(columns, ACTIVITY_ALIASES)
    period = find_column(columns, PERIOD_ALIASES)
    inferred = infer_period(label)
    if not provider or not modality or not activity or (not period and not inferred):
        return None
    mask = frame[modality].astype(str).str.contains(MRI_PATTERN, na=False)
    if not mask.any():
        return None
    result = pd.DataFrame(
        {
            "provider_code": frame.loc[mask, provider],
            "period": frame.loc[mask, period] if period else inferred,
            "actual": frame.loc[mask, activity],
        }
    )
    return _clean_activity(result)


def _extract_month_columns(label: str, frame: pd.DataFrame) -> pd.DataFrame | None:
    columns = list(map(str, frame.columns))
    provider = find_column(columns, PROVIDER_ALIASES)
    modality = find_column(columns, MODALITY_ALIASES)
    month_columns = {column: infer_period(column) for column in columns}
    month_columns = {column: period for column, period in month_columns.items() if period}
    if not provider or not modality or not month_columns:
        return None
    rows = frame[frame[modality].astype(str).str.contains(MRI_PATTERN, na=False)]
    if rows.empty:
        return None
    melted = rows.melt(
        id_vars=[provider],
        value_vars=list(month_columns),
        var_name="source_period",
        value_name="actual",
    )
    melted["period"] = melted["source_period"].map(month_columns)
    melted = melted.rename(columns={provider: "provider_code"})
    return _clean_activity(melted[["provider_code", "period", "actual"]])


def _extract_mri_columns(label: str, frame: pd.DataFrame) -> pd.DataFrame | None:
    columns = list(map(str, frame.columns))
    provider = find_column(columns, PROVIDER_ALIASES)
    period = find_column(columns, PERIOD_ALIASES)
    inferred = infer_period(label)
    mri_columns = [column for column in columns if MRI_PATTERN.search(column)]
    if not provider or not mri_columns or (not period and not inferred):
        return None
    numeric = frame[mri_columns].apply(pd.to_numeric, errors="coerce")
    result = pd.DataFrame(
        {
            "provider_code": frame[provider],
            "period": frame[period] if period else inferred,
            "actual": numeric.sum(axis=1, min_count=1),
        }
    )
    return _clean_activity(result)


def extract_activity(tables: list[tuple[str, pd.DataFrame]]) -> tuple[pd.DataFrame, list[str]]:
    extracted: list[pd.DataFrame] = []
    sources: list[str] = []
    for label, frame in tables:
        for extractor in (_extract_long, _extract_month_columns, _extract_mri_columns):
            result = extractor(label, frame)
            if result is not None and not result.empty:
                extracted.append(result)
                sources.append(label)
                break
    if not extracted:
        raise ValueError(
            "No official NHS table yielded provider-month MRI activity in long, month-column, "
            "or MRI-column form; inspect schema_inventory.json"
        )
    result = pd.concat(extracted, ignore_index=True)
    result = result.groupby(["provider_code", "period"], as_index=False)["actual"].sum()
    if result["period"].nunique() < 6:
        raise ValueError(
            f"MRI extraction yielded only {result['period'].nunique()} months; "
            "inspect schema_inventory.json"
        )
    return result.sort_values(["provider_code", "period"], ignore_index=True), sorted(set(sources))


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
    for label, frame in tables:
        columns = list(map(str, frame.columns))
        provider = find_column(columns, PROVIDER_ALIASES)
        modality = find_column(columns, MODALITY_ALIASES)
        count = find_column(columns, ("asset count", "number of assets", "scanner count", "count"))
        if provider and modality and count:
            rows = frame[frame[modality].astype(str).str.contains(MRI_PATTERN, na=False)].copy()
            rows["provider_code"] = rows[provider].astype(str).str.strip().str.upper()
            rows["mri_scanners"] = pd.to_numeric(rows[count], errors="coerce")
            result = rows.groupby("provider_code", as_index=False)["mri_scanners"].sum()
            if not result.empty:
                return result[result["mri_scanners"].gt(0)]
        mri_columns = [column for column in columns if MRI_PATTERN.search(column)]
        if provider and mri_columns and "asset" in normalise(label):
            values = frame[mri_columns].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
            result = pd.DataFrame(
                {
                    "provider_code": frame[provider].astype(str).str.strip().str.upper(),
                    "mri_scanners": values,
                }
            )
            result = result.groupby("provider_code", as_index=False)["mri_scanners"].sum()
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
    inventory_path = output_dir / "schema_inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    try:
        activity, source_tables = extract_activity(tables)
        benchmark, baseline, validation_scores = add_predictions(activity)
        capacity = optional_capacity(tables)
        capacity_matches = 0
        if capacity is not None:
            before = len(benchmark)
            benchmark = benchmark.merge(
                capacity, on="provider_code", how="left", validate="many_to_one"
            )
            if len(benchmark) != before:
                raise ValueError("Capacity join changed benchmark row count")
            capacity_matches = int(benchmark["mri_scanners"].notna().sum())
        scores = score_providers(benchmark)
        benchmark.to_csv(output_dir / "benchmark_input.csv", index=False)
        scores.to_csv(output_dir / "provider_scores.csv", index=False)
        holdout_periods = sorted(benchmark["period"].unique())[-2:]
        holdout = benchmark[benchmark["period"].isin(holdout_periods)]
        national_actual = float(holdout["actual"].sum())
        national_predicted = float(holdout["predicted"].sum())
        metadata = {
            "activity_source_tables": source_tables,
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
            "claim_limit": (
                "External operational benchmark only; not clinical validation or causal inference."
            ),
        }
        (output_dir / "run_metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        wape = metadata["national_holdout_wape"]
        lines = [
            "# NHS MRI external benchmark",
            "",
            f"- Activity source tables: {len(source_tables)}",
            f"- Providers: {metadata['providers']}",
            f"- Months: {metadata['months']}",
            f"- Selected leakage-free baseline: `{baseline}`",
            f"- National holdout WAPE: {wape:.4f}" if wape is not None else "- National holdout WAPE: unavailable",
            f"- Rows matched to MRI scanner capacity: {capacity_matches}",
            "",
            "Results are derived from public operational data and are not clinical validation.",
        ]
        (output_dir / "benchmark_report.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    except Exception as exc:
        failure = {
            "error": type(exc).__name__,
            "message": str(exc),
            "tables_read": len(tables),
            "inventory": str(inventory_path),
        }
        (output_dir / "failure_diagnostics.json").write_text(
            json.dumps(failure, indent=2), encoding="utf-8"
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the complete NHS MRI public-data benchmark")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/nhs_public"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/nhs_end_to_end"))
    args = parser.parse_args()
    run(args.raw_dir, args.output_dir)


if __name__ == "__main__":
    main()
