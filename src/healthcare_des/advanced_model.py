"""Backward-compatible public import surface for the corrected advanced engine."""

from .advanced_engine import (
    AdvancedMRIModel,
    AdvancedScenarioConfig,
    AdvancedSimulationResult,
    CapacityWindow,
    DynamicCapacity,
    MachineWindow,
    MRIMachine,
    run_advanced_once,
    run_advanced_replications,
    summarise_advanced,
)

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
