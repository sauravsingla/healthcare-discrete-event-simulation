from dataclasses import replace

import numpy as np
import simpy

from healthcare_des.advanced_model import (
    AdvancedMRIModel,
    AdvancedScenarioConfig,
    MachineWindow,
    run_advanced_once,
)


def test_global_dispatch_prioritises_emergency_over_outpatient():
    env = simpy.Environment()
    config = AdvancedScenarioConfig(
        days=1, daily_demand=1, mri_machines=1, emergency_capacity_reserve=0
    )
    model = AdvancedMRIModel(env, config, np.random.default_rng(4))
    machine = model.machines[0]
    blocker = machine.resource.request(priority=-100)
    env.run(until=blocker)
    outpatient = env.process(model._acquire_any_machine(2, 100, "outpatient"))
    emergency = env.process(model._acquire_any_machine(0, 100, "emergency"))
    env.run(until=1)
    machine.resource.release(blocker)
    env.run(until=2)
    assert emergency.triggered
    assert not outpatient.triggered
    assigned_machine, request = emergency.value
    assigned_machine.resource.release(request)
    env.run(until=3)
    assert outpatient.triggered


def test_explicit_queue_metrics_include_waiting_patients():
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=100,
        mri_machines=1,
        cancellation_rate=0,
        no_show_rate=0,
        abandonment_minutes=600,
        tracking_interval_minutes=1,
        emergency_capacity_reserve=0,
        seed=22,
    )
    result, _, state = run_advanced_once(config)
    assert state["mri_queue"].max() > 0
    assert (
        state["mri_queue"]
        == state["mri_queue_emergency"]
        + state["mri_queue_inpatient"]
        + state["mri_queue_outpatient"]
    ).all()
    assert result.max_queue_length == int(state["mri_queue"].max())


def test_service_time_does_not_consume_patience():
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=1,
        mri_machines=2,
        outpatient_share=1,
        inpatient_share=0,
        emergency_share=0,
        cancellation_rate=0,
        no_show_rate=0,
        abandonment_minutes=1,
        reception_mean=20,
        preparation_mean=20,
        report_mean=20,
        emergency_capacity_reserve=0,
        seed=7,
    )
    result, _, _ = run_advanced_once(config)
    assert result.arrivals >= 1
    assert result.abandoned == 0


def test_scanned_patient_is_not_reclassified_as_abandoned_during_reporting():
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=8,
        mri_machines=2,
        cancellation_rate=0,
        no_show_rate=0,
        abandonment_minutes=1,
        report_mean=100,
        emergency_capacity_reserve=0,
        seed=13,
    )
    result, frame, _ = run_advanced_once(config)
    scanned = frame.loc[frame["scan_completed"].fillna(False)]
    assert not scanned.empty
    assert (scanned["status"] == "completed").all()
    assert set(scanned["report_status"].dropna()).issubset({"completed", "unfinished"})
    assert result.arrivals == result.completed + result.abandoned + result.unfinished


def test_calendar_maintenance_does_not_extend_past_window_end():
    base = AdvancedScenarioConfig(
        days=1,
        daily_demand=20,
        mri_machines=1,
        machine_maintenance=(MachineWindow(0, 20, 80),),
        cancellation_rate=0,
        no_show_rate=0,
        emergency_capacity_reserve=0,
        seed=3,
    )
    fixed, _, _ = run_advanced_once(replace(base, maintenance_policy="fixed_calendar_window"))
    duration, _, _ = run_advanced_once(
        replace(base, maintenance_policy="fixed_duration_after_release")
    )
    assert fixed.mri_downtime_minutes <= duration.mri_downtime_minutes


def test_overlapping_blockers_are_counted_once():
    env = simpy.Environment()
    model = AdvancedMRIModel(
        env,
        AdvancedScenarioConfig(days=1, daily_demand=1, mri_machines=1),
        np.random.default_rng(1),
    )
    machine = model.machines[0]
    machine._add_blocker("maintenance")
    env.run(until=5)
    machine._add_blocker("failure")
    env.run(until=10)
    machine._remove_blocker("maintenance")
    env.run(until=15)
    machine._remove_blocker("failure")
    assert machine.downtime == 15
