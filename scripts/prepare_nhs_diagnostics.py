"""Prepare NHS England diagnostics data for MRI demand calibration.

Download a provider/commissioner CSV ZIP from the official NHS England monthly
Diagnostic Waiting Times and Activity publication, extract it, and pass the CSV
path to this script. Column names vary across releases, so the script uses
case-insensitive keyword matching and fails loudly when it cannot identify the
required fields.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def find_column(columns: list[str], keywords: tuple[str, ...]) -> str:
    for column in columns:
        value = column.lower().replace("_", " ")
        if all(keyword in value for keyword in keywords):
            return column
    raise ValueError(f"Could not identify column containing: {keywords}")


def prepare(source: Path, output: Path) -> pd.DataFrame:
    frame = pd.read_csv(source, low_memory=False)
    columns = list(frame.columns)
    test_col = find_column(columns, ("test",))
    activity_col = find_column(columns, ("activity",))

    mri = frame[
        frame[test_col].astype(str).str.contains("MRI|magnetic resonance", case=False, na=False)
    ].copy()
    mri[activity_col] = pd.to_numeric(mri[activity_col], errors="coerce")
    mri = mri.dropna(subset=[activity_col])
    if mri.empty:
        raise ValueError("No MRI activity rows found in the supplied NHS file")

    result = pd.DataFrame(
        {
            "source_test_name": mri[test_col].astype(str),
            "activity": mri[activity_col].astype(float),
        }
    )
    result = result.groupby("source_test_name", as_index=False)["activity"].sum()
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Standardise NHS MRI diagnostics activity data")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed/nhs_mri_activity.csv"))
    args = parser.parse_args()
    result = prepare(args.source, args.output)
    print(f"Saved {len(result)} MRI activity rows to {args.output}")


if __name__ == "__main__":
    main()
