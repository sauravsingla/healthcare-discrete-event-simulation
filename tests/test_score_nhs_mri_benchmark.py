from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "score_nhs_mri_benchmark.py"
SPEC = importlib.util.spec_from_file_location("score_nhs_mri_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_score_uses_temporal_holdout_and_calculates_metrics(tmp_path: Path) -> None:
    source = tmp_path / "benchmark.csv"
    output_csv = tmp_path / "scores.csv"
    output_json = tmp_path / "scores.json"
    pd.DataFrame(
        {
            "provider_code": ["abc"] * 6,
            "period": [
                "2025-01",
                "2025-02",
                "2025-03",
                "2025-04",
                "2025-05",
                "2025-06",
            ],
            "actual": [100, 110, 120, 130, 140, 150],
            "predicted": [100, 108, 118, 128, 135, 155],
            "mri_scanners": [2, 2, 2, 2, 2, 2],
        }
    ).to_csv(source, index=False)

    result = module.score(
        source,
        output_csv,
        output_json,
        min_months=6,
        validation_months=2,
        holdout_months=2,
    )

    assert output_csv.is_file()
    assert output_json.is_file()
    assert result.loc[0, "provider_code"] == "ABC"
    assert result.loc[0, "holdout_months"] == 2
    assert result.loc[0, "actual_total"] == 290.0
    assert result.loc[0, "predicted_total"] == 290.0
    assert result.loc[0, "wape"] == pytest.approx(10 / 290)
    assert result.loc[0, "actual_per_scanner"] == 72.5
    metadata = json.loads(output_json.read_text())
    assert metadata["included_providers"] == 1
    assert "not clinical validation" in metadata["claim_limit"].lower()


def test_score_records_provider_exclusions(tmp_path: Path) -> None:
    source = tmp_path / "benchmark.csv"
    pd.DataFrame(
        {
            "provider_code": ["SHORT"] * 5 + ["VALID"] * 6,
            "period": [
                "2025-01",
                "2025-02",
                "2025-03",
                "2025-04",
                "2025-05",
                "2025-01",
                "2025-02",
                "2025-03",
                "2025-04",
                "2025-05",
                "2025-06",
            ],
            "actual": [10] * 11,
            "predicted": [10] * 11,
        }
    ).to_csv(source, index=False)
    output_json = tmp_path / "metadata.json"

    result = module.score(
        source,
        tmp_path / "scores.csv",
        output_json,
        min_months=6,
        validation_months=2,
        holdout_months=2,
    )

    assert result["provider_code"].tolist() == ["VALID"]
    exclusions = json.loads(output_json.read_text())["excluded_providers"]
    assert exclusions == [
        {
            "provider_code": "SHORT",
            "reason": "insufficient_months",
            "observed_months": 5,
        }
    ]


def test_score_handles_zero_actual_without_division_error(tmp_path: Path) -> None:
    source = tmp_path / "benchmark.csv"
    pd.DataFrame(
        {
            "provider_code": ["ABC"] * 6,
            "period": pd.period_range("2025-01", periods=6, freq="M").astype(str),
            "actual": [1, 1, 1, 1, 0, 0],
            "predicted": [1, 1, 1, 1, 2, 2],
        }
    ).to_csv(source, index=False)

    result = module.score(
        source,
        tmp_path / "scores.csv",
        tmp_path / "scores.json",
        min_months=6,
        validation_months=2,
        holdout_months=2,
    )

    assert pd.isna(result.loc[0, "mape"])
    assert pd.isna(result.loc[0, "annualised_throughput_error"])


def test_score_rejects_unparseable_periods(tmp_path: Path) -> None:
    source = tmp_path / "benchmark.csv"
    pd.DataFrame(
        {
            "provider_code": ["ABC"] * 6,
            "period": ["bad"] * 6,
            "actual": [1] * 6,
            "predicted": [1] * 6,
        }
    ).to_csv(source, index=False)

    with pytest.raises(ValueError, match="No valid benchmark observations"):
        module.score(source, tmp_path / "scores.csv", tmp_path / "scores.json")
