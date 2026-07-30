from dataclasses import replace
from datetime import date

import numpy as np

from healthcare_des.advanced_model import (
    AdvancedScenarioConfig,
    CapacityWindow,
    MachineWindow,
    run_advanced_once,
    run_advanced_replications,
    summarise_advanced,
)


def config(**changes):
    base = AdvancedScenarioConfig(
        days=2,
        daily_demand=24,
        mri_machines=2,
        cancellation_rate=0.0,
        no_show_rate=0.0,
        seed=11,
    )
    return replace(base, **changes)


def test_wait_is_not_system_time_and_stage_waits_reconcile():
    _, frame, _ = run_advanced_once(config())
    completed = frame.loc[frame["status"] == "completed"]
    assert not completed.empty
    stage_sum = completed[
        [
            "reception_wait_minutes",
            "preparation_wait_minutes",
            "mri_wait_minutes",
            "reporting_wait_minutes",
        ]
    ].sum(axis=1)
    assert np.allclose(stage_sum, completed["wait_minutes"])
    assert (completed["system_minutes"] >= completed["wait_minutes"]).all()
    assert (completed["system_minutes"] > completed["wait_minutes"]).any()


def test_patient_outcomes_reconcile_exactly():
    result, frame, _ = run_advanced_once(
        config(cancellation_rate=0.2, no_show_rate=0.2, abandonment_minutes=20)
    )
    assert (
        result.expected_arrivals
        == result.booked + int((frame["patient_type"] != "outpatient").sum()) - result.cancelled
    )
    assert result.arrivals == result.completed + result.abandoned + result.unfinished
    assert set(frame["status"]).issubset(
        {"completed", "cancelled", "no_show", "abandoned", "unfinished"}
    )


def test_capacity_reduction_never_creates_negative_or_excess_tokens():
    scenario = config(
        clerk_capacity=(
            CapacityWindow(0, 120, 3),
            CapacityWindow(120, 480, 1),
        ),
        daily_demand=80,
    )
    _, _, state = run_advanced_once(scenario)
    assert (state["clerk_busy"] >= 0).all()
    assert (state["clerk_tokens"] >= 0).all()
    assert (state["clerk_tokens"] + state["clerk_busy"] >= state["clerk_target"]).all()


def test_overlapping_capacity_windows_are_not_order_dependent():
    first = config(clerk_capacity=(CapacityWindow(0, 300, 2), CapacityWindow(120, 240, 3)))
    second = replace(first, clerk_capacity=tuple(reversed(first.clerk_capacity)))
    _, _, first_state = run_advanced_once(first)
    _, _, second_state = run_advanced_once(second)
    first_target = first_state.loc[first_state["minute_of_day"] == 180, "clerk_target"].iloc[0]
    second_target = second_state.loc[second_state["minute_of_day"] == 180, "clerk_target"].iloc[0]
    assert first_target == second_target == 3


def test_maintenance_waits_for_machine_resource_and_state_is_explicit():
    scenario = config(
        mri_machines=1,
        machine_maintenance=(MachineWindow(0, 20, 80),),
        daily_demand=40,
    )
    result, _, state = run_advanced_once(scenario)
    assert result.mri_downtime_minutes >= 60
    assert state["machine_states"].str.contains("MAINTENANCE").any()


def test_failures_interrupt_and_repair_scans_without_losing_patient_accounting():
    scenario = config(
        mri_machines=1,
        machine_mtbf_minutes=(10.0,),
        machine_repair_mean_minutes=3.0,
        daily_demand=15,
        abandonment_minutes=600,
    )
    result, _, state = run_advanced_once(scenario)
    assert result.mri_failures > 0
    assert state["machine_states"].str.contains("REPAIR|FAILED", regex=True).any()
    assert result.arrivals == result.completed + result.abandoned + result.unfinished


def test_outpatient_profile_controls_scheduled_hours():
    scenario = config(
        operating_hours=8,
        outpatient_share=1.0,
        inpatient_share=0.0,
        emergency_share=0.0,
        outpatient_hourly_profile=(0, 0, 0, 0, 0, 0, 0, 1),
        daily_demand=12,
    )
    _, frame, _ = run_advanced_once(scenario)
    outpatient = frame.loc[frame["patient_type"] == "outpatient"]
    assert not outpatient.empty
    assert ((outpatient["scheduled_time"] % 1440) >= 7 * 60).all()


def test_overbooking_does_not_change_physical_capacity_ceiling():
    baseline = config(
        days=1,
        daily_demand=500,
        mri_machines=1,
        outpatient_share=1.0,
        inpatient_share=0.0,
        emergency_share=0.0,
        emergency_capacity_reserve=0.0,
    )
    _, base_frame, _ = run_advanced_once(baseline)
    _, overbooked_frame, _ = run_advanced_once(replace(baseline, overbooking_rate=0.5))
    assert len(overbooked_frame) <= int(
        baseline.operating_hours * 60 / (baseline.scan_mean + baseline.cleaning_minutes)
    )
    assert len(overbooked_frame) >= len(base_frame)


def test_calendar_start_date_controls_weekday_multiplier():
    monday = config(
        days=1,
        start_date=date(2026, 1, 5),
        weekday_multipliers=(2.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1),
    )
    tuesday = replace(monday, start_date=date(2026, 1, 6))
    monday_result, _, _ = run_advanced_once(monday)
    tuesday_result, _, _ = run_advanced_once(tuesday)
    assert monday_result.expected_arrivals > tuesday_result.expected_arrivals


def test_warmup_patients_and_state_are_excluded():
    scenario = config(days=1, warmup_days=1)
    _, frame, state = run_advanced_once(scenario)
    assert (frame["booked_time"] >= 1440).all()
    assert (state["time"] >= 1440).all()


def test_horizon_and_bounded_drain_report_unfinished_consistently():
    short = config(days=1, daily_demand=100, termination_policy="horizon")
    drained = replace(short, termination_policy="bounded_drain", max_drain_minutes=600)
    horizon_result, _, _ = run_advanced_once(short)
    drained_result, _, _ = run_advanced_once(drained)
    assert drained_result.unfinished <= horizon_result.unfinished
    assert (
        horizon_result.arrivals
        == horizon_result.completed + horizon_result.abandoned + horizon_result.unfinished
    )


def test_open_and_24_hour_state_metrics_are_both_reported():
    result, _, state = run_advanced_once(config())
    assert "is_open" in state
    assert result.mean_queue_length == result.mean_queue_length_open
    assert result.mean_available_mri == result.mean_available_mri_open


def test_bootstrap_summary_is_reproducible():
    replications = run_advanced_replications(config(days=1, daily_demand=8), replications=3)
    first = summarise_advanced(replications, bootstrap_samples=100, seed=9)
    second = summarise_advanced(replications, bootstrap_samples=100, seed=9)
    assert first == second
    assert first["throughput_per_day_ci95_low"] <= first["throughput_per_day"]
    assert first["throughput_per_day_ci95_high"] >= first["throughput_per_day"]
