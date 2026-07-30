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
    "AdvancedScenarioConfig",
    "AdvancedSimulationResult",
    "CapacityWindow",
    "MachineWindow",
    "ScenarioConfig",
    "SimulationResult",
    "calibrate_parameters",
    "confidence_interval",
    "equivalence_report",
    "fit_distributions",
    "fit_hourly_profile",
    "run_advanced_once",
    "run_advanced_replications",
    "run_replications",
    "save_distribution_plots",
    "summarise_advanced",
]

try:
    __version__ = version("healthcare-des")
except PackageNotFoundError:  # Source-tree fallback before installation.
    __version__ = "0+unknown"
