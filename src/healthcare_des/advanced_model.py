"""Advanced MRI simulation with dynamic capacity, machine state and demand calendars."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd
import simpy


@dataclass(frozen=True)
class CapacityWindow:
    start: int
    end: int
    capacity: int


@dataclass(frozen=True)
class MachineWindow:
    machine_id: int
    start: int
    end: int


@dataclass(frozen=True)
class AdvancedScenarioConfig:
    name: str = "advanced-baseline"
    days: int = 30
    warmup_days: int = 0
    operating_hours: int = 8
    daily_demand: float = 70.0
    outpatient_share: float = 0.57
    inpatient_share: float = 0.2408
    emergency_share: float = 0.1892
    weekday_multipliers: tuple[float, ...] = (1.0, 1.05, 1.05, 1.0, 0.95, 0.65, 0.55)
    seasonal_multipliers: tuple[float, ...] = (1.0,) * 12
    outpatient_hourly_profile: tuple[float, ...] = (1.2, 1.3, 1.1, 0.8, 0.7, 1.1, 1.0, 0.8)
    emergency_hourly_profile_24h: tuple[float, ...] = (0.7, 0.6, 0.55, 0.5, 0.55, 0.7, 0.9, 1.1, 1.2, 1.15, 1.05, 1.0, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.2, 1.1, 1.0, 0.9, 0.8, 0.75)
    appointment_interval_minutes: int = 15
    appointment_arrival_sd_minutes: float = 8.0
    overbooking_rate: float = 0.0
    cancellation_rate: float = 0.05
    no_show_rate: float = 0.08
    abandonment_minutes: float = 240.0
    mri_machines: int = 4
    machine_maintenance: tuple[MachineWindow, ...] = ()
    machine_mtbf_minutes: tuple[float, ...] = ()
    machine_repair_mean_minutes: float = 60.0
    cleaning_minutes: float = 3.0
    clerk_capacity: tuple[CapacityWindow, ...] = ()
    radiographer_capacity: tuple[CapacityWindow, ...] = ()
    radiologist_capacity: tuple[CapacityWindow, ...] = ()
    reception_mean: float = 8.0
    preparation_mean: float = 5.0
    scan_mean: float = 26.46
    report_mean: float = 9.0
    tracking_interval_minutes: int = 5
    seed: int = 17

    def validate(self) -> None:
        if self.days <= 0 or self.mri_machines <= 0:
            raise ValueError("days and mri_machines must be positive")
        if not 0 < self.operating_hours <= 24:
            raise ValueError("operating_hours must be in (0, 24]")
        shares = self.outpatient_share + self.inpatient_share + self.emergency_share
        if not np.isclose(shares, 1.0, atol=1e-6):
            raise ValueError("patient shares must sum to 1")
        for value in (self.overbooking_rate, self.cancellation_rate, self.no_show_rate):
            if not 0 <= value < 1:
                raise ValueError("booking probabilities must be in [0, 1)")
        if len(self.weekday_multipliers) != 7 or len(self.seasonal_multipliers) != 12:
            raise ValueError("weekday and seasonal multipliers require 7 and 12 values")
        if len(self.emergency_hourly_profile_24h) != 24:
            raise ValueError("emergency_hourly_profile_24h must contain 24 values")
        for window in (*self.clerk_capacity, *self.radiographer_capacity, *self.radiologist_capacity):
            if not 0 <= window.start < window.end <= 1440 or window.capacity < 0:
                raise ValueError(f"invalid capacity window: {window}")
        for window in self.machine_maintenance:
            if not 0 <= window.machine_id < self.mri_machines or not 0 <= window.start < window.end <= 1440:
                raise ValueError(f"invalid machine maintenance window: {window}")


@dataclass(frozen=True)
class AdvancedSimulationResult:
    scenario: str
    replication: int
    arrivals: int
    completed: int
    cancelled: int
    no_shows: int
    abandoned: int
    completion_rate_pct: float
    mean_wait_minutes: float
    p90_system_minutes: float
    throughput_per_day: float
    mean_queue_length: float
    max_queue_length: int
    mri_failures: int
    mri_downtime_minutes: float
    mean_available_mri: float


class DynamicCapacity:
    """Token-based capacity that changes by minute-of-day."""

    def __init__(self, env: simpy.Environment, default_capacity: int, windows: tuple[CapacityWindow, ...]):
        self.env = env
        self.default_capacity = default_capacity
        self.windows = windows
        self.container = simpy.Container(env, capacity=max(default_capacity, *(w.capacity for w in windows), 1), init=default_capacity)
        env.process(self._controller())

    def target(self, minute: int) -> int:
        matches = [w.capacity for w in self.windows if w.start <= minute < w.end]
        return matches[-1] if matches else self.default_capacity

    def _controller(self):
        while True:
            target = self.target(int(self.env.now % 1440))
            delta = target - int(self.container.level)
            if delta > 0:
                yield self.container.put(delta)
            elif delta < 0:
                yield self.container.get(min(-delta, self.container.level))
            yield self.env.timeout(1)

    def request(self):
        return self.container.get(1)

    def release(self):
        return self.container.put(1)


class MRIMachine:
    def __init__(self, env: simpy.Environment, machine_id: int, config: AdvancedScenarioConfig, rng: np.random.Generator):
        self.env, self.machine_id, self.config, self.rng = env, machine_id, config, rng
        self.resource = simpy.PriorityResource(env, capacity=1)
        self.available = True
        self.failures = 0
        self.downtime = 0.0
        env.process(self._calendar())
        mtbf = config.machine_mtbf_minutes[machine_id] if machine_id < len(config.machine_mtbf_minutes) else 0.0
        if mtbf > 0:
            env.process(self._failure_clock(mtbf))

    def _calendar(self):
        while True:
            minute = int(self.env.now % 1440)
            active = next((w for w in self.config.machine_maintenance if w.machine_id == self.machine_id and w.start <= minute < w.end), None)
            if active:
                self.available = False
                delay = active.end - minute
                self.downtime += delay
                yield self.env.timeout(delay)
                self.available = True
            else:
                yield self.env.timeout(1)

    def _failure_clock(self, mtbf: float):
        while True:
            yield self.env.timeout(float(self.rng.exponential(mtbf)))
            self.available = False
            self.failures += 1
            repair = float(self.rng.exponential(self.config.machine_repair_mean_minutes))
            self.downtime += repair
            yield self.env.timeout(repair)
            self.available = True


class AdvancedMRIModel:
    PRIORITY = {"emergency": 0, "inpatient": 1, "outpatient": 2}

    def __init__(self, env: simpy.Environment, config: AdvancedScenarioConfig, rng: np.random.Generator):
        self.env, self.config, self.rng = env, config, rng
        self.clerks = DynamicCapacity(env, 1, config.clerk_capacity)
        self.radiographers = DynamicCapacity(env, 1, config.radiographer_capacity)
        self.radiologists = DynamicCapacity(env, 1, config.radiologist_capacity)
        self.machines = [MRIMachine(env, i, config, rng) for i in range(config.mri_machines)]
        self.records: list[dict[str, Any]] = []
        self.state: list[dict[str, float]] = []
        self.arrivals = self.cancelled = self.no_shows = self.abandoned = 0
        env.process(self._track_state())

    def _track_state(self):
        while True:
            queue = sum(len(machine.resource.queue) for machine in self.machines)
            busy = sum(machine.resource.count for machine in self.machines)
            available = sum(1 for machine in self.machines if machine.available)
            self.state.append({"time": self.env.now, "mri_queue": queue, "mri_busy": busy, "mri_available": available, "clerk_tokens": self.clerks.container.level, "radiographer_tokens": self.radiographers.container.level, "radiologist_tokens": self.radiologists.container.level})
            yield self.env.timeout(self.config.tracking_interval_minutes)

    def _choose_machine(self) -> MRIMachine:
        candidates = [m for m in self.machines if m.available]
        if not candidates:
            candidates = self.machines
        return min(candidates, key=lambda m: (m.resource.count + len(m.resource.queue), m.machine_id))

    def _service(self, capacity: DynamicCapacity, duration: float):
        yield capacity.request()
        try:
            yield self.env.timeout(duration)
        finally:
            yield capacity.release()

    def patient(self, patient_id: int, patient_type: str, scheduled_time: float | None = None):
        arrival = self.env.now
        if patient_type == "outpatient":
            if self.rng.random() < self.config.cancellation_rate:
                self.cancelled += 1
                return
            if self.rng.random() < self.config.no_show_rate:
                self.no_shows += 1
                return
        self.arrivals += 1
        wait_start = self.env.now
        abandon = self.env.timeout(self.config.abandonment_minutes)
        reception = self.env.process(self._service(self.clerks, float(self.rng.exponential(self.config.reception_mean))))
        outcome = yield reception | abandon
        if abandon in outcome:
            self.abandoned += 1
            return
        yield self.env.process(self._service(self.radiographers, float(self.rng.exponential(self.config.preparation_mean))))
        machine = self._choose_machine()
        request = machine.resource.request(priority=self.PRIORITY[patient_type])
        outcome = yield request | self.env.timeout(self.config.abandonment_minutes)
        if request not in outcome:
            request.cancel()
            self.abandoned += 1
            return
        try:
            while not machine.available:
                yield self.env.timeout(1)
            yield self.env.timeout(max(5.0, float(self.rng.normal(self.config.scan_mean, 8.0))) + self.config.cleaning_minutes)
        finally:
            machine.resource.release(request)
        yield self.env.process(self._service(self.radiologists, float(self.rng.exponential(self.config.report_mean))))
        system = self.env.now - arrival
        self.records.append({"patient_id": patient_id, "patient_type": patient_type, "arrival": arrival, "scheduled_time": scheduled_time, "wait_minutes": self.env.now - wait_start - system + system, "system_minutes": system, "machine_id": machine.machine_id})

    def source(self):
        patient_id = 0
        total_days = self.config.warmup_days + self.config.days
        for day in range(total_days):
            day_start = day * 1440
            weekday_factor = self.config.weekday_multipliers[day % 7]
            month_factor = self.config.seasonal_multipliers[min(11, day // 30)]
            demand = self.config.daily_demand * weekday_factor * month_factor
            events: list[tuple[float, str, float | None]] = []
            # Capacity-aware outpatient slots reserve expected machine minutes and allow controlled overbooking.
            capacity_minutes = self.config.mri_machines * self.config.operating_hours * 60
            expected_slot_minutes = self.config.scan_mean + self.config.cleaning_minutes
            max_slots = int(capacity_minutes / expected_slot_minutes * (1 + self.config.overbooking_rate))
            requested_slots = int(round(demand * self.config.outpatient_share * (1 + self.config.overbooking_rate)))
            slot_count = min(max_slots, requested_slots)
            if slot_count:
                slots = np.linspace(0, self.config.operating_hours * 60 - 1, slot_count)
                for slot in slots:
                    scheduled = day_start + float(slot)
                    actual = max(day_start, scheduled + float(self.rng.normal(0, self.config.appointment_arrival_sd_minutes)))
                    events.append((actual, "outpatient", scheduled))
            inpatient_count = int(self.rng.poisson(demand * self.config.inpatient_share))
            for offset in self.rng.uniform(0, self.config.operating_hours * 60, inpatient_count):
                events.append((day_start + float(offset), "inpatient", None))
            emergency_profile = np.asarray(self.config.emergency_hourly_profile_24h, dtype=float)
            emergency_profile /= emergency_profile.sum()
            for hour, weight in enumerate(emergency_profile):
                count = int(self.rng.poisson(demand * self.config.emergency_share * weight))
                for offset in self.rng.uniform(0, 60, count):
                    events.append((day_start + hour * 60 + float(offset), "emergency", None))
            events.sort(key=lambda item: item[0])
            for event_time, patient_type, scheduled in events:
                if event_time > self.env.now:
                    yield self.env.timeout(event_time - self.env.now)
                patient_id += 1
                self.env.process(self.patient(patient_id, patient_type, scheduled))
            if self.env.now < (day + 1) * 1440:
                yield self.env.timeout((day + 1) * 1440 - self.env.now)


def run_advanced_once(config: AdvancedScenarioConfig, replication: int = 0) -> tuple[AdvancedSimulationResult, pd.DataFrame, pd.DataFrame]:
    config.validate()
    env = simpy.Environment()
    rng = np.random.default_rng(config.seed + replication)
    model = AdvancedMRIModel(env, config, rng)
    env.process(model.source())
    env.run(until=(config.warmup_days + config.days + 1) * 1440)
    frame = pd.DataFrame(model.records)
    state = pd.DataFrame(model.state)
    completed = len(frame)
    eligible = model.arrivals
    result = AdvancedSimulationResult(
        scenario=config.name,
        replication=replication,
        arrivals=model.arrivals,
        completed=completed,
        cancelled=model.cancelled,
        no_shows=model.no_shows,
        abandoned=model.abandoned,
        completion_rate_pct=100.0 * completed / eligible if eligible else 0.0,
        mean_wait_minutes=float(frame["wait_minutes"].mean()) if not frame.empty else 0.0,
        p90_system_minutes=float(frame["system_minutes"].quantile(0.9)) if not frame.empty else 0.0,
        throughput_per_day=completed / config.days,
        mean_queue_length=float(state["mri_queue"].mean()),
        max_queue_length=int(state["mri_queue"].max()),
        mri_failures=sum(m.failures for m in model.machines),
        mri_downtime_minutes=sum(m.downtime for m in model.machines),
        mean_available_mri=float(state["mri_available"].mean()),
    )
    return result, frame, state


def run_advanced_replications(config: AdvancedScenarioConfig, replications: int = 20) -> pd.DataFrame:
    if replications <= 0:
        raise ValueError("replications must be positive")
    return pd.DataFrame(asdict(run_advanced_once(config, i)[0]) for i in range(replications))


def summarise_advanced(results: pd.DataFrame) -> dict[str, float]:
    if results.empty:
        raise ValueError("results must not be empty")
    summary: dict[str, float] = {}
    for column in results.select_dtypes(include=[np.number]).columns:
        values = results[column].astype(float)
        mean = float(values.mean())
        sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        margin = 1.96 * sd / sqrt(len(values)) if len(values) > 1 else 0.0
        summary[column] = mean
        summary[f"{column}_ci95_low"] = mean - margin
        summary[f"{column}_ci95_high"] = mean + margin
    return summary
