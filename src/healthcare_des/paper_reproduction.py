"""Source-backed reproduction contract for Singla (2020).

The values in this module are transcribed from the published article rather than
inferred from current package defaults.  They provide one auditable place for
run-control, patient-mix, staffing, distribution and validation assumptions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from .advanced_model import AdvancedScenarioConfig, CapacityWindow

PAPER_DOI = "10.4236/ojmsi.2020.84007"
PAPER_URL = "https://doi.org/10.4236/ojmsi.2020.84007"


@dataclass(frozen=True)
class PublishedPaperSpecification:
    """Machine-readable assumptions and targets disclosed in the article."""

    simulation_days: int = 30
    warmup_minutes: int = 4320
    replications: int = 46
    random_seed: int = 17
    historical_february_2018_demand: int = 2089
    simulated_demand_low: int = 1828
    simulated_demand_high: int = 1930
    outpatient_share: float = 0.57
    inpatient_share: float = 0.2408
    emergency_share: float = 0.1892
    outpatient_no_show_rate: float = 0.08
    resource_availability: float = 0.90
    reception_queue_capacity: int = 20
    reading_room_queue_capacity: int = 25
    reception_exponential_mean_minutes: float = 8.0
    preparation_triangular_low: float = 4.0
    preparation_triangular_mode: float = 5.0
    preparation_triangular_high: float = 6.0
    report_uniform_low_minutes: float = 6.0
    report_uniform_high_minutes: float = 12.0
    radiographer_morning: int = 4
    radiographer_evening: int = 3
    radiographer_night: int = 2
    clerk_per_shift: int = 1
    consultant_per_shift: int = 1
    outpatient_evening_demand_fraction: float = 0.50
    outpatient_night_demand_fraction: float = 0.25
    reported_mri_queue_before_minutes: float = 17.0
    reported_mri_queue_after_minutes: float = 5.0
    reported_scenario_11_system_time_reduction_minutes: float = 20.0

    @property
    def warmup_days(self) -> int:
        return self.warmup_minutes // 1440

    @property
    def simulated_accuracy_low_pct(self) -> float:
        return 100.0 * self.simulated_demand_low / self.historical_february_2018_demand

    @property
    def simulated_accuracy_high_pct(self) -> float:
        return 100.0 * self.simulated_demand_high / self.historical_february_2018_demand


PUBLISHED_SPEC = PublishedPaperSpecification()

# The article describes these eleven experiment intentions explicitly.  Keeping
# them as labels prevents current implementation choices from being mistaken
# for values printed in the original Simul8 scenario table.
PUBLISHED_SCENARIO_INTENT = {
    "scenario-01": "outpatient arrival profile experiment: 8-hour access",
    "scenario-02": "outpatient arrival profile experiment: 16-hour access",
    "scenario-03": "outpatient arrival profile experiment: 24-hour access",
    "scenario-04": "MRI service-time distribution experiment A",
    "scenario-05": "MRI service-time distribution experiment B",
    "scenario-06": "MRI service-time distribution experiment C",
    "scenario-07": "normal-hours overbooking to offset no-shows",
    "scenario-08": "start/end-of-hour overbooking",
    "scenario-09": "exclusive resources for emergency patients",
    "scenario-10": "exclusive resources for inpatient and emergency patients",
    "scenario-11": "staff capacity changed to match demand by shift",
}


def paper_base_config() -> AdvancedScenarioConfig:
    """Return the closest supported configuration for the published baseline.

    Values are drawn directly from the article.  Distribution families that are
    not configurable in the general engine remain recorded in ``PUBLISHED_SPEC``
    and in the generated manifest, rather than being silently replaced.
    """

    return AdvancedScenarioConfig(
        name="singla-2020-published-baseline",
        days=PUBLISHED_SPEC.simulation_days,
        warmup_days=PUBLISHED_SPEC.warmup_days,
        operating_hours=8,
        daily_demand=float(PUBLISHED_SPEC.historical_february_2018_demand)
        / PUBLISHED_SPEC.simulation_days,
        outpatient_share=PUBLISHED_SPEC.outpatient_share,
        inpatient_share=PUBLISHED_SPEC.inpatient_share,
        emergency_share=PUBLISHED_SPEC.emergency_share,
        no_show_rate=PUBLISHED_SPEC.outpatient_no_show_rate,
        cancellation_rate=0.0,
        appointment_arrival_sd_minutes=0.0,
        reception_mean=PUBLISHED_SPEC.reception_exponential_mean_minutes,
        preparation_mean=PUBLISHED_SPEC.preparation_triangular_mode,
        report_mean=(
            PUBLISHED_SPEC.report_uniform_low_minutes
            + PUBLISHED_SPEC.report_uniform_high_minutes
        )
        / 2,
        clerk_capacity=(
            CapacityWindow(0, 480, PUBLISHED_SPEC.clerk_per_shift),
            CapacityWindow(480, 960, PUBLISHED_SPEC.clerk_per_shift),
            CapacityWindow(960, 1440, PUBLISHED_SPEC.clerk_per_shift),
        ),
        radiographer_capacity=(
            CapacityWindow(0, 480, PUBLISHED_SPEC.radiographer_morning),
            CapacityWindow(480, 960, PUBLISHED_SPEC.radiographer_evening),
            CapacityWindow(960, 1440, PUBLISHED_SPEC.radiographer_night),
        ),
        radiologist_capacity=(
            CapacityWindow(0, 480, PUBLISHED_SPEC.consultant_per_shift),
            CapacityWindow(480, 960, PUBLISHED_SPEC.consultant_per_shift),
            CapacityWindow(960, 1440, PUBLISHED_SPEC.consultant_per_shift),
        ),
        seed=PUBLISHED_SPEC.random_seed,
        termination_policy="horizon",
    )


def published_targets() -> pd.DataFrame:
    """Return numerical claims suitable for automated reproduction reports."""

    return pd.DataFrame(
        [
            {
                "target": "historical_february_2018_demand",
                "expected": PUBLISHED_SPEC.historical_february_2018_demand,
                "lower": PUBLISHED_SPEC.historical_february_2018_demand,
                "upper": PUBLISHED_SPEC.historical_february_2018_demand,
                "unit": "scans",
            },
            {
                "target": "simulated_monthly_demand",
                "expected": (
                    PUBLISHED_SPEC.simulated_demand_low + PUBLISHED_SPEC.simulated_demand_high
                )
                / 2,
                "lower": PUBLISHED_SPEC.simulated_demand_low,
                "upper": PUBLISHED_SPEC.simulated_demand_high,
                "unit": "scans",
            },
            {
                "target": "mri_waiting_room_queue_after",
                "expected": PUBLISHED_SPEC.reported_mri_queue_after_minutes,
                "lower": PUBLISHED_SPEC.reported_mri_queue_after_minutes,
                "upper": PUBLISHED_SPEC.reported_mri_queue_after_minutes,
                "unit": "minutes",
            },
            {
                "target": "scenario_11_system_time_reduction",
                "expected": PUBLISHED_SPEC.reported_scenario_11_system_time_reduction_minutes,
                "lower": PUBLISHED_SPEC.reported_scenario_11_system_time_reduction_minutes,
                "upper": PUBLISHED_SPEC.reported_scenario_11_system_time_reduction_minutes,
                "unit": "minutes",
            },
        ]
    )


def reproduction_manifest() -> dict[str, Any]:
    """Return a serialisable, source-backed reproduction manifest."""

    return {
        "citation": {
            "doi": PAPER_DOI,
            "url": PAPER_URL,
            "title": "Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation",
            "year": 2020,
        },
        "published_specification": asdict(PUBLISHED_SPEC),
        "derived_values": {
            "warmup_days": PUBLISHED_SPEC.warmup_days,
            "simulated_accuracy_low_pct": PUBLISHED_SPEC.simulated_accuracy_low_pct,
            "simulated_accuracy_high_pct": PUBLISHED_SPEC.simulated_accuracy_high_pct,
        },
        "scenario_intent": PUBLISHED_SCENARIO_INTENT,
        "supported_baseline_config": asdict(paper_base_config()),
        "distribution_fidelity": {
            "patient_interarrival": "published Pearson V; retained as authoritative metadata",
            "preparation": "published triangular(4,5,6); engine baseline uses mean parameter 5",
            "report_interpretation": "published uniform(6,12); engine baseline uses mean parameter 9",
            "mri_service": "published normal; directly supported",
            "reception": "published exponential mean 8; directly supported",
        },
    }


def validate_reproduction_manifest(manifest: dict[str, Any] | None = None) -> None:
    """Fail if a required published input or target is absent."""

    selected = reproduction_manifest() if manifest is None else manifest
    required_top_level = {
        "citation",
        "published_specification",
        "derived_values",
        "scenario_intent",
        "supported_baseline_config",
        "distribution_fidelity",
    }
    missing = required_top_level - set(selected)
    if missing:
        raise ValueError(f"Missing reproduction manifest sections: {', '.join(sorted(missing))}")
    if len(selected["scenario_intent"]) != 11:
        raise ValueError("The reproduction manifest must contain all eleven paper scenarios")
    if PUBLISHED_SPEC.replications != 46 or PUBLISHED_SPEC.random_seed != 17:
        raise ValueError("Published run-control assumptions were altered")
    if not np_isclose_patient_mix():
        raise ValueError("Published patient shares must sum to one")


def np_isclose_patient_mix() -> bool:
    total = (
        PUBLISHED_SPEC.outpatient_share
        + PUBLISHED_SPEC.inpatient_share
        + PUBLISHED_SPEC.emergency_share
    )
    return abs(total - 1.0) <= 1e-9


__all__ = [
    "PAPER_DOI",
    "PAPER_URL",
    "PUBLISHED_SCENARIO_INTENT",
    "PUBLISHED_SPEC",
    "PublishedPaperSpecification",
    "paper_base_config",
    "published_targets",
    "reproduction_manifest",
    "validate_reproduction_manifest",
]
