"""Core SimPy model for MRI patient flow and capacity experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd
import simpy

PATIENT_TYPES = ("outpatient", "inpatient", "emergency")
DEFAULT_HOURLY_PROFILE = (1.15, 1.30, 1.20, 0.85, 0.70, 1.10, 1.05, 0.65)


@dataclass(frozen=True)
class ScenarioConfig:
    name: str = "baseline"
    days: int = 30
    warmup_days: int = 0
    drain_until_empty: bool = False
    operating_hours: int = 8
    daily_demand: float = 70.0
    outpatient_share: float = 0.57
    inpatient_share: float = 0.2408
    emergency_share: float = 0.1892
    no_show_rate: float = 0.08
    hourly_arrival_profile: tuple[float, ...] = ()
    appointment_interval_minutes: int = 15
    appointment_arrival_sd_minutes: float = 8.0
    mri_machines: int = 4
    clerks: int = 1
    radiographers: int = 4
    radiologists: int = 1
    reception_mean: float = 8.0
    preparation_low: float = 4.0
    preparation_mode: float = 5.0
    preparation_high: float = 6.0
    scan_mean: float = 26.46
    scan_sd_outpatient: float = 20.47
    scan_sd_inpatient: float = 25.47
    scan_sd_emergency: float = 30.47
    report_low: float = 6.0
    report_high: float = 12.0
    cleaning_minutes: float = 3.0
    planned_mri_maintenance: tuple[tuple[int, int], ...] = ()
    mri_failure_probability: float = 0.0
    mri_repair_mean_minutes: float = 60.0
    clerk_shifts: tuple[tuple[int, int], ...] = ()
    radiographer_shifts: tuple[tuple[int, int], ...] = ()
    radiologist_shifts: tuple[tuple[int, int], ...] = ()
    staff_breaks: tuple[tuple[int, int], ...] = ()
    seed: int = 17

    def validate(self) -> None:
        shares = (self.outpatient_share, self.inpatient_share, self.emergency_share)
        if any(share < 0 for share in shares):
            raise ValueError("Patient shares must be non-negative")
        if not np.isclose(sum(shares), 1.0, atol=1e-6):
            raise ValueError(f"Patient shares must sum to 1.0, got {sum(shares):.6f}")
        for field in ("days", "mri_machines", "clerks", "radiographers", "radiologists"):
            if getattr(self, field) <= 0:
                raise ValueError(f"{field} must be positive")
        if self.warmup_days < 0:
            raise ValueError("warmup_days must be non-negative")
        if not 0 < self.operating_hours <= 24:
            raise ValueError("operating_hours must be in (0, 24]")
        if self.daily_demand <= 0:
            raise ValueError("daily_demand must be positive")
        if not 0 <= self.no_show_rate < 1:
            raise ValueError("no_show_rate must be in [0, 1)")
        if self.hourly_arrival_profile and (any(value < 0 for value in self.hourly_arrival_profile) or sum(self.hourly_arrival_profile) <= 0):
            raise ValueError("hourly_arrival_profile must contain non-negative demand weights")
        if self.appointment_interval_minutes <= 0:
            raise ValueError("appointment_interval_minutes must be positive")
        if self.appointment_arrival_sd_minutes < 0:
            raise ValueError("appointment_arrival_sd_minutes must be non-negative")
        if self.reception_mean <= 0:
            raise ValueError("reception_mean must be positive")
        if not 0 <= self.preparation_low <= self.preparation_mode <= self.preparation_high:
            raise ValueError("Preparation times must satisfy 0 <= low <= mode <= high")
        if self.scan_mean <= 0:
            raise ValueError("scan_mean must be positive")
        if any(value < 0 for value in (self.scan_sd_outpatient, self.scan_sd_inpatient, self.scan_sd_emergency)):
            raise ValueError("Scan standard deviations must be non-negative")
        if not 0 <= self.report_low <= self.report_high:
            raise ValueError("Report times must satisfy 0 <= low <= high")
        if self.cleaning_minutes < 0:
            raise ValueError("cleaning_minutes must be non-negative")
        if not 0 <= self.mri_failure_probability <= 1:
            raise ValueError("mri_failure_probability must be in [0, 1]")
        if self.mri_repair_mean_minutes <= 0:
            raise ValueError("mri_repair_mean_minutes must be positive")
        for name, windows in (("planned_mri_maintenance", self.planned_mri_maintenance), ("clerk_shifts", self.clerk_shifts), ("radiographer_shifts", self.radiographer_shifts), ("radiologist_shifts", self.radiologist_shifts), ("staff_breaks", self.staff_breaks)):
            for start, end in windows:
                if not 0 <= start < end <= self.operating_hours * 60:
                    raise ValueError(f"Invalid {name} window: {(start, end)}")


@dataclass(frozen=True)
class SimulationResult:
    scenario: str
    replication: int
    arrivals: int
    completed: int
    no_shows: int
    unfinished: int
    completion_rate_pct: float
    mean_wait_minutes: float
    mean_reception_wait_minutes: float
    mean_preparation_wait_minutes: float
    mean_mri_wait_minutes: float
    mean_reporting_wait_minutes: float
    mean_system_minutes: float
    p90_system_minutes: float
    completed_within_120_pct: float
    throughput_per_day: float
    clerk_utilisation_pct: float
    radiographer_utilisation_pct: float
    mri_utilisation_pct: float
    radiologist_utilisation_pct: float
    outpatient_mean_wait_minutes: float
    outpatient_mean_system_minutes: float
    outpatient_completed_within_120_pct: float
    inpatient_mean_wait_minutes: float
    inpatient_mean_system_minutes: float
    inpatient_completed_within_120_pct: float
    emergency_mean_wait_minutes: float
    emergency_mean_system_minutes: float
    emergency_completed_within_120_pct: float
    mri_failures: int
    mri_downtime_minutes: float


class MRIModel:
    """MRI patient-flow model with appointments and operational calendars."""

    PRIORITY = {"emergency": 0, "inpatient": 1, "outpatient": 2}

    def __init__(self, env: simpy.Environment, config: ScenarioConfig, rng: np.random.Generator):
        self.env = env
        self.config = config
        self.rng = rng
        self.clerks = simpy.Resource(env, capacity=config.clerks)
        self.radiographers = simpy.Resource(env, capacity=config.radiographers)
        self.mri = simpy.PriorityResource(env, capacity=config.mri_machines)
        self.radiologists = simpy.Resource(env, capacity=config.radiologists)
        self.records: list[dict[str, Any]] = []
        self.measurement_start = config.warmup_days * 1440
        self.arrivals = 0
        self.no_shows = 0
        self.mri_failures = 0
        self.mri_downtime_minutes = 0.0
        self.busy_minutes = {"clerks": 0.0, "radiographers": 0.0, "mri": 0.0, "radiologists": 0.0}

    def scan_time(self, patient_type: str) -> float:
        sd = {"outpatient": self.config.scan_sd_outpatient, "inpatient": self.config.scan_sd_inpatient, "emergency": self.config.scan_sd_emergency}[patient_type]
        return max(5.0, float(self.rng.normal(self.config.scan_mean, sd)))

    def _record_busy(self, resource: str, service_time: float, measured: bool) -> None:
        if measured:
            self.busy_minutes[resource] += service_time

    def _next_available_delay(self, windows: tuple[tuple[int, int], ...], include_breaks: bool = True) -> float:
        open_minutes = self.config.operating_hours * 60
        minute = self.env.now % 1440
        if minute >= open_minutes:
            return 1440 - minute
        active = windows or ((0, open_minutes),)
        allowed = any(start <= minute < end for start, end in active)
        in_break = include_breaks and any(start <= minute < end for start, end in self.config.staff_breaks)
        if allowed and not in_break:
            return 0.0
        candidates = [start - minute for start, _ in active if start > minute]
        if in_break:
            candidates.extend(end - minute for start, end in self.config.staff_breaks if start <= minute < end)
        return float(min((value for value in candidates if value > 0), default=1440 - minute))

    def _maintenance_delay(self) -> float:
        minute = self.env.now % 1440
        for start, end in self.config.planned_mri_maintenance:
            if start <= minute < end:
                return float(end - minute)
        return 0.0

    def patient(self, patient_id: int, patient_type: str, scheduled_time: float | None = None):
        arrival = self.env.now
        measured = arrival >= self.measurement_start
        if patient_type == "outpatient" and self.rng.random() < self.config.no_show_rate:
            if measured:
                self.no_shows += 1
            return
        stage_waits: dict[str, float] = {}
        delay = self._next_available_delay(self.config.clerk_shifts)
        if delay:
            yield self.env.timeout(delay)
        queue_start = self.env.now
        with self.clerks.request() as request:
            yield request
            stage_waits["reception_wait_minutes"] = self.env.now - queue_start
            service = float(self.rng.exponential(self.config.reception_mean))
            self._record_busy("clerks", service, measured)
            yield self.env.timeout(service)
        delay = self._next_available_delay(self.config.radiographer_shifts)
        if delay:
            yield self.env.timeout(delay)
        queue_start = self.env.now
        with self.radiographers.request() as request:
            yield request
            stage_waits["preparation_wait_minutes"] = self.env.now - queue_start
            service = float(self.rng.triangular(self.config.preparation_low, self.config.preparation_mode, self.config.preparation_high))
            self._record_busy("radiographers", service, measured)
            yield self.env.timeout(service)
        maintenance_delay = self._maintenance_delay()
        if maintenance_delay:
            if measured:
                self.mri_downtime_minutes += maintenance_delay
            yield self.env.timeout(maintenance_delay)
        queue_start = self.env.now
        with self.mri.request(priority=self.PRIORITY[patient_type]) as request:
            yield request
            stage_waits["mri_wait_minutes"] = self.env.now - queue_start
            service = self.scan_time(patient_type) + self.config.cleaning_minutes
            self._record_busy("mri", service, measured)
            yield self.env.timeout(service)
            if self.rng.random() < self.config.mri_failure_probability:
                repair = float(self.rng.exponential(self.config.mri_repair_mean_minutes))
                if measured:
                    self.mri_failures += 1
                    self.mri_downtime_minutes += repair
                yield self.env.timeout(repair)
        delay = self._next_available_delay(self.config.radiologist_shifts)
        if delay:
            yield self.env.timeout(delay)
        queue_start = self.env.now
        with self.radiologists.request() as request:
            yield request
            stage_waits["reporting_wait_minutes"] = self.env.now - queue_start
            service = float(self.rng.uniform(self.config.report_low, self.config.report_high))
            self._record_busy("radiologists", service, measured)
            yield self.env.timeout(service)
        if measured:
            system_time = self.env.now - arrival
            self.records.append({"patient_id": patient_id, "patient_type": patient_type, "arrival": arrival, "scheduled_time": scheduled_time, "arrival_deviation_minutes": (arrival - scheduled_time) if scheduled_time is not None else np.nan, **stage_waits, "wait_minutes": sum(stage_waits.values()), "system_minutes": system_time})

    def _launch(self, patient_id: int, patient_type: str, scheduled_time: float | None = None) -> None:
        if self.env.now >= self.measurement_start:
            self.arrivals += 1
        self.env.process(self.patient(patient_id, patient_type, scheduled_time))

    def source(self):
        total_days = self.config.warmup_days + self.config.days
        open_minutes = self.config.operating_hours * 60
        raw_profile = np.asarray(self.config.hourly_arrival_profile or DEFAULT_HOURLY_PROFILE, dtype=float)
        profile = np.interp(np.linspace(0, 1, self.config.operating_hours), np.linspace(0, 1, len(raw_profile)), raw_profile)
        profile = profile / profile.sum()
        outpatient_daily = self.config.daily_demand * self.config.outpatient_share
        unscheduled_daily = self.config.daily_demand * (self.config.inpatient_share + self.config.emergency_share)
        denominator = self.config.inpatient_share + self.config.emergency_share
        inpatient_probability = self.config.inpatient_share / denominator if denominator else 0.0
        patient_id = 0
        for day in range(total_days):
            day_start = day * 1440
            events: list[tuple[float, str, float | None]] = []
            slots = np.arange(0, open_minutes, self.config.appointment_interval_minutes, dtype=float)
            slot_count = min(len(slots), int(round(outpatient_daily)))
            for slot in slots[:slot_count]:
                jitter = float(self.rng.normal(0.0, self.config.appointment_arrival_sd_minutes))
                arrival_time = max(day_start, min(day_start + open_minutes - 0.01, day_start + slot + jitter))
                events.append((arrival_time, "outpatient", day_start + float(slot)))
            for hour, weight in enumerate(profile):
                count = int(self.rng.poisson(unscheduled_daily * float(weight)))
                for offset in self.rng.uniform(0, 60, count):
                    patient_type = "inpatient" if self.rng.random() < inpatient_probability else "emergency"
                    events.append((day_start + hour * 60 + float(offset), patient_type, None))
            events.sort(key=lambda event: event[0])
            for arrival_time, patient_type, scheduled_time in events:
                delay = arrival_time - self.env.now
                if delay > 0:
                    yield self.env.timeout(delay)
                patient_id += 1
                self._launch(patient_id, patient_type, scheduled_time)
            next_day = (day + 1) * 1440
            if self.env.now < next_day:
                yield self.env.timeout(next_day - self.env.now)


def _utilisation_pct(busy_minutes: float, capacity: int, scheduled_minutes: float) -> float:
    return float(busy_minutes / (capacity * scheduled_minutes) * 100.0)


def _patient_type_metrics(frame: pd.DataFrame, patient_type: str) -> tuple[float, float, float]:
    subset = frame.loc[frame["patient_type"] == patient_type]
    if subset.empty:
        return 0.0, 0.0, 0.0
    system = subset["system_minutes"].astype(float)
    return float(subset["wait_minutes"].mean()), float(system.mean()), float((system <= 120).mean() * 100)


def run_once(config: ScenarioConfig, replication: int = 0) -> tuple[SimulationResult, pd.DataFrame]:
    config.validate()
    rng = np.random.default_rng(config.seed + replication)
    env = simpy.Environment()
    model = MRIModel(env, config, rng)
    env.process(model.source())
    arrival_horizon = (config.warmup_days + config.days) * 1440
    env.run() if config.drain_until_empty else env.run(until=arrival_horizon + 1440)
    frame = pd.DataFrame(model.records)
    if frame.empty:
        raise RuntimeError("Simulation completed without any measured patients")
    completed = len(frame)
    unfinished = max(0, model.arrivals - model.no_shows - completed)
    eligible = max(0, model.arrivals - model.no_shows)
    completion_rate = float(completed / eligible * 100.0) if eligible else 0.0
    system = frame["system_minutes"].to_numpy(dtype=float)
    scheduled_minutes = config.days * config.operating_hours * 60
    outpatient = _patient_type_metrics(frame, "outpatient")
    inpatient = _patient_type_metrics(frame, "inpatient")
    emergency = _patient_type_metrics(frame, "emergency")
    result = SimulationResult(scenario=config.name, replication=replication, arrivals=model.arrivals, completed=completed, no_shows=model.no_shows, unfinished=unfinished, completion_rate_pct=completion_rate, mean_wait_minutes=float(frame["wait_minutes"].mean()), mean_reception_wait_minutes=float(frame["reception_wait_minutes"].mean()), mean_preparation_wait_minutes=float(frame["preparation_wait_minutes"].mean()), mean_mri_wait_minutes=float(frame["mri_wait_minutes"].mean()), mean_reporting_wait_minutes=float(frame["reporting_wait_minutes"].mean()), mean_system_minutes=float(system.mean()), p90_system_minutes=float(np.quantile(system, 0.90)), completed_within_120_pct=float((system <= 120).mean() * 100), throughput_per_day=float(completed / config.days), clerk_utilisation_pct=_utilisation_pct(model.busy_minutes["clerks"], config.clerks, scheduled_minutes), radiographer_utilisation_pct=_utilisation_pct(model.busy_minutes["radiographers"], config.radiographers, scheduled_minutes), mri_utilisation_pct=_utilisation_pct(model.busy_minutes["mri"], config.mri_machines, scheduled_minutes), radiologist_utilisation_pct=_utilisation_pct(model.busy_minutes["radiologists"], config.radiologists, scheduled_minutes), outpatient_mean_wait_minutes=outpatient[0], outpatient_mean_system_minutes=outpatient[1], outpatient_completed_within_120_pct=outpatient[2], inpatient_mean_wait_minutes=inpatient[0], inpatient_mean_system_minutes=inpatient[1], inpatient_completed_within_120_pct=inpatient[2], emergency_mean_wait_minutes=emergency[0], emergency_mean_system_minutes=emergency[1], emergency_completed_within_120_pct=emergency[2], mri_failures=model.mri_failures, mri_downtime_minutes=model.mri_downtime_minutes)
    return result, frame


def run_replications(config: ScenarioConfig, replications: int = 20) -> pd.DataFrame:
    if replications <= 0:
        raise ValueError("replications must be positive")
    return pd.DataFrame(asdict(run_once(config, index)[0]) for index in range(replications))


def summarise(results: pd.DataFrame) -> dict[str, float]:
    """Summarise replications with means, variability and normal 95% confidence intervals."""
    if results.empty:
        raise ValueError("results must contain at least one replication")
    numeric = [column for column in results.columns if column not in {"scenario", "replication"}]
    summary: dict[str, float] = {}
    n = len(results)
    for metric in numeric:
        values = results[metric].astype(float)
        metric_mean = float(values.mean())
        sd = float(values.std(ddof=1)) if n > 1 else 0.0
        margin = 1.96 * (sd / sqrt(n) if n > 1 else 0.0)
        summary[metric] = metric_mean
        summary[f"{metric}_sd"] = sd
        summary[f"{metric}_ci95_low"] = metric_mean - margin
        summary[f"{metric}_ci95_high"] = metric_mean + margin
    return summary
