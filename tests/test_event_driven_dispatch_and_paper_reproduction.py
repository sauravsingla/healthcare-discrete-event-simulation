from __future__ import annotations

import json

import numpy as np
import pytest
import simpy

from healthcare_des.advanced_model import AdvancedMRIModel, AdvancedScenarioConfig
from healthcare_des.paper_reproduction import (
    PUBLISHED_SCENARIO_INTENT,
    PUBLISHED_SPEC,
    paper_base_config,
    published_targets,
    reproduction_manifest,
    validate_reproduction_manifest,
)


def _blocked_model() -> tuple[simpy.Environment, AdvancedMRIModel, simpy.events.Event]:
    env = simpy.Environment()
    config = AdvancedScenarioConfig(
        days=1,
        daily_demand=1,
        mri_machines=1,
        emergency_capacity_reserve=0,
    )
    model = AdvancedMRIModel(env, config, np.random.default_rng(7))
    blocker = model.machines[0].resource.request(priority=-100)
    env.run(until=blocker)
    return env, model, blocker


def test_dispatch_wakes_immediately_on_non_grid_release() -> None:
    env, model, blocker = _blocked_model()
    waiting = env.process(model._acquire_any_machine(0, 10.0, "emergency"))

    def release() -> simpy.events.Event:
        yield env.timeout(5.037)
        model.machines[0].resource.release(blocker)
        model._notify_mri_dispatch()

    env.process(release())
    env.run(until=5.038)

    assert waiting.triggered
    machine, request = waiting.value
    assert float(env.now) == pytest.approx(5.038)
    machine.resource.release(request)


def test_exact_deadline_barrier_allows_same_timestamp_release_without_extra_patience() -> None:
    env, model, blocker = _blocked_model()
    waiting = env.process(model._acquire_any_machine(0, 5.0, "emergency"))

    def release() -> simpy.events.Event:
        yield env.timeout(5.0)
        model.machines[0].resource.release(blocker)
        model._notify_mri_dispatch()

    env.process(release())
    env.run(until=5.000001)

    assert waiting.triggered
    assert waiting.value is not None
    machine, request = waiting.value
    machine.resource.release(request)


def test_patient_expires_at_exact_deadline_when_no_machine_is_released() -> None:
    env, model, _ = _blocked_model()
    waiting = env.process(model._acquire_any_machine(0, 5.0, "emergency"))
    env.run(until=5.000001)

    assert waiting.triggered
    assert waiting.value is None


def test_published_reproduction_contract_is_complete_and_serialisable() -> None:
    manifest = reproduction_manifest()
    validate_reproduction_manifest(manifest)
    encoded = json.dumps(manifest, default=str)

    assert "10.4236/ojmsi.2020.84007" in encoded
    assert len(PUBLISHED_SCENARIO_INTENT) == 11
    assert PUBLISHED_SPEC.replications == 46
    assert PUBLISHED_SPEC.warmup_minutes == 4320
    assert PUBLISHED_SPEC.random_seed == 17
    assert PUBLISHED_SPEC.historical_february_2018_demand == 2089
    assert PUBLISHED_SPEC.simulated_demand_low == 1828
    assert PUBLISHED_SPEC.simulated_demand_high == 1930


def test_published_baseline_uses_disclosed_run_control_and_patient_mix() -> None:
    config = paper_base_config()
    config.validate()

    assert config.days == 30
    assert config.warmup_days == 3
    assert config.seed == 17
    assert config.no_show_rate == pytest.approx(0.08)
    assert config.outpatient_share == pytest.approx(0.57)
    assert config.inpatient_share == pytest.approx(0.2408)
    assert config.emergency_share == pytest.approx(0.1892)
    assert tuple(window.capacity for window in config.radiographer_capacity) == (4, 3, 2)


def test_published_targets_include_demand_and_reported_improvements() -> None:
    targets = published_targets().set_index("target")

    assert targets.loc["historical_february_2018_demand", "expected"] == 2089
    assert targets.loc["simulated_monthly_demand", "lower"] == 1828
    assert targets.loc["simulated_monthly_demand", "upper"] == 1930
    assert targets.loc["mri_waiting_room_queue_after", "expected"] == 5
    assert targets.loc["scenario_11_system_time_reduction", "expected"] == 20


def test_manifest_validation_rejects_missing_sections() -> None:
    manifest = reproduction_manifest()
    manifest.pop("scenario_intent")
    with pytest.raises(ValueError, match="Missing reproduction manifest sections"):
        validate_reproduction_manifest(manifest)
