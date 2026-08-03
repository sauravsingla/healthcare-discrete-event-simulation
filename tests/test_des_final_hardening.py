import importlib

import numpy as np
import pandas as pd
import pytest
import simpy

import healthcare_des.advanced_engine as legacy_engine
from healthcare_des.advanced_model import (
    AdvancedMRIModel,
    AdvancedScenarioConfig,
    MachineWindow,
    run_advanced_once,
    run_advanced_replications,
    summarise_advanced,
)


def _model(
    *, machines: int = 1, reserve: float = 0.0
) -> tuple[simpy.Environment, AdvancedMRIModel]:
    env = simpy.Environment()
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=1,
        mri_machines=machines,
        emergency_capacity_reserve=reserve,
    )
    return env, AdvancedMRIModel(env, config, np.random.default_rng(12))


def test_equal_priority_dispatch_is_fifo():
    env, model = _model()
    machine = model.machines[0]
    blocker = machine.resource.request(priority=-100)
    env.run(until=blocker)

    first = env.process(model._acquire_any_machine(1, 100, "inpatient"))
    second = env.process(model._acquire_any_machine(1, 100, "inpatient"))
    env.run(until=1)
    machine.resource.release(blocker)
    env.run(until=2)

    assert first.triggered
    assert not second.triggered
    assigned, request = first.value
    assigned.resource.release(request)
    env.run(until=3)
    assert second.triggered


def test_two_simultaneous_releases_dispatch_to_distinct_scanners():
    env, model = _model(machines=2)
    blockers = [machine.resource.request(priority=-100) for machine in model.machines]
    for blocker in blockers:
        env.run(until=blocker)

    first = env.process(model._acquire_any_machine(0, 100, "emergency"))
    second = env.process(model._acquire_any_machine(1, 100, "inpatient"))
    env.run(until=1)
    for machine, blocker in zip(model.machines, blockers, strict=True):
        machine.resource.release(blocker)
    env.run(until=2)

    assert first.triggered and second.triggered
    first_machine, first_request = first.value
    second_machine, second_request = second.value
    assert first_machine.machine_id != second_machine.machine_id
    first_machine.resource.release(first_request)
    second_machine.resource.release(second_request)


def test_dispatch_waits_for_same_time_maintenance_window():
    env = simpy.Environment()
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=1,
        mri_machines=1,
        machine_maintenance=(MachineWindow(0, 0, 5),),
        maintenance_policy="fixed_calendar_window",
        emergency_capacity_reserve=0,
    )
    model = AdvancedMRIModel(env, config, np.random.default_rng(3))
    waiting = env.process(model._acquire_any_machine(0, 20, "emergency"))
    env.run(until=1)
    assert not waiting.triggered
    env.run(until=6)
    assert waiting.triggered
    machine, request = waiting.value
    machine.resource.release(request)


def test_dispatch_wins_when_release_and_deadline_share_timestamp():
    env, model = _model()
    machine = model.machines[0]
    blocker = machine.resource.request(priority=-100)
    env.run(until=blocker)
    waiting = env.process(model._acquire_any_machine(0, 5, "emergency"))

    def release_at_deadline():
        yield env.timeout(5)
        machine.resource.release(blocker)

    env.process(release_at_deadline())
    env.run(until=5.2)
    assert waiting.triggered
    assert waiting.value is not None
    assigned, request = waiting.value
    assigned.resource.release(request)


def test_repeated_failures_preserve_remaining_scan_work():
    env, model = _model()
    machine = model.machines[0]
    completed_at: list[float] = []

    def scan():
        yield env.process(machine.scan(10))
        completed_at.append(float(env.now))

    def fail(at: float, repair: float):
        yield env.timeout(at - env.now)
        machine._add_blocker("failure")
        assert machine.active_scan is not None
        machine.active_scan.interrupt(("machine_failure", machine.machine_id))
        yield env.timeout(repair)
        machine._remove_blocker("failure")

    env.process(scan())
    env.process(fail(2, 1))
    env.process(fail(6, 2))
    env.run(until=20)
    assert completed_at == pytest.approx([13.0], abs=0.2)
    assert machine.downtime == pytest.approx(3.0)


def test_importing_public_model_does_not_mutate_legacy_module_globals():
    original_config = legacy_engine.AdvancedScenarioConfig
    original_machine = legacy_engine.MRIMachine
    original_model = legacy_engine.AdvancedMRIModel
    import healthcare_des.advanced_model as public_model

    importlib.reload(public_model)
    assert legacy_engine.AdvancedScenarioConfig is original_config
    assert legacy_engine.MRIMachine is original_machine
    assert legacy_engine.AdvancedMRIModel is original_model


def test_public_replications_and_summary_are_deterministic():
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=5,
        mri_machines=2,
        cancellation_rate=0,
        no_show_rate=0,
        emergency_capacity_reserve=0,
        bootstrap_samples=20,
        seed=21,
    )
    first = run_advanced_replications(config, replications=2)
    second = run_advanced_replications(config, replications=2)
    pd.testing.assert_frame_equal(first, second)
    summary = summarise_advanced(first, bootstrap_samples=20, seed=21)
    assert summary["completed"] == pytest.approx(first["completed"].mean())
    assert summary["completed_ci95_low"] <= summary["completed"]
    assert summary["completed_ci95_high"] >= summary["completed"]


def test_summary_rejects_empty_results_and_replications_reject_zero():
    with pytest.raises(ValueError, match="must not be empty"):
        summarise_advanced(pd.DataFrame())
    with pytest.raises(ValueError, match="must be positive"):
        run_advanced_replications(AdvancedScenarioConfig(), replications=0)


@pytest.mark.parametrize(
    "config",
    [
        AdvancedScenarioConfig(days=0),
        AdvancedScenarioConfig(warmup_days=-1),
        AdvancedScenarioConfig(outpatient_share=0.5),
        AdvancedScenarioConfig(emergency_capacity_reserve=1),
        AdvancedScenarioConfig(abandonment_minutes=0),
        AdvancedScenarioConfig(weekday_multipliers=(1.0,)),
        AdvancedScenarioConfig(outpatient_hourly_profile=(1.0,)),
        AdvancedScenarioConfig(emergency_hourly_profile_24h=(1.0,)),
        AdvancedScenarioConfig(tracking_interval_minutes=0),
        AdvancedScenarioConfig(termination_policy="invalid"),  # type: ignore[arg-type]
        AdvancedScenarioConfig(maintenance_policy="invalid"),  # type: ignore[arg-type]
    ],
)
def test_invalid_advanced_configurations_are_rejected(config):
    with pytest.raises(ValueError):
        config.validate()


def test_urgent_aware_reserve_does_not_idle_without_urgent_waiters():
    env, model = _model(machines=2, reserve=0.5)
    outpatient = env.process(model._acquire_any_machine(2, 10, "outpatient"))
    env.run(until=1)
    assert outpatient.triggered
    machine, request = outpatient.value
    machine.resource.release(request)


def test_urgent_aware_reserve_holds_last_available_scanner_for_waiting_urgent_patient():
    env, model = _model(machines=2, reserve=0.5)
    first_machine = model.machines[0]
    blocker = first_machine.resource.request(priority=-100)
    env.run(until=blocker)
    outpatient = env.process(model._acquire_any_machine(2, 20, "outpatient"))
    urgent = env.process(model._acquire_any_machine(0, 20, "emergency"))
    env.run(until=1)
    assert urgent.triggered
    assert not outpatient.triggered
    urgent_machine, urgent_request = urgent.value
    urgent_machine.resource.release(urgent_request)
    env.run(until=2)
    assert outpatient.triggered
    first_machine.resource.release(blocker)


def test_simplified_queue_obeys_little_law_within_transient_tolerance():
    config = AdvancedScenarioConfig(
        days=8,
        warmup_days=2,
        daily_demand=35,
        mri_machines=1,
        cancellation_rate=0,
        no_show_rate=0,
        abandonment_minutes=1440,
        emergency_capacity_reserve=0,
        tracking_interval_minutes=1,
        seed=8,
    )
    result, _, _ = run_advanced_once(config)
    arrival_rate_per_minute = result.completed / (config.days * 1440)
    implied_queue = arrival_rate_per_minute * result.mean_mri_wait_minutes
    assert result.mean_queue_length_24h >= 0
    assert abs(result.mean_queue_length_24h - implied_queue) <= max(1.0, implied_queue)


def test_legacy_engine_executes_full_compatibility_workflow():
    config = legacy_engine.AdvancedScenarioConfig(
        name="legacy-compatibility",
        days=2,
        warmup_days=1,
        daily_demand=18,
        mri_machines=2,
        machine_maintenance=(legacy_engine.MachineWindow(0, 20, 45),),
        machine_mtbf_minutes=(120.0, 0.0),
        machine_repair_mean_minutes=5,
        cancellation_rate=0.1,
        no_show_rate=0.1,
        abandonment_minutes=360,
        emergency_capacity_reserve=0.1,
        tracking_interval_minutes=2,
        bootstrap_samples=20,
        seed=31,
    )
    result, patients, state = legacy_engine.run_advanced_once(config)
    assert result.arrivals == result.completed + result.abandoned + result.unfinished
    assert not patients.empty
    assert not state.empty
    assert result.mri_downtime_minutes >= 0

    replications = legacy_engine.run_advanced_replications(config, replications=2)
    summary = legacy_engine.summarise_advanced(replications, bootstrap_samples=20, seed=31)
    assert len(replications) == 2
    assert summary["completed"] == pytest.approx(replications["completed"].mean())


def test_legacy_engine_validation_and_summary_edges_are_exercised():
    with pytest.raises(ValueError):
        legacy_engine.AdvancedScenarioConfig(days=0).validate()
    with pytest.raises(ValueError, match="must be positive"):
        legacy_engine.run_advanced_replications(
            legacy_engine.AdvancedScenarioConfig(), replications=0
        )
    with pytest.raises(ValueError, match="must not be empty"):
        legacy_engine.summarise_advanced(pd.DataFrame())

    singleton = pd.DataFrame({"completed": [1.0]})
    summary = legacy_engine.summarise_advanced(singleton, bootstrap_samples=0)
    assert summary["completed_ci95_low"] == 1.0
    assert summary["completed_ci95_high"] == 1.0
