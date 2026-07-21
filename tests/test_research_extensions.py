from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from healthcare_des.calibration import calibration_metrics, calibration_table
from healthcare_des.model import ScenarioConfig
from healthcare_des.reproduction import ReproductionTarget, verify_targets
from healthcare_des.reporting import save_latex_table
from healthcare_des.tracking import config_hash, experiment_manifest, write_manifest


def test_calibration_metrics_are_correct() -> None:
    metrics = calibration_metrics([10, 20], [12, 18])
    assert metrics["mae"] == pytest.approx(2.0)
    assert metrics["rmse"] == pytest.approx(2.0)
    assert metrics["mean_error"] == pytest.approx(0.0)


def test_calibration_table_aligns_by_key() -> None:
    observed = pd.DataFrame({"month": ["a", "b"], "activity": [10, 20]})
    simulated = pd.DataFrame({"month": ["b", "a"], "activity": [19, 11]})
    table, metrics = calibration_table(observed, simulated, key="month", value="activity")
    assert len(table) == 2
    assert metrics["mae"] == pytest.approx(1.0)


def test_calibration_rejects_mismatched_shapes() -> None:
    with pytest.raises(ValueError, match="same shape"):
        calibration_metrics(np.array([1.0]), np.array([1.0, 2.0]))


def test_manifest_is_reproducible_for_same_config(tmp_path: Path) -> None:
    config = ScenarioConfig(days=2, daily_demand=10)
    assert config_hash(config) == config_hash(config)
    manifest = experiment_manifest(config, replications=3)
    assert manifest["seed"] == config.seed
    assert manifest["config_sha256"] == config_hash(config)
    path = write_manifest(tmp_path / "manifest.json", config, replications=3)
    assert path.exists()


def test_reproduction_targets_report_pass_and_failure() -> None:
    results = pd.DataFrame({"name": ["baseline"], "mean_wait_minutes": [17.5]})
    checks = verify_targets(
        results,
        (
            ReproductionTarget("baseline", "mean_wait_minutes", 17.0, 1.0),
            ReproductionTarget("missing", "mean_wait_minutes", 5.0, 1.0),
        ),
    )
    assert bool(checks.iloc[0]["passed"])
    assert not bool(checks.iloc[1]["passed"])


def test_latex_output_is_created(tmp_path: Path) -> None:
    results = pd.DataFrame(
        {
            "name": ["baseline"],
            "mean_wait_minutes": [10.0],
            "throughput_per_day": [20.0],
        }
    )
    destination = save_latex_table(results, tmp_path / "table.tex")
    assert destination.exists()
    assert "baseline" in destination.read_text(encoding="utf-8")
