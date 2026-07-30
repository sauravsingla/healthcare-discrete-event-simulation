"""Backward-compatible public import surface for the corrected advanced engine."""

from . import advanced_engine as _engine


class AdvancedMRIModel(_engine.AdvancedMRIModel):
    """Advanced model with state snapshots taken after capacity reconciliation."""

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
                    "mri_queue": sum(
                        len(machine.resource.queue) for machine in self.machines
                    ),
                    "mri_busy": sum(machine.resource.count for machine in self.machines),
                    "mri_available": sum(
                        machine.available for machine in self.machines
                    ),
                    "clerk_target": self.clerks.target(minute),
                    "clerk_busy": self.clerks.busy,
                    "clerk_tokens": self.clerks.tokens.level,
                    "radiographer_target": self.radiographers.target(minute),
                    "radiographer_busy": self.radiographers.busy,
                    "radiographer_tokens": self.radiographers.tokens.level,
                    "radiologist_target": self.radiologists.target(minute),
                    "radiologist_busy": self.radiologists.busy,
                    "radiologist_tokens": self.radiologists.tokens.level,
                    "machine_states": "|".join(
                        machine.state for machine in self.machines
                    ),
                }
            )
            yield self.env.timeout(self.config.tracking_interval_minutes)


# The engine runner resolves this global at execution time. Rebinding it keeps all
# public entry points on the corrected implementation without duplicating runners.
_engine.AdvancedMRIModel = AdvancedMRIModel  # type: ignore[misc]

AdvancedScenarioConfig = _engine.AdvancedScenarioConfig
AdvancedSimulationResult = _engine.AdvancedSimulationResult
CapacityWindow = _engine.CapacityWindow
DynamicCapacity = _engine.DynamicCapacity
MachineWindow = _engine.MachineWindow
MRIMachine = _engine.MRIMachine
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
