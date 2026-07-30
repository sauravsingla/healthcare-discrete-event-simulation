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


def test_prepare_aggregates_mri_activity_by_source(tmp_path: Path) -> None:
    source = tmp_path / "did.csv"
    output = tmp_path / "processed.csv"
    pd.DataFrame(
        {
            "Provider Code": ["r01", "r01", "r01", "r02"],
            "Reporting Period": ["2025-04-01"] * 4,
            "Modality": ["MRI", "Magnetic Resonance Imaging", "CT", "MRI"],
            "Activity": [100, 20, 50, 10],
            "Patient Source": ["Outpatient", "Outpatient", "Emergency", "Inpatient"],
            "Median Test to Report Days": [2, 4, 1, 3],
        }
    ).to_csv(source, index=False)

    result = module.prepare(source, output)

    assert output.is_file()
    assert result.to_dict("records") == [
        {
            "provider_code": "R01",
            "period": "2025-04",
            "patient_source": "outpatient",
            "did_mri_activity": 120,
            "median_test_to_report_days": 3.0,
        },
        {
            "provider_code": "R02",
            "period": "2025-04",
            "patient_source": "inpatient",
            "did_mri_activity": 10,
            "median_test_to_report_days": 3.0,
        },
    ]


def test_standardise_source_maps_expected_categories() -> None:
    assert module.standardise_source("Outpatient clinic") == "outpatient"
    assert module.standardise_source("Admitted inpatient") == "inpatient"
    assert module.standardise_source("A&E") == "emergency"
    assert module.standardise_source("Unknown") == "other"


def test_prepare_rejects_file_without_mri_rows(tmp_path: Path) -> None:
    source = tmp_path / "did.csv"
    pd.DataFrame(
        {
            "Provider Code": ["R01"],
            "Reporting Period": ["2025-04-01"],
            "Modality": ["CT"],
            "Activity": [10],
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="No MRI rows"):
        module.prepare(source, tmp_path / "out.csv")
