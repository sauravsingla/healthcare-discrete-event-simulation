from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "prepare_nhs_nidc.py"
SPEC = importlib.util.spec_from_file_location("prepare_nhs_nidc", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_prepare_assets_filters_and_aggregates_mri_rows(tmp_path: Path) -> None:
    source = tmp_path / "nidc.csv"
    output = tmp_path / "assets.csv"
    pd.DataFrame(
        {
            "Organisation Code": ["abc", "abc", "abc", "xyz"],
            "Reporting Year": ["2025", "2025", "2025", "2025"],
            "Modality": ["MRI", "Magnetic Resonance", "CT", "MRI"],
            "Scanner Count": [2, 1, 10, 0],
        }
    ).to_csv(source, index=False)

    result = module.prepare_assets(source, output)

    assert output.is_file()
    assert result.to_dict("records") == [
        {
            "provider_code": "ABC",
            "reporting_year": "2025",
            "mri_scanners": 3,
            "asset_status": "valid",
        },
        {
            "provider_code": "XYZ",
            "reporting_year": "2025",
            "mri_scanners": 0,
            "asset_status": "zero",
        },
    ]


def test_prepare_assets_flags_implausible_counts(tmp_path: Path) -> None:
    source = tmp_path / "nidc.csv"
    pd.DataFrame(
        {
            "Provider Code": ["R01", "R02"],
            "Year": [2025, 2025],
            "MRI Scanner Count": [-1, 101],
        }
    ).to_csv(source, index=False)

    result = module.prepare_assets(source, tmp_path / "out.csv")

    assert result["asset_status"].tolist() == [
        "invalid_negative",
        "implausible_high",
    ]


def test_join_activity_calculates_throughput_and_missing_status(
    tmp_path: Path,
) -> None:
    activity = tmp_path / "activity.csv"
    assets = tmp_path / "assets.csv"
    output = tmp_path / "joined.csv"
    pd.DataFrame(
        {
            "provider_code": ["ABC", "XYZ"],
            "period": ["2025-04", "2025-04"],
            "mri_activity": [300.0, 120.0],
        }
    ).to_csv(activity, index=False)
    pd.DataFrame(
        {
            "provider_code": ["ABC"],
            "reporting_year": ["2025"],
            "mri_scanners": [3.0],
            "asset_status": ["valid"],
        }
    ).to_csv(assets, index=False)

    result = module.join_activity(activity, assets, output)

    assert result.loc[0, "asset_join_status"] == "matched"
    assert result.loc[0, "mri_activity_per_scanner"] == 100.0
    assert result.loc[1, "asset_join_status"] == "missing"
    assert pd.isna(result.loc[1, "mri_activity_per_scanner"])


def test_prepare_assets_rejects_non_mri_file(tmp_path: Path) -> None:
    source = tmp_path / "nidc.csv"
    pd.DataFrame(
        {
            "Provider Code": ["ABC"],
            "Year": [2025],
            "Modality": ["CT"],
            "Scanner Count": [2],
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="No MRI scanner rows"):
        module.prepare_assets(source, tmp_path / "out.csv")
