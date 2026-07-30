from dataclasses import replace

import pandas as pd
import pytest

from healthcare_des.advanced_model import (
    AdvancedScenarioConfig,
    CapacityWindow,
    MachineWindow,
    run_advanced_once,
)
from healthcare_des.paper_scenarios import run_paper_scenarios, verify_paper_targets


def small_config(**changes):
    base = AdvancedScenarioConfig(days=2, daily_demand=18, mri_machines=2, seed=3)
    return replace(base, **changes)


def test_dynamic_capacity_by_shift_changes_state():
    config = small_config(
        radiographer_capacity=(CapacityWindow(0, 120, 2), CapacityWindow(120, 480, 1))
    )
    _, _, state = run_advanced_once(config)
    assert state["radiographer_tokens"].max() >= 2
    assert state["radiographer_tokens"].min() <= 1


def test_machine_specific_maintenance_reduces_available_count():
    config = small_config(machine_maintenance=(MachineWindow(0, 30, 120),))
    result, _, state = run_advanced_once(config)
    during = state.loc[(state["time"] >= 30) & (state["time"] < 120)]
    assert during["mri_available"].min() <= 1
    assert result.mri_downtime_minutes >= 90


def test_machine_failures_are_recorded():
    config = small_config(machine_mtbf_minutes=(15.0, 15.0), machine_repair_mean_minutes=5)
    result, _, _ = run_advanced_once(config)
    assert result.mri_failures > 0
    assert result.mri_downtime_minutes > 0


def test_queue_and_resource_state_tracking_is_returned():
    _, _, state = run_advanced_once(small_config(tracking_interval_minutes=10))
    assert {"mri_queue", "mri_busy", "mri_available", "clerk_tokens"}.issubset(state.columns)
    assert state["time"].is_monotonic_increasing


def test_capacity_aware_scheduler_limits_outpatient_slots():
    config = small_config(daily_demand=500, mri_machines=1, overbooking_rate=0)
    result, frame, _ = run_advanced_once(config)
    outpatient = frame.loc[frame["patient_type"] == "outpatient"]
    theoretical_daily_capacity = int(
        config.operating_hours * 60 / (config.scan_mean + config.cleaning_minutes)
    )
    assert len(outpatient) <= theoretical_daily_capacity * config.days
    assert result.arrivals >= result.completed


def test_emergencies_can_arrive_outside_outpatient_hours():
    config = small_config(
        operating_hours=8, emergency_share=0.8, outpatient_share=0.1, inpatient_share=0.1
    )
    _, frame, _ = run_advanced_once(config)
    emergency = frame.loc[frame["patient_type"] == "emergency"]
    assert ((emergency["arrival"] % 1440) >= 480).any()


def test_cancellation_no_show_and_abandonment_accounting():
    config = small_config(
        cancellation_rate=0.4, no_show_rate=0.4, abandonment_minutes=0.01, daily_demand=40
    )
    result, _, _ = run_advanced_once(config)
    assert result.cancelled + result.no_shows + result.abandoned > 0


def test_weekday_and_seasonal_profiles_validate():
    with pytest.raises(ValueError):
        replace(small_config(), weekday_multipliers=(1.0,)).validate()
    with pytest.raises(ValueError):
        replace(small_config(), seasonal_multipliers=(1.0,)).validate()


def test_paper_registry_runs_all_eleven_scenarios():
    results = run_paper_scenarios(small_config(days=1, daily_demand=8), replications=1)
    assert len(results) == 11
    assert results["name"].is_unique


def test_paper_target_verification(tmp_path):
    results = pd.DataFrame([{"name": "scenario-01-baseline", "throughput_per_day": 10.0}])
    targets = tmp_path / "targets.csv"
    pd.DataFrame(
        [
            {
                "scenario": "scenario-01-baseline",
                "metric": "throughput_per_day",
                "expected": 10.0,
                "tolerance_pct": 1.0,
            }
        ]
    ).to_csv(targets, index=False)
    checks = verify_paper_targets(results, targets)
    assert bool(checks.loc[0, "passed"])
