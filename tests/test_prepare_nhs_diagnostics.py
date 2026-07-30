from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "prepare_nhs_diagnostics.py"
SPEC = importlib.util.spec_from_file_location("prepare_nhs_diagnostics", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_prepare_aggregates_provider_month_mri_rows(tmp_path: Path) -> None:
    source = tmp_path / "dm01.csv"
    output = tmp_path / "processed.csv"
    pd.DataFrame(
        {
            "Provider Code": ["abc", "abc", "xyz", "abc"],
            "Provider Name": ["Alpha", "Alpha", "Xray", "Alpha"],
            "Month": ["2025-04-01", "2025-04-01", "2025-04-01", "2025-04-01"],
            "Test Name": ["MRI", "Magnetic Resonance Imaging", "CT", "MRI"],
            "Activity": [100, 20, 50, "invalid"],
            "Patients Waiting": [8, 2, 4, 1],
        }
    ).to_csv(source, index=False)

    result = module.prepare(source, output)

    assert output.is_file()
    assert result.to_dict("records") == [
        {
            "provider_code": "ABC",
            "period": "2025-04",
            "provider_name": "Alpha",
            "mri_activity": 120.0,
            "mri_waiting_list": 10.0,
            "activity_per_calendar_day": 4.0,
        }
    ]


def test_prepare_supports_year_and_month_columns(tmp_path: Path) -> None:
    source = tmp_path / "dm01.csv"
    pd.DataFrame(
        {
            "Organisation Code": ["R01"],
            "Year": [2025],
            "Month Number": [5],
            "Modality": ["MRI"],
            "Total Tests": [31],
        }
    ).to_csv(source, index=False)

    result = module.prepare(source, tmp_path / "out.csv")

    assert result.loc[0, "period"] == "2025-05"
    assert result.loc[0, "activity_per_calendar_day"] == 1.0


def test_prepare_rejects_file_without_mri_rows(tmp_path: Path) -> None:
    source = tmp_path / "dm01.csv"
    pd.DataFrame(
        {
            "Provider Code": ["ABC"],
            "Month": ["2025-04-01"],
            "Test": ["CT"],
            "Activity": [10],
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="No MRI activity"):
        module.prepare(source, tmp_path / "out.csv")
