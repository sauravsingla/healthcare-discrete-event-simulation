"""Normalise coded DM01 diagnostic-test values so the generic extractor can identify MRI rows."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


COLUMN_HINTS = ("modality", "diagnostic", "test", "procedure")
MRI_CODES = {"1", "01", "1.0", "01.0"}


def normalise_csv(path: Path) -> bool:
    try:
        frame = pd.read_csv(path, low_memory=False)
    except (UnicodeDecodeError, pd.errors.ParserError):
        return False

    changed = False
    for column in frame.columns:
        label = str(column).lower()
        if not any(hint in label for hint in COLUMN_HINTS):
            continue
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
    print(f"Normalised coded MRI values in {changed} CSV file(s)")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalise coded MRI values in DM01 CSV files")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    run(args.root)


if __name__ == "__main__":
    main()
