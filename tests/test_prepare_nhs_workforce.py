from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "prepare_nhs_workforce.py"
SPEC = importlib.util.spec_from_file_location("prepare_nhs_workforce", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_prepare_workforce_filters_and_aggregates(tmp_path: Path) -> None:
    source = tmp_path / "workforce.csv"
    output = tmp_path / "prepared.csv"
    pd.DataFrame(
        {
            "Organisation Code": ["abc", "abc", "abc", "xyz"],
            "Reporting Year": ["2025", "2025", "2025", "2025"],
            "Staff Group": [
                "Diagnostic Radiography",
                "Imaging Support",
                "Nursing",
                "Radiology",
            ],
            "FTE": [10.0, 2.0, 20.0, 0.0],
        }
    ).to_csv(source, index=False)

    result = module.prepare_workforce(source, output)

    assert output.is_file()
    assert result.to_dict("records") == [
        {
            "provider_code": "ABC",
            "reporting_year": "2025",
            "imaging_workforce_fte": 12.0,
            "workforce_status": "valid",
        },
        {
            "provider_code": "XYZ",
            "reporting_year": "2025",
            "imaging_workforce_fte": 0.0,
            "workforce_status": "zero",
        },
    ]


def test_prepare_workforce_flags_invalid_values(tmp_path: Path) -> None:
    source = tmp_path / "workforce.csv"
    pd.DataFrame(
        {
            "Provider Code": ["R01", "R02"],
            "Year": [2025, 2025],
            "Workforce Count": [-1, 10001],
        }
    ).to_csv(source, index=False)

    result = module.prepare_workforce(source, tmp_path / "out.csv")

    assert result["workforce_status"].tolist() == [
        "invalid_negative",
        "implausible_high",
    ]


def test_join_benchmark_adds_workforce_metrics(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.csv"
    workforce = tmp_path / "workforce.csv"
    output = tmp_path / "joined.csv"
    pd.DataFrame(
        {
            "provider_code": ["ABC", "XYZ"],
            "period": ["2025-04", "2025-04"],
            "mri_activity": [300.0, 120.0],
            "mri_scanners": [3.0, 2.0],
            "backlog": [60.0, 30.0],
        }
    ).to_csv(benchmark, index=False)
    pd.DataFrame(
        {
            "provider_code": ["ABC"],
            "reporting_year": ["2025"],
            "imaging_workforce_fte": [12.0],
            "workforce_status": ["valid"],
        }
    ).to_csv(workforce, index=False)

    result = module.join_benchmark(benchmark, workforce, output)

    assert result.loc[0, "workforce_join_status"] == "matched"
    assert result.loc[0, "mri_activity_per_workforce_fte"] == 25.0
    assert result.loc[0, "scanners_per_workforce_fte"] == 0.25
    assert result.loc[0, "backlog_per_workforce_fte"] == 5.0
    assert result.loc[1, "workforce_join_status"] == "missing"
    assert pd.isna(result.loc[1, "mri_activity_per_workforce_fte"])


def test_prepare_workforce_rejects_non_imaging_categories(tmp_path: Path) -> None:
    source = tmp_path / "workforce.csv"
    pd.DataFrame(
        {
            "Provider Code": ["ABC"],
            "Year": [2025],
            "Staff Group": ["Nursing"],
            "FTE": [5.0],
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="No imaging workforce rows"):
        module.prepare_workforce(source, tmp_path / "out.csv")
