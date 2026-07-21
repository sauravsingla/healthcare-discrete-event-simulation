"""Advanced MRI simulation with reconciled patient outcomes and operational state."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from math import sqrt
from typing import Any, Literal

import numpy as np
import pandas as pd
import simpy


@dataclass(frozen=True)
class CapacityWindow:
    """Explicit total staffed capacity for a minute-of-day interval."""

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
    emergency_hourly_profile_24h: tuple[float, ...] = (
        0.7, 0.6, 0.55, 0.5, 0.55, 0.7, 0.9, 1.1, 1.2, 1.15, 1.05, 1.0,
        1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.2, 1.1, 1.0, 0.9, 0.8, 0.75,
    )
    appointment_interval_minutes: int = 15
    appointment_arrival_sd_minutes: float = 8.0
    overbooking_rate: float = 0.0
    cancellation_rate: float = 0.05
    cancellation_lead_minutes: float = 240.0
    no_show_rate: float = 0.08
    abandonment_minutes: float = 240.0
    mri_machines: int = 4
    machine_maintenance: tuple[MachineWindow, ...] = ()
    machine_mtbf_minutes: tuple[float, ...] = ()
    machine_repair_mean_minutes: float = 60.0
    restart_scan_after_failure: bool = False
    cleaning_minutes: float = 3.0
    clerk_capacity: tuple[CapacityWindow, ...] = ()
    radiographer_capacity: tuple[CapacityWindow, ...] = ()
    radiologist_capacity: tuple[CapacityWindow, ...] = ()
    reception_mean: float = 8.0
    preparation_mean: float = 5.0
    scan_mean: float = 26.46
    scan_sd: float = 8.0
    report_mean: float = 9.0
    emergency_capacity_reserve: float = 0.15
    tracking_interval_minutes: int = 5
    start_date: date = date(2026, 1, 5)
    termination_policy: Literal["horizon", "drain", "bounded_drain"] = "bounded_drain"
    max_drain_minutes: int = 1440
    bootstrap_samples: int = 2000
    seed: int = 17

    def validate(self) -> None:
        if self.days <= 0 or self.mri_machines <= 0:
            raise ValueError("days and mri_machines must be positive")
        if self.warmup_days < 0:
            raise ValueError("warmup_days must be non-negative")
        if not 0 < self.operating_hours <= 24:
            raise ValueError("operating_hours must be in (0, 24]")
        if self.daily_demand <= 0:
            raise ValueError("daily_demand must be positive")
        shares = self.outpatient_share + self.inpatient_share + self.emergency_share
        if not np.isclose(shares, 1.0, atol=1e-6):
            raise ValueError("patient shares must sum to 1")
        for value in (self.overbooking_rate, self.cancellation_rate, self.no_show_rate, self.emergency_capacity_reserve):
            if not 0 <= value < 1:
                raise ValueError("probabilities and reserve fractions must be in [0, 1)")
        if self.abandonment_minutes <= 0 or self.cancellation_lead_minutes < 0:
            raise ValueError("patience must be positive and cancellation lead non-negative")
        if len(self.weekday_multipliers) != 7 or len(self.seasonal_multipliers) != 12:
            raise ValueError("weekday and seasonal multipliers require 7 and 12 values")
        if len(self.emergency_hourly_profile_24h) != 24:
            raise ValueError("emergency_hourly_profile_24h must contain 24 values")
        if len(self.outpatient_hourly_profile) != self.operating_hours:
            raise ValueError("outpatient_hourly_profile must match operating_hours")
        if any(value < 0 for value in (*self.weekday_multipliers, *self.seasonal_multipliers, *self.outpatient_hourly_profile, *self.emergency_hourly_profile_24h)):
            raise ValueError("demand profiles must be non-negative")
        if not 0 < self.tracking_interval_minutes or self.max_drain_minutes < 0:
            raise ValueError("tracking interval must be positive and max drain non-negative")
        if self.termination_policy not in {"horizon", "drain", "bounded_drain"}:
            raise ValueError("invalid termination_policy")
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
    booked: int
    cancelled: int
    expected_arrivals: int
    no_shows: int
    arrivals: int
    completed: int
    abandoned: int
    unfinished: int
    completion_rate_pct: float
    mean_wait_minutes: float
    mean_reception_wait_minutes: float
    mean_preparation_wait_minutes: float
    mean_mri_wait_minutes: float
    mean_reporting_wait_minutes: float
    mean_system_minutes: float
    p90_system_minutes: float
    throughput_per_day: float
    mean_queue_length_open: float
    mean_queue_length_24h: float
    max_queue_length: int
    mri_failures: int
    mri_downtime_minutes: float
    mean_available_mri_open: float
    mean_available_mri_24h: float


class DynamicCapacity:
    """Capacity gate that honours reductions while staff are already busy."""

    def __init__(self, env: simpy.Environment, default_capacity: int, windows: tuple[CapacityWindow, ...]):
        self.env = env
        self.default_capacity = default_capacity
        self.windows = windows
        self.maximum = max(default_capacity, *(window.capacity for window in windows), 1)
        self.tokens = simpy.Container(env, capacity=self.maximum, init=default_capacity)
        self.busy = 0
        env.process(self._controller())

    def target(self, minute: int) -> int:
        matches = [window.capacity for window in self.windows if window.start <= minute < window.end]
        return max(matches) if matches else self.default_capacity

    def _desired_available(self) -> int:
        return max(0, self.target(int(self.env.now % 1440)) - self.busy)

    def _rebalance(self):
        desired = self._desired_available()
        current = int(self.tokens.level)
        if desired > current:
            yield self.tokens.put(desired - current)
        elif desired < current:
            yield self.tokens.get(current - desired)

    def _controller(self):
        while True:
            yield self.env.process(self._rebalance())
            yield self.env.timeout(1)

    def acquire(self):
        yield self.tokens.get(1)
        self.busy += 1
        yield self.env.process(self._rebalance())

    def release(self):
        self.busy -= 1
        if self.busy < 0:
            raise RuntimeError("dynamic capacity busy count became negative")
        yield self.env.process(self._rebalance())


class MRIMachine:
    """One scanner with coordinated busy, failure, repair and maintenance state."""

    def __init__(self, env: simpy.Environment, machine_id: int, config: AdvancedScenarioConfig, rng: np.random.Generator):
        self.env = env
        self.machine_id = machine_id
        self.config = config
        self.rng = rng
        self.resource = simpy.PriorityResource(env, capacity=1)
        self.state = "AVAILABLE"
        self.failures = 0
        self.downtime = 0.0
        self.active_scan: simpy.Process | None = None
        self.blockers: set[str] = set()
        env.process(self._maintenance_calendar())
        mtbf = config.machine_mtbf_minutes[machine_id] if machine_id < len(config.machine_mtbf_minutes) else 0.0
        if mtbf > 0:
            env.process(self._failure_clock(mtbf))

    @property
    def available(self) -> bool:
        return not self.blockers and self.state == "AVAILABLE" and self.resource.count == 0

    def _maintenance_calendar(self):
        windows = [window for window in self.config.machine_maintenance if window.machine_id == self.machine_id]
        while True:
            minute = int(self.env.now % 1440)
            upcoming = [window for window in windows if window.start >= minute]
            if not upcoming:
                yield self.env.timeout(1440 - minute)
                continue
            window = min(upcoming, key=lambda item: item.start)
            yield self.env.timeout(max(0, window.start - minute))
            with self.resource.request(priority=-20) as request:
                yield request
                self.blockers.add("maintenance")
                self.state = "MAINTENANCE"
                duration = float(window.end - window.start)
                self.downtime += duration
                yield self.env.timeout(duration)
                self.blockers.discard("maintenance")
                self.state = "AVAILABLE" if not self.blockers else self.state

    def _failure_clock(self, mtbf: float):
        while True:
            yield self.env.timeout(float(self.rng.exponential(mtbf)))
            if "maintenance" in self.blockers:
                continue
            self.failures += 1
            self.blockers.add("failure")
            self.state = "FAILED"
            if self.active_scan is not None and self.active_scan.is_alive:
                self.active_scan.interrupt(("machine_failure", self.machine_id))
            repair = float(self.rng.exponential(self.config.machine_repair_mean_minutes))
            self.state = "REPAIR"
            self.downtime += repair
            yield self.env.timeout(repair)
            self.blockers.discard("failure")
            self.state = "AVAILABLE" if not self.blockers and self.resource.count == 0 else "BUSY"

    def scan(self, duration: float):
        remaining = duration
        self.active_scan = self.env.active_process
        try:
            while remaining > 0:
                while self.blockers:
                    yield self.env.timeout(1)
                self.state = "BUSY"
                started = self.env.now
                try:
                    yield self.env.timeout(remaining)
                    remaining = 0
                except simpy.Interrupt as interruption:
                    if not isinstance(interruption.cause, tuple) or interruption.cause[0] != "machine_failure":
                        raise
                    elapsed = self.env.now - started
                    remaining = duration if self.config.restart_scan_after_failure else max(0.0, remaining - elapsed)
                    while "failure" in self.blockers:
                        yield self.env.timeout(1)
        finally:
            self.active_scan = None
            self.state = "AVAILABLE" if not self.blockers else self.state


class AdvancedMRIModel:
    PRIORITY = {"emergency": 0, "inpatient": 1, "outpatient": 2}

    def __init__(self, env: simpy.Environment, config: AdvancedScenarioConfig, rng: np.random.Generator):
        self.env = env
        self.config = config
        self.rng = rng
        self.clerks = DynamicCapacity(env, 1, config.clerk_capacity)
        self.radiographers = DynamicCapacity(env, 1, config.radiographer_capacity)
        self.radiologists = DynamicCapacity(env, 1, config.radiologist_capacity)
        self.machines = [MRIMachine(env, index, config, rng) for index in range(config.mri_machines)]
        self.ledger: dict[int, dict[str, Any]] = {}
        self.state: list[dict[str, float | str]] = []
        self.active_patients = 0
        self.source_finished = False
        env.process(self._track_state())

    def _track_state(self):
        while True:
            minute = int(self.env.now % 1440)
            self.state.append(
                {
                    "time": self.env.now,
                    "minute_of_day": minute,
                    "is_open": minute < self.config.operating_hours * 60,
                    "mri_queue": sum(len(machine.resource.queue) for machine in self.machines),
                    "mri_busy": sum(machine.resource.count for machine in self.machines),
                    "mri_available": sum(machine.available for machine in self.machines),
                    "clerk_target": self.clerks.target(minute),
                    "clerk_busy": self.clerks.busy,
                    "clerk_tokens": self.clerks.tokens.level,
                    "radiographer_target": self.radiographers.target(minute),
                    "radiographer_busy": self.radiographers.busy,
                    "radiographer_tokens": self.radiographers.tokens.level,
                    "radiologist_target": self.radiologists.target(minute),
                    "radiologist_busy": self.radiologists.busy,
                    "radiologist_tokens": self.radiologists.tokens.level,
                    "machine_states": "|".join(machine.state for machine in self.machines),
                }
            )
            yield self.env.timeout(self.config.tracking_interval_minutes)

    def _remaining_patience(self, deadline: float) -> float:
        return max(0.0, deadline - self.env.now)

    def _timed_staff_service(self, capacity: DynamicCapacity, duration: float, deadline: float):
        started_wait = self.env.now
        acquire = self.env.process(capacity.acquire())
        timeout = self.env.timeout(self._remaining_patience(deadline))
        outcome = yield acquire | timeout
        if acquire not in outcome:
            acquire.interrupt("abandoned")
            return None
        wait = self.env.now - started_wait
        try:
            yield self.env.timeout(duration)
        finally:
            yield self.env.process(capacity.release())
        return wait

    def _acquire_any_machine(self, priority: int, deadline: float):
        while self.env.now < deadline:
            candidates = sorted(self.machines, key=lambda machine: (machine.resource.count, len(machine.resource.queue), machine.machine_id))
            for machine in candidates:
                if machine.blockers or machine.resource.count:
                    continue
                request = machine.resource.request(priority=priority)
                result = yield request | self.env.timeout(0)
                if request in result:
                    return machine, request, self.env.now
                request.cancel()
            yield self.env.timeout(min(1.0, self._remaining_patience(deadline)))
        return None

    def _finish(self, patient_id: int, status: str, **fields: Any) -> None:
        row = self.ledger[patient_id]
        row.update(fields)
        row["status"] = status
        row["outcome_time"] = self.env.now

    def patient(self, patient_id: int):
        row = self.ledger[patient_id]
        self.active_patients += 1
        try:
            arrival = self.env.now
            row["arrival"] = arrival
            if row["patient_type"] == "outpatient" and self.rng.random() < self.config.no_show_rate:
                self._finish(patient_id, "no_show")
                return
            row["entered_system"] = True
            deadline = arrival + self.config.abandonment_minutes
            waits: dict[str, float] = {}

            reception = yield self.env.process(
                self._timed_staff_service(self.clerks, float(self.rng.exponential(self.config.reception_mean)), deadline)
            )
            if reception is None:
                self._finish(patient_id, "abandoned", abandonment_stage="reception")
                return
            waits["reception_wait_minutes"] = reception

            preparation = yield self.env.process(
                self._timed_staff_service(self.radiographers, float(self.rng.exponential(self.config.preparation_mean)), deadline)
            )
            if preparation is None:
                self._finish(patient_id, "abandoned", abandonment_stage="preparation")
                return
            waits["preparation_wait_minutes"] = preparation

            mri_queue_start = self.env.now
            acquired = yield self.env.process(self._acquire_any_machine(self.PRIORITY[row["patient_type"]], deadline))
            if acquired is None:
                self._finish(patient_id, "abandoned", abandonment_stage="mri")
                return
            machine, request, _ = acquired
            waits["mri_wait_minutes"] = self.env.now - mri_queue_start
            row["machine_id"] = machine.machine_id
            scan_duration = max(5.0, float(self.rng.normal(self.config.scan_mean, self.config.scan_sd)))
            try:
                yield self.env.process(machine.scan(scan_duration + self.config.cleaning_minutes))
            finally:
                machine.resource.release(request)

            reporting = yield self.env.process(
                self._timed_staff_service(self.radiologists, float(self.rng.exponential(self.config.report_mean)), deadline)
            )
            if reporting is None:
                self._finish(patient_id, "abandoned", abandonment_stage="reporting", **waits)
                return
            waits["reporting_wait_minutes"] = reporting
            total_wait = sum(waits.values())
            self._finish(
                patient_id,
                "completed",
                **waits,
                wait_minutes=total_wait,
                service_minutes=self.env.now - arrival - total_wait,
                system_minutes=self.env.now - arrival,
            )
        except simpy.Interrupt:
            self._finish(patient_id, "abandoned", abandonment_stage="interrupted")
        finally:
            self.active_patients -= 1

    def _calendar_factors(self, day: int) -> tuple[float, float]:
        current = self.config.start_date + timedelta(days=day)
        return self.config.weekday_multipliers[current.weekday()], self.config.seasonal_multipliers[current.month - 1]

    def _effective_daily_slots(self, day_start: float, requested: int) -> int:
        open_minutes = self.config.operating_hours * 60
        maintenance = sum(
            window.end - window.start
            for window in self.config.machine_maintenance
            if window.start < open_minutes
        )
        planned_capacity = max(0.0, self.config.mri_machines * open_minutes - maintenance)
        expected_failure_fraction = 0.0
        mtbf = [value for value in self.config.machine_mtbf_minutes[: self.config.mri_machines] if value > 0]
        if mtbf:
            expected_failure_fraction = min(
                0.95,
                float(np.mean([self.config.machine_repair_mean_minutes / (value + self.config.machine_repair_mean_minutes) for value in mtbf])),
            )
        usable = planned_capacity * (1 - expected_failure_fraction) * (1 - self.config.emergency_capacity_reserve)
        expected_scan = self.config.scan_mean + self.config.cleaning_minutes
        physical_slots = int(usable / expected_scan)
        return min(int(round(requested * (1 + self.config.overbooking_rate))), physical_slots)

    def source(self):
        patient_id = 0
        total_days = self.config.warmup_days + self.config.days
        open_minutes = self.config.operating_hours * 60
        profile = np.asarray(self.config.outpatient_hourly_profile, dtype=float)
        profile = profile / profile.sum()
        emergency_profile = np.asarray(self.config.emergency_hourly_profile_24h, dtype=float)
        emergency_profile = emergency_profile / emergency_profile.sum()
        for day in range(total_days):
            day_start = day * 1440
            weekday_factor, month_factor = self._calendar_factors(day)
            demand = self.config.daily_demand * weekday_factor * month_factor
            events: list[tuple[float, int]] = []

            requested_outpatients = int(round(demand * self.config.outpatient_share))
            slot_count = self._effective_daily_slots(day_start, requested_outpatients)
            if slot_count:
                per_hour = self.rng.multinomial(slot_count, profile)
                for hour, count in enumerate(per_hour):
                    if count == 0:
                        continue
                    hour_start = hour * 60
                    spacing = 60.0 / count
                    for index in range(count):
                        patient_id += 1
                        scheduled = day_start + hour_start + index * spacing
                        row = {
                            "patient_id": patient_id,
                            "patient_type": "outpatient",
                            "booked_time": self.env.now,
                            "scheduled_time": scheduled,
                            "status": "booked",
                            "entered_system": False,
                        }
                        self.ledger[patient_id] = row
                        if self.rng.random() < self.config.cancellation_rate:
                            cancellation_time = max(day_start, scheduled - self.config.cancellation_lead_minutes)
                            row.update(status="cancelled", outcome_time=cancellation_time)
                            continue
                        jitter = float(self.rng.normal(0, self.config.appointment_arrival_sd_minutes))
                        actual = min(day_start + open_minutes - 0.01, max(day_start, scheduled + jitter))
                        events.append((actual, patient_id))

            inpatient_count = int(self.rng.poisson(demand * self.config.inpatient_share))
            for offset in self.rng.uniform(0, open_minutes, inpatient_count):
                patient_id += 1
                self.ledger[patient_id] = {
                    "patient_id": patient_id,
                    "patient_type": "inpatient",
                    "booked_time": day_start + float(offset),
                    "scheduled_time": np.nan,
                    "status": "expected",
                    "entered_system": False,
                }
                events.append((day_start + float(offset), patient_id))

            for hour, weight in enumerate(emergency_profile):
                count = int(self.rng.poisson(demand * self.config.emergency_share * float(weight)))
                for offset in self.rng.uniform(0, 60, count):
                    patient_id += 1
                    arrival = day_start + hour * 60 + float(offset)
                    self.ledger[patient_id] = {
                        "patient_id": patient_id,
                        "patient_type": "emergency",
                        "booked_time": arrival,
                        "scheduled_time": np.nan,
                        "status": "expected",
                        "entered_system": False,
                    }
                    events.append((arrival, patient_id))

            events.sort(key=lambda item: item[0])
            for event_time, event_patient_id in events:
                if event_time > self.env.now:
                    yield self.env.timeout(event_time - self.env.now)
                self.env.process(self.patient(event_patient_id))
            next_day = (day + 1) * 1440
            if self.env.now < next_day:
                yield self.env.timeout(next_day - self.env.now)
        self.source_finished = True


def _bootstrap_interval(values: pd.Series, rng: np.random.Generator, samples: int) -> tuple[float, float]:
    array = values.to_numpy(dtype=float)
    if len(array) <= 1 or samples <= 0:
        mean = float(array.mean()) if len(array) else 0.0
        return mean, mean
    means = np.empty(samples)
    for index in range(samples):
        means[index] = rng.choice(array, size=len(array), replace=True).mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def run_advanced_once(config: AdvancedScenarioConfig, replication: int = 0) -> tuple[AdvancedSimulationResult, pd.DataFrame, pd.DataFrame]:
    config.validate()
    env = simpy.Environment()
    rng = np.random.default_rng(config.seed + replication)
    model = AdvancedMRIModel(env, config, rng)
    env.process(model.source())
    arrival_horizon = (config.warmup_days + config.days) * 1440
    if config.termination_policy == "horizon":
        env.run(until=arrival_horizon)
    elif config.termination_policy == "bounded_drain":
        env.run(until=arrival_horizon + config.max_drain_minutes)
    else:
        env.run()

    measurement_start = config.warmup_days * 1440
    measurement_end = arrival_horizon
    frame = pd.DataFrame(model.ledger.values())
    if frame.empty:
        frame = pd.DataFrame(columns=["patient_id", "patient_type", "status", "booked_time", "arrival"])
    frame = frame.loc[
        (frame["booked_time"].astype(float) >= measurement_start)
        & (frame["booked_time"].astype(float) < measurement_end)
    ].copy()
    terminal = {"completed", "cancelled", "no_show", "abandoned"}
    frame.loc[~frame["status"].isin(terminal), "status"] = "unfinished"

    state = pd.DataFrame(model.state)
    state = state.loc[(state["time"] >= measurement_start) & (state["time"] < env.now)].copy()
    completed_frame = frame.loc[frame["status"] == "completed"]
    open_state = state.loc[state["is_open"].astype(bool)]

    booked = int((frame["patient_type"] == "outpatient").sum())
    cancelled = int((frame["status"] == "cancelled").sum())
    expected_arrivals = int(len(frame) - cancelled)
    no_shows = int((frame["status"] == "no_show").sum())
    arrivals = int(frame["entered_system"].fillna(False).astype(bool).sum())
    completed = int((frame["status"] == "completed").sum())
    abandoned = int((frame["status"] == "abandoned").sum())
    unfinished = int((frame["status"] == "unfinished").sum())

    def mean_column(name: str) -> float:
        return float(completed_frame[name].fillna(0).mean()) if not completed_frame.empty and name in completed_frame else 0.0

    result = AdvancedSimulationResult(
        scenario=config.name,
        replication=replication,
        booked=booked,
        cancelled=cancelled,
        expected_arrivals=expected_arrivals,
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
        p90_system_minutes=float(completed_frame["system_minutes"].quantile(0.9)) if not completed_frame.empty else 0.0,
        throughput_per_day=completed / config.days,
        mean_queue_length_open=float(open_state["mri_queue"].mean()) if not open_state.empty else 0.0,
        mean_queue_length_24h=float(state["mri_queue"].mean()) if not state.empty else 0.0,
        max_queue_length=int(state["mri_queue"].max()) if not state.empty else 0,
        mri_failures=sum(machine.failures for machine in model.machines),
        mri_downtime_minutes=sum(machine.downtime for machine in model.machines),
        mean_available_mri_open=float(open_state["mri_available"].mean()) if not open_state.empty else 0.0,
        mean_available_mri_24h=float(state["mri_available"].mean()) if not state.empty else 0.0,
    )
    return result, frame.reset_index(drop=True), state.reset_index(drop=True)


def run_advanced_replications(config: AdvancedScenarioConfig, replications: int = 20) -> pd.DataFrame:
    if replications <= 0:
        raise ValueError("replications must be positive")
    return pd.DataFrame(asdict(run_advanced_once(config, index)[0]) for index in range(replications))


def summarise_advanced(results: pd.DataFrame, bootstrap_samples: int = 2000, seed: int = 17) -> dict[str, float]:
    """Summarise replications using means, SDs and bootstrap percentile intervals."""
    if results.empty:
        raise ValueError("results must not be empty")
    rng = np.random.default_rng(seed)
    summary: dict[str, float] = {}
    for column in results.select_dtypes(include=[np.number]).columns:
        values = results[column].astype(float)
        mean = float(values.mean())
        sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        low, high = _bootstrap_interval(values, rng, bootstrap_samples)
        summary[column] = mean
        summary[f"{column}_sd"] = sd
        summary[f"{column}_ci95_low"] = low
        summary[f"{column}_ci95_high"] = high
    return summary
