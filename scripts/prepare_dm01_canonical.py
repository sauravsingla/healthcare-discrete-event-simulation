"""Create canonical provider-month MRI activity CSVs from downloaded DM01 extracts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _find_column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> object | None:
    by_key = {_key(column): column for column in frame.columns}
    for candidate in candidates:
        if candidate in by_key:
            return by_key[candidate]
    for key, column in by_key.items():
        if any(candidate in key for candidate in candidates):
            return column
    return None


def _normalise_period(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    parsed = pd.to_datetime(text, errors="coerce")
    unresolved = parsed.isna() & text.str.fullmatch(r"\d{6}")
    if unresolved.any():
        parsed.loc[unresolved] = pd.to_datetime(
            text.loc[unresolved], format="%Y%m", errors="coerce"
        )
    return parsed.dt.to_period("M").astype(str)


def _read_csv(path: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path, low_memory=False)
    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
        return None


def prepare_file(path: Path, output_dir: Path) -> Path | None:
    frame = _read_csv(path)
    if frame is None or frame.empty:
        return None

    provider = _find_column(
        frame,
        ("providerorgcode", "providercode", "organisationcode", "orgcode"),
    )
    period = _find_column(frame, ("period", "month", "reportingperiod"))
    activity = _find_column(
        frame,
        ("totalactivity", "activity", "count", "tests", "value"),
    )
    if provider is None or period is None or activity is None:
        return None

    diagnostic_columns = [
        column
        for column in frame.columns
        if any(
            token in _key(column)
            for token in ("diagnostictest", "modality", "procedure", "testtype")
        )
    ]
    if not diagnostic_columns:
        return None

    mask = pd.Series(False, index=frame.index)
    for column in diagnostic_columns:
        values = frame[column].astype(str).str.strip()
        mask |= values.str.contains(
            r"\b(?:MRI|Magnetic Resonance(?: Imaging)?)\b",
            case=False,
            regex=True,
            na=False,
        )

    if not mask.any():
        for column in diagnostic_columns:
            codes = pd.to_numeric(frame[column], errors="coerce")
            mask |= codes.eq(1)

    if not mask.any():
        return None

    result = pd.DataFrame(
        {
            "provider_code": frame.loc[mask, provider],
            "period": _normalise_period(frame.loc[mask, period]),
            "modality": "MRI",
            "activity": pd.to_numeric(frame.loc[mask, activity], errors="coerce"),
        }
    )
    result["provider_code"] = result["provider_code"].astype(str).str.strip().str.upper()
    result = result.dropna(subset=["activity"])
    result = result[
        result["provider_code"].ne("")
        & result["provider_code"].ne("NAN")
        & result["period"].ne("NaT")
    ]
    result = result.groupby(
        ["provider_code", "period", "modality"], as_index=False
    )["activity"].sum()
    if result.empty:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{path.stem}_canonical.csv"
    result.to_csv(target, index=False)
    return target


def run(root: Path, output_dir: Path) -> int:
    written = [
        target
        for path in sorted(root.rglob("*.csv"))
        if output_dir not in path.parents
        if (target := prepare_file(path, output_dir)) is not None
    ]
    if len(written) < 6:
        raise ValueError(
            f"Only {len(written)} canonical DM01 monthly files were created; "
            "at least 6 are required"
        )
    print(f"Created {len(written)} canonical DM01 MRI files in {output_dir}")
    return len(written)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare canonical DM01 MRI activity files")
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/nhs_public/canonical_dm01"),
    )
    args = parser.parse_args()
    run(args.root, args.output_dir)


if __name__ == "__main__":
    main()
