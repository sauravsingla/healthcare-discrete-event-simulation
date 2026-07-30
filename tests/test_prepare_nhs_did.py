from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "prepare_nhs_did.py"
SPEC = importlib.util.spec_from_file_location("prepare_nhs_did", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_prepare_aggregates_mri_by_provider_period_and_source(tmp_path: Path) -> None:
    source = tmp_path / "did.csv"
    output = tmp_path / "processed.csv"
    pd.DataFrame(
        {
            "Provider Code": ["abc", "abc", "abc", "xyz"],
            "Provider Name": ["Alpha", "Alpha", "Alpha", "Other"],
            "Reporting Period": ["2025-04", "2025-04", "2025-04", "2025-04"],
            "Modality": ["MRI", "Magnetic Resonance Imaging", "CT", "MRI"],
            "Patient Source": ["Outpatient", "Outpatient", "Emergency", "Inpatient"],
            "Activity": [100, 20, 50, "invalid"],
            "Request to Test Days": [12, 18, 2, 3],
            "Test to Report Days": [2, 4, 1, 2],
        }
    ).to_csv(source, index=False)

    result = module.prepare(source, output)

    assert output.is_file()
    assert result.to_dict("records") == [
        {
            "provider_code": "ABC",
            "period": "2025-04",
            "patient_source": "outpatient",
            "provider_name": "Alpha",
            "mri_activity": 120.0,
            "request_to_test_days": 15.0,
            "test_to_report_days": 3.0,
        }
    ]


def test_prepare_supports_year_month_and_default_source(tmp_path: Path) -> None:
    source = tmp_path / "did.csv"
    pd.DataFrame(
        {
            "Organisation Code": ["R01"],
            "Year": [2025],
            "Month Number": [5],
            "Imaging Type": ["MRI"],
            "Examinations": [31],
        }
    ).to_csv(source, index=False)

    result = module.prepare(source, tmp_path / "out.csv")

    assert result.loc[0, "period"] == "2025-05"
    assert result.loc[0, "patient_source"] == "all"
    assert result.loc[0, "mri_activity"] == 31.0


def test_prepare_rejects_file_without_mri_rows(tmp_path: Path) -> None:
    source = tmp_path / "did.csv"
    pd.DataFrame(
        {
            "Provider Code": ["ABC"],
            "Month": ["2025-04-01"],
            "Modality": ["CT"],
            "Activity": [10],
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="No MRI activity"):
        module.prepare(source, tmp_path / "out.csv")
