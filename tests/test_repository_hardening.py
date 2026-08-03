from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from healthcare_des import calibration, cli, config, performance, reporting
from healthcare_des.model import ScenarioConfig


def test_load_config_and_calibrate_daily_demand(tmp_path: Path) -> None:
    config_path = tmp_path / "scenario.yaml"
    config_path.write_text("name: hardening-test\ndays: 2\n", encoding="utf-8")
    loaded = config.load_config(config_path)
    assert loaded.name == "hardening-test"
    assert loaded.days == 2

    activity_path = tmp_path / "activity.csv"
    pd.DataFrame({"activity": [304.375, 608.75]}).to_csv(activity_path, index=False)
    assert config.calibrate_daily_demand(activity_path) == pytest.approx(15.0)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ("- item\n", "YAML mapping"),
        ("unknown_setting: 1\n", "Unknown scenario settings"),
    ],
)
def test_load_config_rejects_invalid_yaml(tmp_path: Path, payload: str, error: str) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        config.load_config(path)


def test_calibrate_daily_demand_validation(tmp_path: Path) -> None:
    missing_column = tmp_path / "missing.csv"
    pd.DataFrame({"other": [1]}).to_csv(missing_column, index=False)
    with pytest.raises(ValueError, match="Missing required column"):
        config.calibrate_daily_demand(missing_column)

    invalid = tmp_path / "invalid.csv"
    pd.DataFrame({"activity": [0, -1]}).to_csv(invalid, index=False)
    with pytest.raises(ValueError, match="positive numbers"):
        config.calibrate_daily_demand(invalid)


def test_cli_parser_and_positive_integer() -> None:
    assert cli.positive_int("3") == 3
    with pytest.raises(argparse.ArgumentTypeError):
        cli.positive_int("0")
    parsed = cli.build_parser().parse_args(["--config", "scenario.yaml"])
    assert parsed.replications == 20
    assert parsed.output == "outputs/results.csv"


def test_cli_main_writes_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    scenario = ScenarioConfig(name="cli-test", days=1, daily_demand=1)
    output = tmp_path / "result.csv"
    frame = pd.DataFrame([{"name": "cli-test", "replication": 0, "mean_wait_minutes": 1.0}])
    monkeypatch.setattr(cli, "load_config", lambda _: scenario)
    monkeypatch.setattr(cli, "run_replications", lambda _config, _reps: frame)
    monkeypatch.setattr(cli, "summarise", lambda _frame: {"rows": len(_frame)})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "healthcare-des",
            "--config",
            "unused.yaml",
            "--replications",
            "1",
            "--output",
            str(output),
        ],
    )
    cli.main()
    assert output.is_file()
    assert '"rows": 1' in capsys.readouterr().out


def test_calibration_metrics_table_and_plot(tmp_path: Path) -> None:
    metrics = calibration.calibration_metrics([10, 20], [12, 18])
    assert metrics["mae"] == pytest.approx(2.0)
    assert metrics["mean_error"] == pytest.approx(0.0)
    assert np.isfinite(metrics["rmse"])

    observed = pd.DataFrame({"month": ["a", "b"], "activity": [10, 20]})
    simulated = pd.DataFrame({"month": ["a", "b"], "activity": [11, 19]})
    table, table_metrics = calibration.calibration_table(
        observed, simulated, key="month", value="activity"
    )
    assert list(table["error"]) == [1, -1]
    assert table_metrics["mae"] == pytest.approx(1.0)
    assert calibration.save_calibration_plot(
        table, tmp_path / "calibration.png", x="month"
    ).is_file()

    with pytest.raises(ValueError, match="same shape"):
        calibration.calibration_metrics([1], [1, 2])
    with pytest.raises(ValueError, match="must not be empty"):
        calibration.calibration_metrics([], [])


def test_reporting_outputs_and_validation(tmp_path: Path) -> None:
    results = pd.DataFrame(
        {
            "name": ["baseline", "capacity"],
            "mean_wait_minutes": [12.0, 6.0],
            "throughput_per_day": [30.0, 35.0],
            "completed_within_120_pct": [80.0, 90.0],
            "mri_utilisation_pct": [75.0, 70.0],
        }
    )
    assert reporting.save_scenario_figure(results, tmp_path / "scenario.png").is_file()
    assert reporting.save_latex_table(results, tmp_path / "scenario.tex").is_file()
    assert reporting.save_pdf_report(results, tmp_path / "scenario.pdf").is_file()
    with pytest.raises(ValueError, match="Missing reporting columns"):
        reporting.save_scenario_figure(pd.DataFrame({"name": ["x"]}), tmp_path / "bad.png")


def test_parallel_replication_validation_and_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    class InlineExecutor:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def map(self, function, arguments):
            return [function(argument) for argument in arguments]

    monkeypatch.setattr(performance, "ProcessPoolExecutor", InlineExecutor)
    scenario = replace(ScenarioConfig(), days=1, daily_demand=1, seed=7)
    result = performance.run_replications_parallel(scenario, replications=2, workers=1)
    assert len(result) == 2
    assert set(result["replication"]) == {0, 1}

    with pytest.raises(ValueError, match="replications must be positive"):
        performance.run_replications_parallel(scenario, replications=0)
    with pytest.raises(ValueError, match="workers must be positive"):
        performance.run_replications_parallel(scenario, replications=1, workers=0)
