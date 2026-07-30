"""Backward-compatible public import surface for the corrected advanced engine."""

import simpy

from . import advanced_engine as _engine


class MRIMachine(_engine.MRIMachine):
    """MRI machine with interrupt-safe scan and repair handling."""

    def _failure_clock(self, mtbf: float):
        while True:
            yield self.env.timeout(float(self.rng.exponential(mtbf)))
            if self.blockers.intersection({"maintenance", "failure"}):
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
        """Run a scan while containing repeated failure interrupts."""
        remaining = duration
        segment_started: float | None = None
        self.active_scan = self.env.active_process
        try:
            while remaining > 0:
                try:
                    while self.blockers:
                        segment_started = None
                        yield self.env.timeout(1)
                    self.state = "BUSY"
                    segment_started = self.env.now
                    yield self.env.timeout(remaining)
                    remaining = 0
                except simpy.Interrupt as interruption:
                    cause = interruption.cause
                    if not isinstance(cause, tuple) or not cause or cause[0] != "machine_failure":
                        raise
                    if segment_started is not None:
                        elapsed = self.env.now - segment_started
                        remaining = (
                            duration
                            if self.config.restart_scan_after_failure
                            else max(0.0, remaining - elapsed)
                        )
                    segment_started = None
        finally:
            self.active_scan = None
            self.state = "AVAILABLE" if not self.blockers else self.state


class AdvancedMRIModel(_engine.AdvancedMRIModel):
    """Advanced model with corrected capacity tracking and machine failures."""

    def _track_state(self):
        while True:
            yield self.env.process(self.clerks.rebalance())
            yield self.env.process(self.radiographers.rebalance())
            yield self.env.process(self.radiologists.rebalance())
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


# The engine runners resolve these globals at execution time. Rebinding them keeps
# all public entry points on the corrected implementations without duplicating runners.
_engine.MRIMachine = MRIMachine  # type: ignore[misc]
_engine.AdvancedMRIModel = AdvancedMRIModel  # type: ignore[misc]

AdvancedScenarioConfig = _engine.AdvancedScenarioConfig
AdvancedSimulationResult = _engine.AdvancedSimulationResult
CapacityWindow = _engine.CapacityWindow
DynamicCapacity = _engine.DynamicCapacity
MachineWindow = _engine.MachineWindow
run_advanced_once = _engine.run_advanced_once
run_advanced_replications = _engine.run_advanced_replications
summarise_advanced = _engine.summarise_advanced

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
