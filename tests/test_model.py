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


def test_stage_waits_sum_to_total_wait() -> None:
    _, patients = run_once(small_config())
    stage_total = patients[
        [
            "reception_wait_minutes",
            "preparation_wait_minutes",
            "mri_wait_minutes",
            "reporting_wait_minutes",
        ]
    ].sum(axis=1)
    pd.testing.assert_series_equal(
        patients["wait_minutes"], stage_total, check_names=False
    )


def test_resource_utilisation_metrics_are_valid() -> None:
    result, _ = run_once(small_config())
    utilisation = (
        result.clerk_utilisation_pct,
        result.radiographer_utilisation_pct,
        result.mri_utilisation_pct,
        result.radiologist_utilisation_pct,
    )
    assert all(0 <= value <= 100 for value in utilisation)
    assert result.mri_utilisation_pct > 0


def test_summary_includes_diagnostic_metrics() -> None:
    summary = summarise(run_replications(small_config(), replications=2))
    expected = {
        "mean_reception_wait_minutes",
        "mean_preparation_wait_minutes",
        "mean_mri_wait_minutes",
        "mean_reporting_wait_minutes",
        "clerk_utilisation_pct",
        "radiographer_utilisation_pct",
        "mri_utilisation_pct",
        "radiologist_utilisation_pct",
    }
    assert expected <= summary.keys()


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


def test_negative_patient_share_is_rejected() -> None:
    config = replace(
        small_config(),
        outpatient_share=-0.1,
        inpatient_share=0.5,
        emergency_share=0.6,
    )
    with pytest.raises(ValueError, match="non-negative"):
        run_once(config)


@pytest.mark.parametrize("daily_demand", [0.0, -1.0])
def test_daily_demand_must_be_positive(daily_demand: float) -> None:
    with pytest.raises(ValueError, match="daily_demand must be positive"):
        run_once(replace(small_config(), daily_demand=daily_demand))


@pytest.mark.parametrize("operating_hours", [0, 25])
def test_operating_hours_must_fit_within_a_day(operating_hours: int) -> None:
    with pytest.raises(ValueError, match="operating_hours must be in"):
        run_once(replace(small_config(), operating_hours=operating_hours))


def test_invalid_preparation_distribution_is_rejected() -> None:
    with pytest.raises(ValueError, match="Preparation times"):
        run_once(replace(small_config(), preparation_low=7, preparation_mode=5))


def test_negative_scan_variability_is_rejected() -> None:
    with pytest.raises(ValueError, match="standard deviations"):
        run_once(replace(small_config(), scan_sd_emergency=-1))


def test_invalid_report_distribution_is_rejected() -> None:
    with pytest.raises(ValueError, match="Report times"):
        run_once(replace(small_config(), report_low=15, report_high=10))


def test_replication_count_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        run_replications(small_config(), replications=0)
