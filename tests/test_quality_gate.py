from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
import pytest

from healthcare_des import reproduction_cli
from healthcare_des.research_validation import (
    confidence_interval,
    equivalence_report,
    fit_distributions,
    fit_hourly_profile,
    save_distribution_plots,
)


def test_reproduction_cli_positive_int_validation() -> None:
    assert reproduction_cli.positive_int("3") == 3
    with pytest.raises(argparse.ArgumentTypeError, match="positive"):
        reproduction_cli.positive_int("0")


def test_reproduction_cli_main_writes_outputs(monkeypatch, tmp_path, capsys) -> None:
    config = object()
    results = pd.DataFrame({"name": ["baseline"], "throughput": [10.0]})
    checks = pd.DataFrame({"scenario": ["baseline"], "passed": [True]})
    recorded: dict[str, object] = {}

    monkeypatch.setattr(reproduction_cli, "load_config", lambda path: config)
    monkeypatch.setattr(
        reproduction_cli,
        "reproduce_paper",
        lambda supplied, replications: (results, checks),
    )
    monkeypatch.setattr(
        reproduction_cli,
        "save_scenario_figure",
        lambda frame, path: recorded.setdefault("figure", path),
    )
    monkeypatch.setattr(
        reproduction_cli,
        "save_latex_table",
        lambda frame, path: recorded.setdefault("latex", path),
    )
    monkeypatch.setattr(
        reproduction_cli,
        "save_pdf_report",
        lambda frame, path, title: recorded.setdefault("pdf", (path, title)),
    )
    monkeypatch.setattr(
        reproduction_cli,
        "write_manifest",
        lambda path, supplied, **kwargs: recorded.setdefault("manifest", (path, kwargs)),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "healthcare-des-reproduce",
            "--config",
            "scenario.yaml",
            "--replications",
            "2",
            "--output-dir",
            str(tmp_path),
        ],
    )

    reproduction_cli.main()

    assert (tmp_path / "scenario_results.csv").is_file()
    assert (tmp_path / "target_checks.csv").is_file()
    assert "baseline" in capsys.readouterr().out
    assert recorded["figure"] == tmp_path / "scenario_tradeoff.png"
    assert recorded["latex"] == tmp_path / "scenario_table.tex"
    assert recorded["pdf"] == (
        tmp_path / "reproduction_report.pdf",
        "Paper Reproduction Report",
    )
    manifest_path, manifest_kwargs = recorded["manifest"]
    assert manifest_path == tmp_path / "manifest.json"
    assert manifest_kwargs["replications"] == 2
    assert manifest_kwargs["extra"] == {"all_targets_passed": True}


def test_reproduction_cli_exits_when_targets_fail(monkeypatch, tmp_path) -> None:
    results = pd.DataFrame({"name": ["baseline"]})
    checks = pd.DataFrame({"scenario": ["baseline"], "passed": [False]})
    monkeypatch.setattr(reproduction_cli, "load_config", lambda path: object())
    monkeypatch.setattr(
        reproduction_cli,
        "reproduce_paper",
        lambda config, replications: (results, checks),
    )
    monkeypatch.setattr(reproduction_cli, "save_scenario_figure", lambda *args: None)
    monkeypatch.setattr(reproduction_cli, "save_latex_table", lambda *args: None)
    monkeypatch.setattr(reproduction_cli, "save_pdf_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(reproduction_cli, "write_manifest", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["healthcare-des-reproduce", "--config", "scenario.yaml", "--output-dir", str(tmp_path)],
    )
    with pytest.raises(SystemExit) as exc:
        reproduction_cli.main()
    assert exc.value.code == 1


def test_distribution_plots_are_created(tmp_path) -> None:
    rng = np.random.default_rng(8)
    values = rng.exponential(5.0, 64)
    qq_path, density_path = save_distribution_plots(values, "expon", tmp_path, prefix="scan")
    assert qq_path.is_file()
    assert density_path.is_file()
    assert qq_path.name == "scan_expon_qq.png"
    assert density_path.name == "scan_expon_density.png"


def test_research_validation_rejects_invalid_inputs() -> None:
    valid = pd.DataFrame({"timestamp": ["2026-01-01 08:00"], "count": [1]})

    with pytest.raises(ValueError, match="Missing timestamp"):
        fit_hourly_profile(pd.DataFrame({"other": [1]}))
    with pytest.raises(ValueError, match="operating_hours"):
        fit_hourly_profile(valid, operating_hours=0)
    with pytest.raises(ValueError, match="Missing count"):
        fit_hourly_profile(valid, count_column="missing")
    with pytest.raises(ValueError, match="finite and non-negative"):
        fit_hourly_profile(
            pd.DataFrame({"timestamp": ["2026-01-01 08:00"], "count": [-1]}),
            count_column="count",
        )
    with pytest.raises(ValueError, match="No activity"):
        fit_hourly_profile(
            pd.DataFrame({"timestamp": ["2026-01-01 23:00"]}),
            operating_hours=1,
            smoothing=0,
        )
    with pytest.raises(ValueError, match="At least two"):
        confidence_interval([1.0])
    with pytest.raises(ValueError, match="positive equivalence"):
        equivalence_report([1.0, 2.0], [1.0, 2.0], 0)
    with pytest.raises(ValueError, match="At least eight"):
        fit_distributions([1.0, 2.0])
    with pytest.raises(ValueError, match="Unknown scipy"):
        fit_distributions(range(8), candidates=("not_a_distribution",))
