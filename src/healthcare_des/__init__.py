"""Healthcare demand and capacity discrete-event simulation."""

from importlib.metadata import PackageNotFoundError, version

from .advanced_model import (
    AdvancedScenarioConfig,
    AdvancedSimulationResult,
    CapacityWindow,
    MachineWindow,
    run_advanced_once,
    run_advanced_replications,
    summarise_advanced,
)
from .model import ScenarioConfig, SimulationResult, run_replications
from .research_validation import (
    calibrate_parameters,
    confidence_interval,
    equivalence_report,
    fit_distributions,
    fit_hourly_profile,
    save_distribution_plots,
)

__all__ = [
    "ScenarioConfig",
    "SimulationResult",
    "run_replications",
    "AdvancedScenarioConfig",
    "AdvancedSimulationResult",
    "CapacityWindow",
    "MachineWindow",
    "run_advanced_once",
    "run_advanced_replications",
    "summarise_advanced",
    "fit_hourly_profile",
    "confidence_interval",
    "equivalence_report",
    "fit_distributions",
    "save_distribution_plots",
    "calibrate_parameters",
]

try:
    __version__ = version("healthcare-des")
except PackageNotFoundError:  # Source-tree fallback before installation.
    __version__ = "0+unknown"
