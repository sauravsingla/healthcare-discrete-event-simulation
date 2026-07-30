"""Prepare NHS England Diagnostic Imaging Dataset extracts for benchmarking."""

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
    """Resolve the first column matching every keyword in an alternative."""
    normalised = {column: normalise_name(column) for column in columns}
    for keywords in alternatives:
        for column, value in normalised.items():
            if all(keyword in value for keyword in keywords):
                return column
    if required:
        raise ValueError(f"Could not identify column matching any of: {alternatives}")
    return None


def period_values(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    year_col = find_column(columns, (("year",),), required=False)
    month_col = find_column(
        columns,
        (("month", "number"), ("month", "num"), ("month",)),
        required=False,
    )
    if year_col is not None and month_col is not None:
        parsed = pd.to_datetime(
            {"year": frame[year_col], "month": frame[month_col], "day": 1},
            errors="coerce",
        )
        if parsed.notna().any():
            return parsed.dt.to_period("M").astype(str)

    period_col = find_column(
        columns,
        (("reporting", "period"), ("period",), ("date",), ("month",)),
        required=False,
    )
    if period_col is not None:
        parsed = pd.to_datetime(frame[period_col], errors="coerce")
        if parsed.notna().any():
            return parsed.dt.to_period("M").astype(str)

    raise ValueError("Could not derive a provider-month period from the supplied DID file")


def prepare(source: Path, output: Path) -> pd.DataFrame:
    frame = pd.read_csv(source, low_memory=False)
    columns = list(frame.columns)
    modality_col = find_column(
        columns,
        (("modality",), ("imaging", "type"), ("test", "name"), ("diagnostic", "test")),
    )
    provider_col = find_column(
        columns,
        (("provider", "code"), ("organisation", "code"), ("org", "code")),
    )
    provider_name_col = find_column(
        columns,
        (("provider", "name"), ("organisation", "name"), ("org", "name")),
        required=False,
    )
    activity_col = find_column(
        columns,
        (("activity",), ("examinations",), ("tests", "performed"), ("total", "tests")),
    )
    source_col = find_column(
        columns,
        (("patient", "source"), ("patient", "type"), ("setting",)),
        required=False,
    )
    request_to_test_col = find_column(
        columns,
        (("request", "test"), ("referral", "test")),
        required=False,
    )
    test_to_report_col = find_column(
        columns,
        (("test", "report"), ("report", "turnaround")),
        required=False,
    )

    mri_mask = (
        frame[modality_col]
        .astype(str)
        .str.contains(MRI_PATTERN, case=False, na=False, regex=True)
    )
    mri = frame[mri_mask].copy()
    if mri.empty:
        raise ValueError("No MRI activity rows found in the supplied DID file")

    mri["provider_code"] = mri[provider_col].astype(str).str.strip().str.upper()
    mri["period"] = period_values(mri, columns)
    mri["mri_activity"] = pd.to_numeric(mri[activity_col], errors="coerce")
    mri["patient_source"] = (
        mri[source_col].astype(str).str.strip().str.lower()
        if source_col is not None
        else "all"
    )
    mri = mri.dropna(subset=["mri_activity"])
    mri = mri[mri["provider_code"].ne("") & mri["period"].ne("")]
    if mri.empty:
        raise ValueError("No valid provider-period MRI rows remain after cleaning")

    result = pd.DataFrame(
        {
            "provider_code": mri["provider_code"],
            "provider_name": (
                mri[provider_name_col].astype(str).str.strip()
                if provider_name_col is not None
                else ""
            ),
            "period": mri["period"],
            "patient_source": mri["patient_source"],
            "mri_activity": mri["mri_activity"].astype(float),
        }
    )
    if request_to_test_col is not None:
        result["request_to_test_days"] = pd.to_numeric(
            mri[request_to_test_col], errors="coerce"
        )
    if test_to_report_col is not None:
        result["test_to_report_days"] = pd.to_numeric(
            mri[test_to_report_col], errors="coerce"
        )

    aggregations: dict[str, str] = {
        "provider_name": "first",
        "mri_activity": "sum",
    }
    if "request_to_test_days" in result:
        aggregations["request_to_test_days"] = "median"
    if "test_to_report_days" in result:
        aggregations["test_to_report_days"] = "median"

    result = (
        result.groupby(
            ["provider_code", "period", "patient_source"],
            as_index=False,
            dropna=False,
        )
        .agg(aggregations)
        .sort_values(
            ["provider_code", "period", "patient_source"],
            ignore_index=True,
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardise NHS provider-month MRI DID data"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_did_mri_provider_month.csv"),
    )
    args = parser.parse_args()
    result = prepare(args.source, args.output)
    print(f"Saved {len(result)} provider-month-source MRI rows to {args.output}")


if __name__ == "__main__":
    main()
