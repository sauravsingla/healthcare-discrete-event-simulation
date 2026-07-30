"""Deterministic end-to-end sanity checks using a very small simulation horizon."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from healthcare_des import AdvancedScenarioConfig, run_advanced_once, run_advanced_replications
from healthcare_des.advanced_benchmark_cli import run_benchmark


def _small_config() -> AdvancedScenarioConfig:
    return replace(
        AdvancedScenarioConfig(),
        name="small-data-sanity",
        days=1,
        daily_demand=8.0,
        mri_machines=2,
        cancellation_rate=0.0,
        no_show_rate=0.0,
        abandonment_minutes=720.0,
        bootstrap_samples=20,
        seed=101,
    )


def test_small_advanced_simulation_reconciles_patient_outcomes() -> None:
    result, patients, state = run_advanced_once(_small_config())

    assert not patients.empty
    assert not state.empty
    assert result.booked >= result.cancelled
    assert result.expected_arrivals == len(patients) - result.cancelled
    assert result.arrivals == result.completed + result.abandoned + result.unfinished
    assert result.no_shows == 0
    assert result.cancelled == 0
    assert set(patients["status"]).issubset(
        {"completed", "abandoned", "unfinished", "cancelled", "no_show"}
    )
    assert patients["patient_id"].is_unique
    assert state["time"].is_monotonic_increasing


def test_small_simulation_is_deterministic_for_same_seed() -> None:
    first_result, first_patients, first_state = run_advanced_once(_small_config())
    second_result, second_patients, second_state = run_advanced_once(_small_config())

    assert first_result == second_result
    pd.testing.assert_frame_equal(first_patients, second_patients)
    pd.testing.assert_frame_equal(first_state, second_state)


def test_small_replications_return_one_row_per_replication() -> None:
    results = run_advanced_replications(_small_config(), replications=2)

    assert len(results) == 2
    assert results["replication"].tolist() == [0, 1]
    assert (
        results["arrivals"] == results["completed"] + results["abandoned"] + results["unfinished"]
    ).all()


def test_benchmark_helper_produces_complete_small_output() -> None:
    frame = run_benchmark(days=1, replications=1)

    assert len(frame) == 18
    assert frame["scenario"].nunique() == 18
    assert (frame["elapsed_seconds"] >= 0).all()
    assert (frame["patient_rows"] > 0).all()
    assert (frame["state_rows"] > 0).all()
