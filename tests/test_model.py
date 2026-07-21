from dataclasses import replace

import pandas as pd
import pytest

from healthcare_des.model import ScenarioConfig, run_once, run_replications, summarise


def small_config() -> ScenarioConfig:
    return ScenarioConfig(name="test", days=2, daily_demand=16, seed=11)


def test_simulation_is_deterministic_for_same_seed() -> None:
    first, first_patients = run_once(small_config(), replication=0)
    second, second_patients = run_once(small_config(), replication=0)
    assert first == second
    pd.testing.assert_frame_equal(first_patients, second_patients)


def test_replication_produces_valid_metrics() -> None:
    results = run_replications(small_config(), replications=3)
    assert len(results) == 3
    assert (results["completed"] > 0).all()
    assert (results["mean_wait_minutes"] >= 0).all()
    assert results["completed_within_120_pct"].between(0, 100).all()
    assert summarise(results)["throughput_per_day"] > 0


def test_emergency_priority_configuration_runs() -> None:
    config = replace(
        small_config(),
        outpatient_share=0.2,
        inpatient_share=0.2,
        emergency_share=0.6,
        mri_machines=1,
    )
    result, patients = run_once(config)
    assert result.completed == len(patients)
    assert set(patients["patient_type"]) <= {"outpatient", "inpatient", "emergency"}


def test_invalid_patient_shares_are_rejected() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        run_once(replace(small_config(), outpatient_share=0.9))


def test_replication_count_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        run_replications(small_config(), replications=0)
