"""Public advanced DES implementation with auditable lifecycle semantics."""

from __future__ import annotations

import heapq
from dataclasses import asdict, dataclass
from typing import Any, Callable, Literal

import numpy as np
import pandas as pd
import simpy

from . import advanced_engine as _engine


class _DeadlineEvent(simpy.Event):
    """Patience expiry scheduled after normal same-timestamp operations."""

    def __init__(self, env: simpy.Environment, delay: float):
        super().__init__(env)
        self._ok = True
        self._value = None
        env.schedule(self, priority=2, delay=max(0.0, delay))


class _NotifyingPriorityResource(simpy.PriorityResource):
    """Priority resource that wakes central dispatch whenever capacity is released."""

    def __init__(self, env: simpy.Environment, callback: Callable[[], None]):
        self._callback = callback
        super().__init__(env, capacity=1)

    def release(self, request):
        event = super().release(request)
        self._callback()
        return event


@dataclass(frozen=True)
class AdvancedScenarioConfig(_engine.AdvancedScenarioConfig):
    """Advanced configuration with explicit maintenance-window semantics."""

    maintenance_policy: Literal["fixed_duration_after_release", "fixed_calendar_window"] = (
        "fixed_duration_after_release"
    )

    def validate(self) -> None:
        super().validate()
        if self.maintenance_policy not in {
            "fixed_duration_after_release",
            "fixed_calendar_window",
        }:
            raise ValueError("invalid maintenance_policy")


class MRIMachine(_engine.MRIMachine):
    """MRI machine with interrupt-safe scans and unique downtime accounting."""

    def __init__(
        self,
        env,
        machine_id,
        config: AdvancedScenarioConfig,
        rng,
        availability_changed: Callable[[], None] | None = None,
    ):
        self._unavailable_since: float | None = None
        self._availability_changed = availability_changed or (lambda: None)
        super().__init__(env, machine_id, config, rng)
        self.resource = _NotifyingPriorityResource(env, self._availability_changed)

    def _add_blocker(self, blocker: str) -> None:
        if not self.blockers:
            self._unavailable_since = float(self.env.now)
        self.blockers.add(blocker)
        self._availability_changed()

    def _remove_blocker(self, blocker: str) -> None:
        self.blockers.discard(blocker)
        if not self.blockers and self._unavailable_since is not None:
            self.downtime += float(self.env.now) - self._unavailable_since
            self._unavailable_since = None
        self._availability_changed()

    def _maintenance_calendar(self):
        windows = [w for w in self.config.machine_maintenance if w.machine_id == self.machine_id]
        while True:
            minute = int(self.env.now % 1440)
            upcoming = [w for w in windows if w.start >= minute]
            if not upcoming:
                yield self.env.timeout(1440 - minute)
                continue
            window = min(upcoming, key=lambda item: item.start)
            yield self.env.timeout(max(0, window.start - minute))
            with self.resource.request(priority=-20) as request:
                yield request
                self._add_blocker("maintenance")
                self.state = "MAINTENANCE"
                policy = getattr(self.config, "maintenance_policy", "fixed_duration_after_release")
                if policy == "fixed_calendar_window":
                    duration = float(max(0, window.end - int(self.env.now % 1440)))
                else:
                    duration = float(window.end - window.start)
                if duration:
                    yield self.env.timeout(duration)
                self._remove_blocker("maintenance")
                self.state = "AVAILABLE" if not self.blockers else self.state

    def _failure_clock(self, mtbf: float):
        while True:
            yield self.env.timeout(float(self.rng.exponential(mtbf)))
            if self.blockers.intersection({"maintenance", "failure"}):
                continue
            self.failures += 1
            self._add_blocker("failure")
            self.state = "FAILED"
            if self.active_scan is not None and self.active_scan.is_alive:
                self.active_scan.interrupt(("machine_failure", self.machine_id))
            self.state = "REPAIR"
            yield self.env.timeout(
                float(self.rng.exponential(self.config.machine_repair_mean_minutes))
            )
            self._remove_blocker("failure")
            self.state = "AVAILABLE" if not self.blockers and self.resource.count == 0 else "BUSY"

    def scan(self, duration: float):
        remaining = duration
        segment_started: float | None = None
        self.active_scan = self.env.active_process
        try:
            while remaining > 0:
                try:
                    while self.blockers:
                        segment_started = None
                        yield self.env.timeout(0.1)
                    self.state = "BUSY"
                    segment_started = float(self.env.now)
                    yield self.env.timeout(remaining)
                    remaining = 0
                except simpy.Interrupt as interruption:
                    cause = interruption.cause
                    if not isinstance(cause, tuple) or not cause or cause[0] != "machine_failure":
                        raise
                    if segment_started is not None:
                        elapsed = float(self.env.now) - segment_started
                        remaining = (
                            duration
                            if self.config.restart_scan_after_failure
                            else max(0.0, remaining - elapsed)
                        )
                    segment_started = None
        finally:
            self.active_scan = None
            self.state = "AVAILABLE" if not self.blockers else self.state
            self._availability_changed()


class AdvancedMRIModel(_engine.AdvancedMRIModel):
    """Advanced model with one event-driven system-wide priority MRI queue."""

    def __init__(self, env, config, rng):
        self.env = env
        self.config = config
        self.rng = rng
        self.clerks = _engine.DynamicCapacity(env, 1, config.clerk_capacity)
        self.radiographers = _engine.DynamicCapacity(env, 1, config.radiographer_capacity)
        self.radiologists = _engine.DynamicCapacity(env, 1, config.radiologist_capacity)
        self._mri_dispatch_signal = env.event()
        self.machines = [
            MRIMachine(env, index, config, rng, self._notify_mri_dispatch)
            for index in range(config.mri_machines)
        ]
        self.ledger: dict[int, dict[str, Any]] = {}
        self.state: list[dict[str, float | str | bool]] = []
        self.active_patients = 0
        self._mri_waiters: list[tuple[int, int, str, simpy.Event]] = []
        self._mri_sequence = 0
        env.process(self._track_state())
        env.process(self._dispatch_mri())

    def _notify_mri_dispatch(self) -> None:
        """Wake the dispatcher when demand or machine availability changes."""
        if not self._mri_dispatch_signal.triggered:
            self._mri_dispatch_signal.succeed()

    def _track_state(self):
        while True:
            yield self.env.process(self.clerks.rebalance())
            yield self.env.process(self.radiographers.rebalance())
            yield self.env.process(self.radiologists.rebalance())
            minute = int(self.env.now % 1440)
            queue_types = [x[2] for x in self._mri_waiters if not x[3].triggered]
            self.state.append(
                {
                    "time": self.env.now,
                    "minute_of_day": minute,
                    "is_open": minute < self.config.operating_hours * 60,
                    "mri_queue": len(queue_types),
                    "mri_queue_emergency": queue_types.count("emergency"),
                    "mri_queue_inpatient": queue_types.count("inpatient"),
                    "mri_queue_outpatient": queue_types.count("outpatient"),
                    "mri_busy": sum(m.resource.count for m in self.machines),
                    "mri_available": sum(m.available for m in self.machines),
                    "clerk_target": self.clerks.target(minute),
                    "clerk_busy": self.clerks.busy,
                    "clerk_tokens": self.clerks.tokens.level,
                    "radiographer_target": self.radiographers.target(minute),
                    "radiographer_busy": self.radiographers.busy,
                    "radiographer_tokens": self.radiographers.tokens.level,
                    "radiologist_target": self.radiologists.target(minute),
                    "radiologist_busy": self.radiologists.busy,
                    "radiologist_tokens": self.radiologists.tokens.level,
                    "machine_states": "|".join(m.state for m in self.machines),
                }
            )
            yield self.env.timeout(self.config.tracking_interval_minutes)

    def _reserved_machine_count(self) -> int:
        return int(np.ceil(self.config.mri_machines * self.config.emergency_capacity_reserve))

    def _eligible_machine(self, patient_type: str):
        candidates = [m for m in self.machines if m.available]
        if not candidates:
            return None
        if patient_type == "outpatient" and len(candidates) <= self._reserved_machine_count():
            if any(
                x[2] in {"emergency", "inpatient"} and not x[3].triggered for x in self._mri_waiters
            ):
                return None
        return min(candidates, key=lambda m: m.machine_id)

    def _dispatch_mri(self):
        while True:
            self._mri_waiters = [x for x in self._mri_waiters if not x[3].triggered]
            heapq.heapify(self._mri_waiters)
            dispatched = False
            while self._mri_waiters:
                priority, _, patient_type, event = self._mri_waiters[0]
                machine = self._eligible_machine(patient_type)
                if machine is None:
                    break
                heapq.heappop(self._mri_waiters)
                request = machine.resource.request(priority=priority)
                yield request
                if not event.triggered:
                    event.succeed((machine, request))
                else:
                    machine.resource.release(request)
                dispatched = True
            if dispatched:
                yield self.env.timeout(0)
                continue
            signal = self._mri_dispatch_signal
            if signal.triggered:
                self._mri_dispatch_signal = self.env.event()
                yield self.env.timeout(0)
                continue
            yield signal
            if signal is self._mri_dispatch_signal:
                self._mri_dispatch_signal = self.env.event()

    def _acquire_any_machine(self, priority: int, deadline: float, patient_type: str | None = None):
        patient_type = patient_type or next(
            (name for name, value in self.PRIORITY.items() if value == priority), "outpatient"
        )
        event = self.env.event()
        self._mri_sequence += 1
        heapq.heappush(self._mri_waiters, (priority, self._mri_sequence, patient_type, event))
        self._notify_mri_dispatch()
        timeout = _DeadlineEvent(self.env, deadline - float(self.env.now))
        outcome = yield event | timeout
        if event in outcome:
            return event.value
        if not event.triggered:
            event.fail(TimeoutError("MRI patience exhausted"))
            event.defused = True
            self._notify_mri_dispatch()
        return None

    def patient(self, patient_id: int):
        row = self.ledger[patient_id]
        self.active_patients += 1
        try:
            arrival = float(self.env.now)
            row["arrival"] = arrival
            if row["patient_type"] == "outpatient" and self.rng.random() < self.config.no_show_rate:
                self._finish(patient_id, "no_show")
                return
            row["entered_system"] = True
            waits: dict[str, float] = {}
            remaining_patience = float(self.config.abandonment_minutes)
            stages = (
                ("reception", self.clerks, float(self.rng.exponential(self.config.reception_mean))),
                (
                    "preparation",
                    self.radiographers,
                    float(self.rng.exponential(self.config.preparation_mean)),
                ),
            )
            for stage, capacity, duration in stages:
                wait = yield self.env.process(
                    self._timed_staff_service(capacity, duration, self.env.now + remaining_patience)
                )
                if wait is None:
                    self._finish(patient_id, "abandoned", abandonment_stage=stage, **waits)
                    return
                waits[f"{stage}_wait_minutes"] = wait
                remaining_patience = max(0.0, remaining_patience - wait)

            mri_started = float(self.env.now)
            acquired = yield self.env.process(
                self._acquire_any_machine(
                    self.PRIORITY[row["patient_type"]],
                    self.env.now + remaining_patience,
                    row["patient_type"],
                )
            )
            if acquired is None:
                self._finish(patient_id, "abandoned", abandonment_stage="mri", **waits)
                return
            machine, request = acquired
            mri_wait = float(self.env.now) - mri_started
            waits["mri_wait_minutes"] = mri_wait
            remaining_patience = max(0.0, remaining_patience - mri_wait)
            row["machine_id"] = machine.machine_id
            scan_duration = max(
                5.0, float(self.rng.normal(self.config.scan_mean, self.config.scan_sd))
            )
            try:
                yield self.env.process(machine.scan(scan_duration + self.config.cleaning_minutes))
            finally:
                machine.resource.release(request)
            row["scan_completed"] = True
            row["scan_completion_time"] = float(self.env.now)

            reporting = yield self.env.process(
                self._timed_staff_service(
                    self.radiologists,
                    float(self.rng.exponential(self.config.report_mean)),
                    self.env.now + remaining_patience,
                )
            )
            if reporting is None:
                total_wait = sum(waits.values()) + remaining_patience
                self._finish(
                    patient_id,
                    "completed",
                    report_status="unfinished",
                    **waits,
                    reporting_wait_minutes=remaining_patience,
                    wait_minutes=total_wait,
                    service_minutes=float(self.env.now) - arrival - total_wait,
                    system_minutes=float(self.env.now) - arrival,
                )
                return
            waits["reporting_wait_minutes"] = reporting
            total_wait = sum(waits.values())
            self._finish(
                patient_id,
                "completed",
                report_status="completed",
                **waits,
                wait_minutes=total_wait,
                service_minutes=float(self.env.now) - arrival - total_wait,
                system_minutes=float(self.env.now) - arrival,
            )
        finally:
            self.active_patients -= 1


AdvancedSimulationResult = _engine.AdvancedSimulationResult
CapacityWindow = _engine.CapacityWindow
DynamicCapacity = _engine.DynamicCapacity
MachineWindow = _engine.MachineWindow


def _run_to_termination(
    env: simpy.Environment, model: AdvancedMRIModel, config: AdvancedScenarioConfig, horizon: float
) -> None:
    env.run(until=horizon)
    if config.termination_policy == "horizon":
        return
    drain_limit = (
        float("inf") if config.termination_policy == "drain" else horizon + config.max_drain_minutes
    )
    while model.active_patients > 0 and env.now < drain_limit:
        env.run(until=min(env.now + 1, drain_limit))


def _bootstrap_interval(
    values: pd.Series, rng: np.random.Generator, samples: int
) -> tuple[float, float]:
    array = values.to_numpy(dtype=float)
    if len(array) <= 1 or samples <= 0:
        mean = float(array.mean()) if len(array) else 0.0
        return mean, mean
    means = np.asarray(
        [rng.choice(array, size=len(array), replace=True).mean() for _ in range(samples)]
    )
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def run_advanced_once(
    config: AdvancedScenarioConfig, replication: int = 0
) -> tuple[AdvancedSimulationResult, pd.DataFrame, pd.DataFrame]:
    config.validate()
    env = simpy.Environment()
    rng = np.random.default_rng(config.seed + replication)
    model = AdvancedMRIModel(env, config, rng)
    env.process(model.source())
    horizon = (config.warmup_days + config.days) * 1440
    _run_to_termination(env, model, config, horizon)
    measurement_start = config.warmup_days * 1440

    frame = pd.DataFrame(model.ledger.values())
    if frame.empty:
        frame = pd.DataFrame(
            columns=["patient_id", "patient_type", "status", "booked_time", "entered_system"]
        )
    frame = frame.loc[
        (frame["booked_time"].astype(float) >= measurement_start)
        & (frame["booked_time"].astype(float) < horizon)
    ].copy()
    terminal = {"completed", "cancelled", "no_show", "abandoned"}
    frame.loc[~frame["status"].isin(terminal), "status"] = "unfinished"

    state = pd.DataFrame(model.state)
    state = state.loc[(state["time"] >= measurement_start) & (state["time"] < env.now)].copy()
    completed_frame = frame.loc[frame["status"] == "completed"]
    open_state = state.loc[state["is_open"].astype(bool)]

    counts = frame["status"].value_counts()
    booked = int((frame["patient_type"] == "outpatient").sum())
    cancelled = int(counts.get("cancelled", 0))
    expected_arrivals = len(frame) - cancelled
    no_shows = int(counts.get("no_show", 0))
    arrivals = int(frame["entered_system"].fillna(False).astype(bool).sum())
    completed = int(counts.get("completed", 0))
    abandoned = int(counts.get("abandoned", 0))
    unfinished = int(counts.get("unfinished", 0))

    def mean_column(name: str) -> float:
        return (
            float(completed_frame[name].fillna(0).mean())
            if not completed_frame.empty and name in completed_frame
            else 0.0
        )

    mean_queue_open = float(open_state["mri_queue"].mean()) if not open_state.empty else 0.0
    mean_queue_24h = float(state["mri_queue"].mean()) if not state.empty else 0.0
    mean_available_open = float(open_state["mri_available"].mean()) if not open_state.empty else 0.0
    mean_available_24h = float(state["mri_available"].mean()) if not state.empty else 0.0
    result = AdvancedSimulationResult(
        scenario=config.name,
        replication=replication,
        booked=booked,
        cancelled=cancelled,
        expected_arrivals=int(expected_arrivals),
        no_shows=no_shows,
        arrivals=arrivals,
        completed=completed,
        abandoned=abandoned,
        unfinished=unfinished,
        completion_rate_pct=100.0 * completed / arrivals if arrivals else 0.0,
        mean_wait_minutes=mean_column("wait_minutes"),
        mean_reception_wait_minutes=mean_column("reception_wait_minutes"),
        mean_preparation_wait_minutes=mean_column("preparation_wait_minutes"),
        mean_mri_wait_minutes=mean_column("mri_wait_minutes"),
        mean_reporting_wait_minutes=mean_column("reporting_wait_minutes"),
        mean_system_minutes=mean_column("system_minutes"),
        p90_system_minutes=float(completed_frame["system_minutes"].quantile(0.9))
        if not completed_frame.empty
        else 0.0,
        throughput_per_day=completed / config.days,
        mean_queue_length=mean_queue_open,
        mean_queue_length_open=mean_queue_open,
        mean_queue_length_24h=mean_queue_24h,
        max_queue_length=int(state["mri_queue"].max()) if not state.empty else 0,
        mri_failures=sum(machine.failures for machine in model.machines),
        mri_downtime_minutes=sum(machine.downtime for machine in model.machines),
        mean_available_mri=mean_available_open,
        mean_available_mri_open=mean_available_open,
        mean_available_mri_24h=mean_available_24h,
    )
    return result, frame.reset_index(drop=True), state.reset_index(drop=True)


def run_advanced_replications(
    config: AdvancedScenarioConfig, replications: int = 20
) -> pd.DataFrame:
    if replications <= 0:
        raise ValueError("replications must be positive")
    return pd.DataFrame(
        asdict(run_advanced_once(config, index)[0]) for index in range(replications)
    )


def summarise_advanced(
    results: pd.DataFrame, bootstrap_samples: int = 2000, seed: int = 17
) -> dict[str, float]:
    """Summarise replications with bootstrap percentile confidence intervals."""
    if results.empty:
        raise ValueError("results must not be empty")
    rng = np.random.default_rng(seed)
    summary: dict[str, float] = {}
    for column in results.select_dtypes(include=[np.number]).columns:
        values = results[column].astype(float)
        low, high = _bootstrap_interval(values, rng, bootstrap_samples)
        summary[column] = float(values.mean())
        summary[f"{column}_sd"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        summary[f"{column}_ci95_low"] = low
        summary[f"{column}_ci95_high"] = high
    return summary


__all__ = [
    "AdvancedMRIModel",
    "AdvancedScenarioConfig",
    "AdvancedSimulationResult",
    "CapacityWindow",
    "DynamicCapacity",
    "MRIMachine",
    "MachineWindow",
    "run_advanced_once",
    "run_advanced_replications",
    "summarise_advanced",
]
