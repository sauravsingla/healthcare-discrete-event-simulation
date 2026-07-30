"""Corrected advanced MRI discrete-event simulation engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
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
        0.7,
        0.6,
        0.55,
        0.5,
        0.55,
        0.7,
        0.9,
        1.1,
        1.2,
        1.15,
        1.05,
        1.0,
        1.0,
        1.05,
        1.1,
        1.15,
        1.2,
        1.25,
        1.2,
        1.1,
        1.0,
        0.9,
        0.8,
        0.75,
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
        if self.days <= 0 or self.mri_machines <= 0 or self.daily_demand <= 0:
            raise ValueError("days, mri_machines and daily_demand must be positive")
        if self.warmup_days < 0 or not 0 < self.operating_hours <= 24:
            raise ValueError("invalid warmup_days or operating_hours")
        if not np.isclose(
            self.outpatient_share + self.inpatient_share + self.emergency_share, 1.0, atol=1e-6
        ):
            raise ValueError("patient shares must sum to 1")
        for value in (
            self.overbooking_rate,
            self.cancellation_rate,
            self.no_show_rate,
            self.emergency_capacity_reserve,
        ):
            if not 0 <= value < 1:
                raise ValueError("probabilities and reserve fractions must be in [0, 1)")
        if self.abandonment_minutes <= 0 or self.cancellation_lead_minutes < 0:
            raise ValueError("invalid patience or cancellation lead")
        if len(self.weekday_multipliers) != 7 or len(self.seasonal_multipliers) != 12:
            raise ValueError("weekday and seasonal multipliers require 7 and 12 values")
        if len(self.outpatient_hourly_profile) != self.operating_hours:
            raise ValueError("outpatient_hourly_profile must match operating_hours")
        if len(self.emergency_hourly_profile_24h) != 24:
            raise ValueError("emergency_hourly_profile_24h must contain 24 values")
        profiles = (
            *self.weekday_multipliers,
            *self.seasonal_multipliers,
            *self.outpatient_hourly_profile,
            *self.emergency_hourly_profile_24h,
        )
        if (
            any(value < 0 for value in profiles)
            or sum(self.outpatient_hourly_profile) <= 0
            or sum(self.emergency_hourly_profile_24h) <= 0
        ):
            raise ValueError("demand profiles must be non-negative with positive totals")
        if self.tracking_interval_minutes <= 0 or self.max_drain_minutes < 0:
            raise ValueError("invalid tracking or drain duration")
        if self.termination_policy not in {"horizon", "drain", "bounded_drain"}:
            raise ValueError("invalid termination_policy")
        for window in (
            *self.clerk_capacity,
            *self.radiographer_capacity,
            *self.radiologist_capacity,
        ):
            if not 0 <= window.start < window.end <= 1440 or window.capacity < 0:
                raise ValueError(f"invalid capacity window: {window}")
        for window in self.machine_maintenance:
            if (
                not 0 <= window.machine_id < self.mri_machines
                or not 0 <= window.start < window.end <= 1440
            ):
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
    mean_queue_length: float
    mean_queue_length_open: float
    mean_queue_length_24h: float
    max_queue_length: int
    mri_failures: int
    mri_downtime_minutes: float
    mean_available_mri: float
    mean_available_mri_open: float
    mean_available_mri_24h: float


class DynamicCapacity:
    """Token capacity that safely retires capacity after in-service work completes."""

    def __init__(
        self, env: simpy.Environment, default_capacity: int, windows: tuple[CapacityWindow, ...]
    ):
        self.env = env
        self.default_capacity = default_capacity
        self.windows = windows
        self.maximum = max(default_capacity, *(window.capacity for window in windows), 1)
        initial_capacity = self.target(int(env.now % 1440))
        self.tokens = simpy.Container(env, capacity=self.maximum, init=initial_capacity)
        self.busy = 0
        env.process(self._controller())

    def target(self, minute: int) -> int:
        matches = [
            window.capacity for window in self.windows if window.start <= minute < window.end
        ]
        return max(matches) if matches else self.default_capacity

    def desired_available(self) -> int:
        return max(0, self.target(int(self.env.now % 1440)) - self.busy)

    def rebalance(self):
        desired = self.desired_available()
        current = int(self.tokens.level)
        if desired > current:
            yield self.tokens.put(desired - current)
        elif desired < current:
            yield self.tokens.get(current - desired)

    def _controller(self):
        while True:
            yield self.env.process(self.rebalance())
            yield self.env.timeout(1)

    def release(self):
        if self.busy <= 0:
            raise RuntimeError("dynamic capacity busy count became negative")
        self.busy -= 1
        yield self.env.process(self.rebalance())


class MRIMachine:
    """Scanner state machine coordinating scans, maintenance, failures and repairs."""

    def __init__(
        self,
        env: simpy.Environment,
        machine_id: int,
        config: AdvancedScenarioConfig,
        rng: np.random.Generator,
    ):
        self.env = env
        self.machine_id = machine_id
        self.config = config
        self.rng = rng
        self.resource = simpy.PriorityResource(env, capacity=1)
        self.state = "AVAILABLE"
        self.blockers: set[str] = set()
        self.failures = 0
        self.downtime = 0.0
        self.active_scan: simpy.Process | None = None
        env.process(self._maintenance_calendar())
        mtbf = (
            config.machine_mtbf_minutes[machine_id]
            if machine_id < len(config.machine_mtbf_minutes)
            else 0.0
        )
        if mtbf > 0:
            env.process(self._failure_clock(mtbf))

    @property
    def available(self) -> bool:
        return not self.blockers and self.state == "AVAILABLE" and self.resource.count == 0

    def _maintenance_calendar(self):
        windows = [
            window
            for window in self.config.machine_maintenance
            if window.machine_id == self.machine_id
        ]
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
                    if (
                        not isinstance(interruption.cause, tuple)
                        or interruption.cause[0] != "machine_failure"
                    ):
                        raise
                    elapsed = self.env.now - started
                    remaining = (
                        duration
                        if self.config.restart_scan_after_failure
                        else max(0.0, remaining - elapsed)
                    )
                    while "failure" in self.blockers:
                        yield self.env.timeout(1)
        finally:
            self.active_scan = None
            self.state = "AVAILABLE" if not self.blockers else self.state


class AdvancedMRIModel:
    PRIORITY = {"emergency": 0, "inpatient": 1, "outpatient": 2}

    def __init__(
        self, env: simpy.Environment, config: AdvancedScenarioConfig, rng: np.random.Generator
    ):
        self.env = env
        self.config = config
        self.rng = rng
        self.clerks = DynamicCapacity(env, 1, config.clerk_capacity)
        self.radiographers = DynamicCapacity(env, 1, config.radiographer_capacity)
        self.radiologists = DynamicCapacity(env, 1, config.radiologist_capacity)
        self.machines = [
            MRIMachine(env, index, config, rng) for index in range(config.mri_machines)
        ]
        self.ledger: dict[int, dict[str, Any]] = {}
        self.state: list[dict[str, float | str | bool]] = []
        self.active_patients = 0
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
        token = capacity.tokens.get(1)
        acquired = False
        def mark_acquired(_event):
            nonlocal acquired
            acquired = True
            capacity.busy += 1
        token.callbacks.append(mark_acquired)
        timeout = self.env.timeout(self._remaining_patience(deadline))
        outcome = yield token | timeout
        if token not in outcome:
            if acquired:
                yield self.env.process(capacity.release())
            else:
                token.cancel()
            return None
        yield self.env.process(capacity.rebalance())
        wait = self.env.now - started_wait
        try:
            yield self.env.timeout(duration)
        finally:
            yield self.env.process(capacity.release())
        return wait

    def _acquire_any_machine(self, priority: int, deadline: float):
        while self.env.now < deadline:
            candidates = sorted(
                self.machines,
                key=lambda machine: (
                    machine.resource.count,
                    len(machine.resource.queue),
                    machine.machine_id,
                ),
            )
            for machine in candidates:
                if machine.blockers or machine.resource.count:
                    continue
                request = machine.resource.request(priority=priority)
                result = yield request | self.env.timeout(0)
                if request in result:
                    return machine, request
                request.cancel()
            yield self.env.timeout(min(1.0, self._remaining_patience(deadline)))
        return None

    def _finish(self, patient_id: int, status: str, **fields: Any) -> None:
        self.ledger[patient_id].update(fields, status=status, outcome_time=self.env.now)

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
                    self._timed_staff_service(capacity, duration, deadline)
                )
                if wait is None:
                    self._finish(patient_id, "abandoned", abandonment_stage=stage, **waits)
                    return
                waits[f"{stage}_wait_minutes"] = wait

            mri_started = self.env.now
            acquired = yield self.env.process(
                self._acquire_any_machine(self.PRIORITY[row["patient_type"]], deadline)
            )
            if acquired is None:
                self._finish(patient_id, "abandoned", abandonment_stage="mri", **waits)
                return
            machine, request = acquired
            waits["mri_wait_minutes"] = self.env.now - mri_started
            row["machine_id"] = machine.machine_id
            scan_duration = max(
                5.0, float(self.rng.normal(self.config.scan_mean, self.config.scan_sd))
            )
            try:
                yield self.env.process(machine.scan(scan_duration + self.config.cleaning_minutes))
            finally:
                machine.resource.release(request)

            reporting = yield self.env.process(
                self._timed_staff_service(
                    self.radiologists,
                    float(self.rng.exponential(self.config.report_mean)),
                    deadline,
                )
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
        finally:
            self.active_patients -= 1

    def _calendar_factors(self, day: int) -> tuple[float, float]:
        current = self.config.start_date + timedelta(days=day)
        return self.config.weekday_multipliers[current.weekday()], self.config.seasonal_multipliers[
            current.month - 1
        ]

    def _effective_daily_slots(self, requested: int) -> int:
        open_minutes = self.config.operating_hours * 60
        maintenance = sum(
            min(window.end, open_minutes) - window.start
            for window in self.config.machine_maintenance
            if window.start < open_minutes
        )
        planned_capacity = max(0.0, self.config.mri_machines * open_minutes - maintenance)
        mtbf = [
            value
            for value in self.config.machine_mtbf_minutes[: self.config.mri_machines]
            if value > 0
        ]
        failure_fraction = (
            0.0
            if not mtbf
            else min(
                0.95,
                float(
                    np.mean(
                        [
                            self.config.machine_repair_mean_minutes
                            / (value + self.config.machine_repair_mean_minutes)
                            for value in mtbf
                        ]
                    )
                ),
            )
        )
        usable = (
            planned_capacity * (1 - failure_fraction) * (1 - self.config.emergency_capacity_reserve)
        )
        physical_slots = int(usable / (self.config.scan_mean + self.config.cleaning_minutes))
        return min(int(round(requested * (1 + self.config.overbooking_rate))), physical_slots)

    def source(self):
        patient_id = 0
        total_days = self.config.warmup_days + self.config.days
        open_minutes = self.config.operating_hours * 60
        outpatient_profile = np.asarray(self.config.outpatient_hourly_profile, dtype=float)
        outpatient_profile /= outpatient_profile.sum()
        emergency_profile = np.asarray(self.config.emergency_hourly_profile_24h, dtype=float)
        emergency_profile /= emergency_profile.sum()
        for day in range(total_days):
            day_start = day * 1440
            weekday_factor, month_factor = self._calendar_factors(day)
            demand = self.config.daily_demand * weekday_factor * month_factor
            events: list[tuple[float, int]] = []
            slot_count = self._effective_daily_slots(
                int(round(demand * self.config.outpatient_share))
            )
            if slot_count:
                per_hour = self.rng.multinomial(slot_count, outpatient_profile)
                for hour, count in enumerate(per_hour):
                    spacing = 60.0 / count if count else 0.0
                    for index in range(count):
                        patient_id += 1
                        scheduled = day_start + hour * 60 + index * spacing
                        self.ledger[patient_id] = {
                            "patient_id": patient_id,
                            "patient_type": "outpatient",
                            "booked_time": day_start,
                            "scheduled_time": scheduled,
                            "status": "booked",
                            "entered_system": False,
                        }
                        if self.rng.random() < self.config.cancellation_rate:
                            self.ledger[patient_id].update(
                                status="cancelled",
                                outcome_time=max(
                                    day_start, scheduled - self.config.cancellation_lead_minutes
                                ),
                            )
                            continue
                        jitter = float(
                            self.rng.normal(0, self.config.appointment_arrival_sd_minutes)
                        )
                        events.append(
                            (
                                min(
                                    day_start + open_minutes - 0.01,
                                    max(day_start, scheduled + jitter),
                                ),
                                patient_id,
                            )
                        )

            for offset in self.rng.uniform(
                0, open_minutes, int(self.rng.poisson(demand * self.config.inpatient_share))
            ):
                patient_id += 1
                arrival = day_start + float(offset)
                self.ledger[patient_id] = {
                    "patient_id": patient_id,
                    "patient_type": "inpatient",
                    "booked_time": arrival,
                    "scheduled_time": np.nan,
                    "status": "expected",
                    "entered_system": False,
                }
                events.append((arrival, patient_id))

            for hour, weight in enumerate(emergency_profile):
                for offset in self.rng.uniform(
                    0,
                    60,
                    int(self.rng.poisson(demand * self.config.emergency_share * float(weight))),
                ):
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
