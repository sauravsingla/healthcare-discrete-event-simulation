"""Normalise coded DM01 diagnostic-test values so the generic extractor can identify MRI rows."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

COLUMN_HINTS = (
    "modality",
    "diagnostic",
    "test",
    "procedure",
    "item",
    "testtype",
    "test type",
)
MRI_CODES = {"1", "01", "1.0", "01.0"}


def _header_row(path: Path) -> int:
    preview = pd.read_csv(path, header=None, nrows=30, low_memory=False)
    best_row = 0
    best_score = -1
    for index, row in preview.iterrows():
        values = [str(value).strip().lower() for value in row if not pd.isna(value)]
        score = sum(any(hint in value for hint in COLUMN_HINTS) for value in values)
        score += sum("provider" in value or "organisation" in value for value in values)
        if score > best_score:
            best_row = int(index)
            best_score = score
    return best_row


def normalise_csv(path: Path) -> bool:
    try:
        header_row = _header_row(path)
        frame = pd.read_csv(path, header=header_row, low_memory=False)
    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
        return False

    changed = False
    candidate_columns = [
        column
        for column in frame.columns
        if any(hint in str(column).lower() for hint in COLUMN_HINTS)
    ]
    for column in candidate_columns:
        values = frame[column].astype(str).str.strip()
        mask = values.isin(MRI_CODES)
        if mask.any():
            frame.loc[mask, column] = "MRI"
            changed = True

    if changed:
        frame.to_csv(path, index=False)
    return changed


def run(root: Path) -> int:
    changed = 0
    for path in sorted(root.rglob("*.csv")):
        changed += int(normalise_csv(path))
    if changed == 0:
        raise ValueError("No coded DM01 MRI column was normalised; inspect downloaded schemas")
    print(f"Normalised coded MRI values in {changed} CSV file(s)")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalise coded MRI values in DM01 CSV files")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    run(args.root)


if __name__ == "__main__":
    main()
