"""Cross-cutting invariants for the base discrete-event simulation."""

from dataclasses import replace

import pandas as pd
import pytest

from healthcare_des.model import ScenarioConfig, run_once


def invariant_config() -> ScenarioConfig:
    return ScenarioConfig(
        name="invariant-check",
        days=4,
        daily_demand=36,
        mri_machines=2,
        clerks=1,
        radiographers=2,
        radiologists=1,
        seed=2026,
    )


def test_lifecycle_conservation_holds_for_multiple_replications() -> None:
    config = invariant_config()
    for replication in range(5):
        result, patients = run_once(config, replication=replication)
        assert result.arrivals == result.completed + result.no_shows + result.unfinished
        assert result.completed == len(patients)


def test_all_reported_patient_durations_are_non_negative() -> None:
    _, patients = run_once(invariant_config())
    duration_columns = [
        "reception_wait_minutes",
        "preparation_wait_minutes",
        "mri_wait_minutes",
        "reporting_wait_minutes",
        "wait_minutes",
        "system_minutes",
    ]
    assert set(duration_columns) <= set(patients.columns)
    assert (patients[duration_columns].fillna(0) >= 0).all().all()


def test_arrival_deviation_can_be_early_or_late() -> None:
    _, patients = run_once(invariant_config())
    if "arrival_deviation_minutes" in patients:
        assert patients["arrival_deviation_minutes"].notna().all()
        assert (patients["arrival_deviation_minutes"] < 0).any()
        assert (patients["arrival_deviation_minutes"] > 0).any()


def test_total_wait_equals_sum_of_stage_waits() -> None:
    _, patients = run_once(invariant_config())
    stage_columns = [
        "reception_wait_minutes",
        "preparation_wait_minutes",
        "mri_wait_minutes",
        "reporting_wait_minutes",
    ]
    expected = patients[stage_columns].sum(axis=1)
    pd.testing.assert_series_equal(
        patients["wait_minutes"], expected, check_names=False, rtol=1e-12, atol=1e-12
    )


def test_system_time_is_not_less_than_waiting_time() -> None:
    _, patients = run_once(invariant_config())
    assert (patients["system_minutes"] >= patients["wait_minutes"]).all()


def test_metric_percentages_are_bounded() -> None:
    result, _ = run_once(invariant_config())
    bounded_metrics = [
        result.completion_rate_pct,
        result.completed_within_120_pct,
        result.outpatient_completed_within_120_pct,
        result.inpatient_completed_within_120_pct,
        result.emergency_completed_within_120_pct,
    ]
    assert all(0 <= value <= 100 for value in bounded_metrics)


def test_resource_utilisation_is_non_negative_and_finite() -> None:
    result, _ = run_once(invariant_config())
    utilisation = [
        result.clerk_utilisation_pct,
        result.radiographer_utilisation_pct,
        result.mri_utilisation_pct,
        result.radiologist_utilisation_pct,
    ]
    assert all(value >= 0 for value in utilisation)
    assert all(value < float("inf") for value in utilisation)


def test_same_seed_and_replication_reproduce_identical_outputs() -> None:
    first_result, first_patients = run_once(invariant_config(), replication=3)
    second_result, second_patients = run_once(invariant_config(), replication=3)
    assert first_result == second_result
    pd.testing.assert_frame_equal(first_patients, second_patients)


def test_replication_offset_changes_stochastic_output() -> None:
    first_result, first_patients = run_once(invariant_config(), replication=0)
    second_result, second_patients = run_once(invariant_config(), replication=1)
    assert first_result != second_result or not first_patients.equals(second_patients)


def test_warmup_filters_measured_arrivals() -> None:
    config = replace(invariant_config(), days=5, warmup_days=2)
    _, patients = run_once(config)
    assert (patients["arrival"] >= 2 * 1440).all()


def test_full_drain_leaves_no_unfinished_patients() -> None:
    config = replace(invariant_config(), days=2, daily_demand=60, drain_until_empty=True)
    result, _ = run_once(config)
    assert result.unfinished == 0
    assert result.completed + result.no_shows == result.arrivals


def test_invalid_shift_window_is_rejected() -> None:
    config = replace(invariant_config(), clerk_shifts=((300, 200),))
    with pytest.raises(ValueError, match="Invalid clerk_shifts window"):
        run_once(config)
