"""Prepare NHS England diagnostics data for MRI external benchmarking.

The public DM01 extracts have changed column names across releases. This module
normalises a supplied CSV into one deterministic provider-period table while
failing loudly when the required fields cannot be resolved.
"""

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


def _period_values(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
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
        values = frame[period_col].astype(str).str.strip()
        if values.ne("").any():
            return values

    raise ValueError("Could not derive a provider-month period from the supplied NHS file")


def prepare(source: Path, output: Path) -> pd.DataFrame:
    frame = pd.read_csv(source, low_memory=False)
    columns = list(frame.columns)
    test_col = find_column(
        columns,
        (("modality",), ("test", "name"), ("diagnostic", "test"), ("test",)),
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
        (("activity",), ("tests", "carried"), ("total", "tests")),
    )
    waiting_list_col = find_column(
        columns,
        (("waiting", "list"), ("patients", "waiting")),
        required=False,
    )

    mri = frame[
        frame[test_col].astype(str).str.contains(MRI_PATTERN, case=False, na=False, regex=True)
    ].copy()
    if mri.empty:
        raise ValueError("No MRI activity rows found in the supplied NHS file")

    mri["provider_code"] = mri[provider_col].astype(str).str.strip().str.upper()
    mri["period"] = _period_values(mri, columns)
    mri["activity"] = pd.to_numeric(mri[activity_col], errors="coerce")
    mri = mri.dropna(subset=["activity"])
    mri = mri[mri["provider_code"].ne("") & mri["period"].ne("")]
    if mri.empty:
        raise ValueError("No valid provider-period MRI activity rows remain after cleaning")

    result = pd.DataFrame(
        {
            "provider_code": mri["provider_code"],
            "provider_name": (
                mri[provider_name_col].astype(str).str.strip()
                if provider_name_col is not None
                else ""
            ),
            "period": mri["period"],
            "mri_activity": mri["activity"].astype(float),
        }
    )
    if waiting_list_col is not None:
        result["mri_waiting_list"] = pd.to_numeric(
            mri[waiting_list_col], errors="coerce"
        ).fillna(0.0)

    aggregations: dict[str, str] = {
        "provider_name": "first",
        "mri_activity": "sum",
    }
    if "mri_waiting_list" in result:
        aggregations["mri_waiting_list"] = "sum"
    result = (
        result.groupby(["provider_code", "period"], as_index=False)
        .agg(aggregations)
        .sort_values(["provider_code", "period"], ignore_index=True)
    )
    result["activity_per_calendar_day"] = result["mri_activity"] / pd.PeriodIndex(
        result["period"], freq="M"
    ).days_in_month

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardise NHS provider-month MRI diagnostics activity data"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_mri_provider_month.csv"),
    )
    args = parser.parse_args()
    result = prepare(args.source, args.output)
    print(f"Saved {len(result)} provider-month MRI rows to {args.output}")


if __name__ == "__main__":
    main()
