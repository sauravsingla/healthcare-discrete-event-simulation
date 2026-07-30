"""Prepare NHS NIDC MRI asset data and join it to activity benchmarks."""

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
    """Return the first column containing every keyword in an alternative."""
    normalised = {column: normalise_name(column) for column in columns}
    for keywords in alternatives:
        for column, value in normalised.items():
            if all(keyword in value for keyword in keywords):
                return column
    if required:
        raise ValueError(f"Could not identify column matching any of: {alternatives}")
    return None


def prepare_assets(source: Path, output: Path) -> pd.DataFrame:
    """Create a deterministic provider-year MRI scanner asset table."""
    frame = pd.read_csv(source, low_memory=False)
    columns = list(frame.columns)

    provider_col = find_column(
        columns,
        (("provider", "code"), ("organisation", "code"), ("org", "code")),
    )
    year_col = find_column(
        columns,
        (("reporting", "year"), ("financial", "year"), ("year",)),
    )
    scanner_col = find_column(
        columns,
        (
            ("mri", "scanner", "count"),
            ("mri", "scanners"),
            ("scanner", "count"),
            ("number", "scanners"),
        ),
    )
    modality_col = find_column(
        columns,
        (("modality",), ("asset", "type"), ("equipment", "type")),
        required=False,
    )

    assets = frame.copy()
    if modality_col is not None:
        assets = assets[
            assets[modality_col]
            .astype(str)
            .str.contains(MRI_PATTERN, case=False, na=False, regex=True)
        ].copy()
    if assets.empty:
        raise ValueError("No MRI scanner rows found in the supplied NIDC file")

    assets["provider_code"] = (
        assets[provider_col].astype(str).str.strip().str.upper()
    )
    assets["reporting_year"] = assets[year_col].astype(str).str.strip()
    assets["mri_scanners"] = pd.to_numeric(assets[scanner_col], errors="coerce")
    assets = assets.dropna(subset=["mri_scanners"])
    assets = assets[
        assets["provider_code"].ne("") & assets["reporting_year"].ne("")
    ]
    if assets.empty:
        raise ValueError("No valid provider-year MRI scanner rows remain after cleaning")

    result = (
        assets.groupby(["provider_code", "reporting_year"], as_index=False)
        .agg(mri_scanners=("mri_scanners", "sum"))
        .sort_values(["provider_code", "reporting_year"], ignore_index=True)
    )
    result["asset_status"] = "valid"
    result.loc[result["mri_scanners"].eq(0), "asset_status"] = "zero"
    result.loc[result["mri_scanners"].lt(0), "asset_status"] = "invalid_negative"
    result.loc[result["mri_scanners"].gt(100), "asset_status"] = "implausible_high"

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def join_activity(
    activity_source: Path,
    assets_source: Path,
    output: Path,
) -> pd.DataFrame:
    """Join provider-month activity to provider-year scanner assets."""
    activity = pd.read_csv(activity_source, low_memory=False)
    assets = pd.read_csv(assets_source, low_memory=False)

    required_activity = {"provider_code", "period", "mri_activity"}
    required_assets = {"provider_code", "reporting_year", "mri_scanners"}
    if not required_activity.issubset(activity.columns):
        missing = sorted(required_activity.difference(activity.columns))
        raise ValueError(f"Activity file is missing required columns: {missing}")
    if not required_assets.issubset(assets.columns):
        missing = sorted(required_assets.difference(assets.columns))
        raise ValueError(f"Asset file is missing required columns: {missing}")

    activity = activity.copy()
    assets = assets.copy()
    activity["provider_code"] = (
        activity["provider_code"].astype(str).str.strip().str.upper()
    )
    assets["provider_code"] = (
        assets["provider_code"].astype(str).str.strip().str.upper()
    )
    activity["reporting_year"] = activity["period"].astype(str).str[:4]
    assets["reporting_year"] = assets["reporting_year"].astype(str).str[:4]

    result = activity.merge(
        assets,
        on=["provider_code", "reporting_year"],
        how="left",
        validate="many_to_one",
    )
    result["asset_join_status"] = result["mri_scanners"].notna().map(
        {True: "matched", False: "missing"}
    )
    valid_scanners = result["mri_scanners"].gt(0)
    result["mri_activity_per_scanner"] = pd.NA
    result.loc[valid_scanners, "mri_activity_per_scanner"] = (
        result.loc[valid_scanners, "mri_activity"]
        / result.loc[valid_scanners, "mri_scanners"]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare NIDC MRI assets and optionally join provider activity"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    assets_parser = subparsers.add_parser("assets")
    assets_parser.add_argument("source", type=Path)
    assets_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_nidc_mri_assets.csv"),
    )

    join_parser = subparsers.add_parser("join")
    join_parser.add_argument("activity", type=Path)
    join_parser.add_argument("assets", type=Path)
    join_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/nhs_mri_activity_with_assets.csv"),
    )

    args = parser.parse_args()
    if args.command == "assets":
        result = prepare_assets(args.source, args.output)
    else:
        result = join_activity(args.activity, args.assets, args.output)
    print(f"Saved {len(result)} rows to {args.output}")


if __name__ == "__main__":
    main()
