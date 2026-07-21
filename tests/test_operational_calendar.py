from dataclasses import replace

import numpy as np
import pytest

from healthcare_des.model import DEFAULT_HOURLY_PROFILE, ScenarioConfig, run_once


def operational_config() -> ScenarioConfig:
    return ScenarioConfig(
        name="operations",
        days=2,
        daily_demand=24,
        outpatient_share=0.5,
        inpatient_share=0.25,
        emergency_share=0.25,
        mri_machines=2,
        clerks=2,
        radiographers=2,
        radiologists=2,
        scan_mean=10,
        scan_sd_outpatient=0,
        scan_sd_inpatient=0,
        scan_sd_emergency=0,
        seed=31,
    )


def test_hourly_profile_creates_time_varying_walk_ins() -> None:
    config = replace(
        operational_config(),
        outpatient_share=0.0,
        inpatient_share=0.5,
        emergency_share=0.5,
        hourly_arrival_profile=(8.0, 1.0, 1.0, 0.2, 0.2, 1.0, 1.0, 0.2),
    )
    _, patients = run_once(config)
    walk_ins = patients.loc[patients["patient_type"] != "outpatient"].copy()
    hours = ((walk_ins["arrival"] % 1440) // 60).astype(int)
    assert (hours == 0).sum() > (hours == 3).sum()


def test_outpatients_have_slots_and_arrival_jitter() -> None:
    config = replace(operational_config(), appointment_arrival_sd_minutes=6.0)
    _, patients = run_once(config)
    outpatients = patients.loc[patients["patient_type"] == "outpatient"]
    assert outpatients["scheduled_time"].notna().all()
    assert np.isfinite(outpatients["arrival_deviation_minutes"]).all()
    assert outpatients["arrival_deviation_minutes"].abs().max() > 0


def test_outpatient_no_shows_are_counted() -> None:
    result, _ = run_once(replace(operational_config(), no_show_rate=0.9))
    assert result.no_shows > 0
    assert result.arrivals == result.completed + result.no_shows + result.unfinished


def test_cleaning_time_increases_mri_utilisation() -> None:
    without_cleaning, _ = run_once(replace(operational_config(), cleaning_minutes=0))
    with_cleaning, _ = run_once(replace(operational_config(), cleaning_minutes=8))
    assert with_cleaning.mri_utilisation_pct > without_cleaning.mri_utilisation_pct


def test_random_failures_are_reported() -> None:
    result, _ = run_once(
        replace(
            operational_config(),
            mri_failure_probability=1.0,
            mri_repair_mean_minutes=5,
        )
    )
    assert result.mri_failures > 0
    assert result.mri_downtime_minutes > 0


def test_planned_maintenance_delays_mri_access() -> None:
    baseline, _ = run_once(operational_config())
    maintained, _ = run_once(
        replace(operational_config(), planned_mri_maintenance=((0, 120),))
    )
    assert maintained.mean_system_minutes > baseline.mean_system_minutes
    assert maintained.mri_downtime_minutes > 0


def test_staff_breaks_delay_patient_flow() -> None:
    baseline, _ = run_once(operational_config())
    with_breaks, _ = run_once(
        replace(operational_config(), staff_breaks=((0, 120),))
    )
    assert with_breaks.mean_system_minutes > baseline.mean_system_minutes


def test_shift_windows_are_validated() -> None:
    with pytest.raises(ValueError, match="Invalid clerk_shifts"):
        run_once(replace(operational_config(), clerk_shifts=((200, 100),)))


def test_hourly_profile_validation() -> None:
    with pytest.raises(ValueError, match="hourly_arrival_profile"):
        run_once(replace(operational_config(), hourly_arrival_profile=(0.0,) * 8))


def test_default_profile_has_morning_peak_and_lunch_dip() -> None:
    assert DEFAULT_HOURLY_PROFILE[1] > DEFAULT_HOURLY_PROFILE[4]
