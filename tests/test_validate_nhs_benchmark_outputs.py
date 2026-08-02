from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.validate_nhs_benchmark_outputs import validate


def write_valid_outputs(root: Path) -> None:
    root.mkdir(parents=True)
    benchmark = pd.DataFrame(
        {
            "provider_code": ["AAA"] * 6,
            "period": [f"2025-{month:02d}" for month in range(1, 7)],
            "actual": [100, 110, 120, 130, 140, 150],
            "predicted": [98, 108, 119, 128, 138, 148],
        }
    )
    benchmark.to_csv(root / "benchmark_input.csv", index=False)
    pd.DataFrame(
        {
            "provider_code": ["AAA"],
            "holdout_months": [2],
            "actual_total": [290.0],
            "predicted_total": [286.0],
            "wape": [4 / 290],
            "throughput_error": [4 / 290],
        }
    ).to_csv(root / "provider_scores.csv", index=False)
    (root / "run_metadata.json").write_text(
        json.dumps(
            {
                "providers": 1,
                "months": 6,
                "rows": 6,
                "national_holdout_wape": 4 / 290,
            }
        ),
        encoding="utf-8",
    )
    (root / "benchmark_report.md").write_text(
        "# NHS MRI external benchmark\n\n"
        "- National holdout WAPE: 0.0138\n\n"
        "Results are not clinical validation.\n",
        encoding="utf-8",
    )
    (root / "schema_inventory.json").write_text("[]", encoding="utf-8")


def test_validate_accepts_complete_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "benchmark"
    write_valid_outputs(output_dir)
    validate(output_dir)


def test_validate_rejects_missing_outputs(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Missing benchmark outputs"):
        validate(tmp_path)


def test_validate_rejects_too_short_history(tmp_path: Path) -> None:
    output_dir = tmp_path / "benchmark"
    write_valid_outputs(output_dir)
    metadata_path = output_dir / "run_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["months"] = 5
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="at least 6"):
        validate(output_dir)
