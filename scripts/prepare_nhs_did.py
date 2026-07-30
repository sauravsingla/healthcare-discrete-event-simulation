"""Prepare NHS Diagnostic Imaging Dataset extracts for MRI benchmarking."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

MRI_PATTERN = r"MRI|magnetic resonance"


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


def standardise_source(value: object) -> str:
    text = normalise_name(str(value))
    if "outpatient" in text:
        return "outpatient"
    if "inpatient" in text or "admitted" in text:
        return "inpatient"
    if "emergency" in text or "a&e" in text or "ae" == text:
        return "emergency"
    return "other"


def prepare(source: Path, output: Path) -> pd.DataFrame:
    frame = pd.read_csv(source, low_memory=False)
    columns = list(frame.columns)

    provider_col = find_column(
        columns,
        (("provider", "code"), ("organisation", "code"), ("org", "code")),
    )
    period_col = find_column(
        columns,
        (("reporting", "period"), ("period",), ("month",), ("date",)),
    )
    modality_col = find_column(
        columns,
        (("modality",), ("test", "name"), ("imaging", "type")),
    )
    activity_col = find_column(
        columns,
        (("activity",), ("examinations",), ("tests",), ("count",)),
    )
    source_col = find_column(
        columns,
        (("patient", "source"), ("source", "setting"), ("patient", "type")),
        required=False,
    )
    report_time_col = find_column(
        columns,
        (("test", "report", "median"), ("report", "turnaround"), ("reporting", "time")),
        required=False,
    )

    mri = frame[
        frame[modality_col]
        .astype(str)
        .str.contains(MRI_PATTERN, case=False, na=False, regex=True)
    ].copy()
    if mri.empty:
        raise ValueError("No MRI rows found in the supplied DID file")

    mri["provider_code"] = mri[provider_col].astype(str).str.strip().str.upper()
    parsed_period = pd.to_datetime(mri[period_col], errors="coerce")
    mri["period"] = parsed_period.dt.to_period("M").astype(str)
    mri["did_mri_activity"] = pd.to_numeric(mri[activity_col], errors="coerce")
    mri = mri.dropna(subset=["did_mri_activity"])
    mri = mri[mri["provider_code"].ne("") & mri["period"].ne("NaT")]
    if mri.empty:
        raise ValueError("No valid provider-month MRI rows remain after cleaning")

    if source_col is not None:
        mri["patient_source"] = mri[source_col].map(standardise_source)
    else:
        mri["patient_source"] = "all"

    group_columns = ["provider_code", "period", "patient_source"]
    aggregations: dict[str, str] = {"did_mri_activity": "sum"}
    if report_time_col is not None:
        mri["median_test_to_report_days"] = pd.to_numeric(
            mri[report_time_col], errors="coerce"
        )
        aggregations["median_test_to_report_days"] = "median"

    result = (
        mri.groupby(group_columns, as_index=False)
        .agg(aggregations)
        .sort_values(group_columns, ignore_index=True)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardise NHS DID provider-month MRI activity data"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_did_mri_provider_month.csv"),
    )
    args = parser.parse_args()
    result = prepare(args.source, args.output)
    print(f"Saved {len(result)} DID MRI rows to {args.output}")


if __name__ == "__main__":
    main()
