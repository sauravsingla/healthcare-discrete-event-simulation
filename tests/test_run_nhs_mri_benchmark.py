from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_nhs_mri_benchmark.py"
SPEC = importlib.util.spec_from_file_location("run_nhs_mri_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _benchmark_frame() -> pd.DataFrame:
    rows = []
    for month in range(1, 9):
        rows.append(
            {
                "provider_code": "abc",
                "period": f"2025-{month:02d}",
                "actual": 100 + month,
                "predicted": 99 + month,
                "mri_scanners": 2,
            }
        )
    return pd.DataFrame(rows)


def test_run_writes_scores_metadata_and_report(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.csv"
    dm01 = tmp_path / "dm01.csv"
    did = tmp_path / "did.csv"
    nidc = tmp_path / "nidc.csv"
    _benchmark_frame().to_csv(benchmark, index=False)
    for path in (dm01, did, nidc):
        path.write_text("fixture\n", encoding="utf-8")

    config = tmp_path / "run.json"
    config.write_text(
        json.dumps(
            {
                "benchmark_input": "benchmark.csv",
                "output_dir": "results",
                "scoring": {
                    "min_months": 6,
                    "validation_months": 2,
                    "holdout_months": 2,
                },
                "sources": [
                    {"name": "DM01", "path": "dm01.csv", "release": "fixture"},
                    {"name": "DID", "path": "did.csv", "release": "fixture"},
                    {"name": "NIDC", "path": "nidc.csv", "release": "fixture"},
                ],
            }
        ),
        encoding="utf-8",
    )

    outputs = module.run(config)

    assert all(path.is_file() for path in outputs.values())
    metadata = json.loads(outputs["metadata"].read_text(encoding="utf-8"))
    assert metadata["included_providers"] == 1
    assert len(metadata["sources"]) == 3
    assert len(metadata["benchmark_input_sha256"]) == 64
    report = outputs["report"].read_text(encoding="utf-8")
    assert "ABC" in report
    assert "not clinical validation" in report


def test_run_rejects_missing_configured_source(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.csv"
    _benchmark_frame().to_csv(benchmark, index=False)
    config = tmp_path / "run.json"
    config.write_text(
        json.dumps(
            {
                "benchmark_input": "benchmark.csv",
                "sources": [{"name": "DM01", "path": "missing.csv"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="Configured source does not exist"):
        module.run(config)


def test_load_config_requires_benchmark_input(tmp_path: Path) -> None:
    config = tmp_path / "run.json"
    config.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="benchmark_input"):
        module.load_config(config)
