"""Source-backed reproduction contract for Singla (2020).

Published values are transcribed explicitly. Missing scenario-level numbers remain
marked unavailable rather than being inferred or invented.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from .advanced_model import AdvancedScenarioConfig, CapacityWindow

PAPER_DOI = "10.4236/ojmsi.2020.84007"
PAPER_URL = "https://doi.org/10.4236/ojmsi.2020.84007"
REPRODUCTION_CLAIM = "Source-backed reproduction contract with partial numerical reproduction"


@dataclass(frozen=True)
class PublishedPaperSpecification:
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
    mri_normal_mean_minutes: float = 26.46
    mri_normal_sd_minutes: float = 8.0
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
    """Return the closest supported baseline using every directly supported value."""
    return AdvancedScenarioConfig(
        name="singla-2020-published-baseline",
        days=PUBLISHED_SPEC.simulation_days,
        warmup_days=PUBLISHED_SPEC.warmup_days,
        operating_hours=8,
        daily_demand=PUBLISHED_SPEC.historical_february_2018_demand
        / PUBLISHED_SPEC.simulation_days,
        outpatient_share=PUBLISHED_SPEC.outpatient_share,
        inpatient_share=PUBLISHED_SPEC.inpatient_share,
        emergency_share=PUBLISHED_SPEC.emergency_share,
        no_show_rate=PUBLISHED_SPEC.outpatient_no_show_rate,
        cancellation_rate=0.0,
        appointment_arrival_sd_minutes=0.0,
        reception_mean=PUBLISHED_SPEC.reception_exponential_mean_minutes,
        preparation_mean=PUBLISHED_SPEC.preparation_triangular_mode,
        scan_mean=PUBLISHED_SPEC.mri_normal_mean_minutes,
        scan_sd=PUBLISHED_SPEC.mri_normal_sd_minutes,
        report_mean=(
            PUBLISHED_SPEC.report_uniform_low_minutes + PUBLISHED_SPEC.report_uniform_high_minutes
        )
        / 2,
        clerk_capacity=tuple(
            CapacityWindow(start, start + 480, PUBLISHED_SPEC.clerk_per_shift)
            for start in (0, 480, 960)
        ),
        radiographer_capacity=(
            CapacityWindow(0, 480, PUBLISHED_SPEC.radiographer_morning),
            CapacityWindow(480, 960, PUBLISHED_SPEC.radiographer_evening),
            CapacityWindow(960, 1440, PUBLISHED_SPEC.radiographer_night),
        ),
        radiologist_capacity=tuple(
            CapacityWindow(start, start + 480, PUBLISHED_SPEC.consultant_per_shift)
            for start in (0, 480, 960)
        ),
        seed=PUBLISHED_SPEC.random_seed,
        termination_policy="horizon",
    )


def sample_published_service_times(rng: np.random.Generator, size: int) -> pd.DataFrame:
    """Sample the paper's explicitly parameterised service distributions exactly."""
    if size <= 0:
        raise ValueError("size must be positive")
    return pd.DataFrame(
        {
            "reception_minutes": rng.exponential(
                PUBLISHED_SPEC.reception_exponential_mean_minutes, size
            ),
            "preparation_minutes": rng.triangular(
                PUBLISHED_SPEC.preparation_triangular_low,
                PUBLISHED_SPEC.preparation_triangular_mode,
                PUBLISHED_SPEC.preparation_triangular_high,
                size,
            ),
            "mri_minutes": np.maximum(
                0.0,
                rng.normal(
                    PUBLISHED_SPEC.mri_normal_mean_minutes,
                    PUBLISHED_SPEC.mri_normal_sd_minutes,
                    size,
                ),
            ),
            "report_minutes": rng.uniform(
                PUBLISHED_SPEC.report_uniform_low_minutes,
                PUBLISHED_SPEC.report_uniform_high_minutes,
                size,
            ),
        }
    )


def published_targets() -> pd.DataFrame:
    """Return every numerical result currently transcribed from the paper."""
    rows = [
        ("baseline", "historical_february_2018_demand", 2089, 2089, 2089, "scans"),
        ("baseline", "simulated_monthly_demand", 1879, 1828, 1930, "scans"),
        ("baseline", "mri_waiting_room_queue_before", 17, 17, 17, "minutes"),
        ("improved", "mri_waiting_room_queue_after", 5, 5, 5, "minutes"),
        ("scenario-11", "system_time_reduction", 20, 20, 20, "minutes"),
    ]
    return pd.DataFrame(
        rows,
        columns=["scenario", "target", "expected", "lower", "upper", "unit"],
    )


def scenario_results_catalog() -> pd.DataFrame:
    """Index all eleven scenarios and disclose numerical-result availability."""
    rows = []
    for scenario, intent in PUBLISHED_SCENARIO_INTENT.items():
        available = scenario == "scenario-11"
        rows.append(
            {
                "scenario": scenario,
                "intent": intent,
                "published_numeric_result_available": available,
                "published_metric": "system_time_reduction" if available else None,
                "published_value": 20.0 if available else None,
                "status": "transcribed"
                if available
                else "not numerically disclosed in current evidence",
            }
        )
    return pd.DataFrame(rows)


def paper_table_figure_index() -> pd.DataFrame:
    """Map paper evidence concepts to repository fields and outputs."""
    return pd.DataFrame(
        [
            ("run controls", "published_specification", "reproduction_manifest.json"),
            (
                "patient mix",
                "published_specification.*_share",
                "reproduction_manifest.json",
            ),
            (
                "service distributions",
                "distribution_fidelity",
                "service_distribution_samples.csv",
            ),
            (
                "monthly demand validation",
                "published_targets: simulated_monthly_demand",
                "published_targets.csv",
            ),
            (
                "MRI queue before/after",
                "published_targets: mri_waiting_room_queue_*",
                "published_targets.csv",
            ),
            (
                "scenario 11",
                "published_targets: system_time_reduction",
                "comparison_template.csv",
            ),
            ("all 11 scenarios", "scenario_results_catalog", "scenario_catalog.csv"),
        ],
        columns=["paper_evidence", "repository_mapping", "reproduction_output"],
    )


def operational_constraint_status() -> pd.DataFrame:
    """Show which published constraints are applied directly or retained as evidence."""
    return pd.DataFrame(
        [
            (
                "90% resource availability",
                0.90,
                "metadata; no generic availability field in engine",
            ),
            (
                "reception queue capacity",
                20,
                "metadata; engine currently models patience rather than hard queue caps",
            ),
            (
                "reading-room queue capacity",
                25,
                "metadata; engine currently models patience rather than hard queue caps",
            ),
            ("radiographer shift capacity", "4/3/2", "applied directly"),
            ("clerk shift capacity", "1/1/1", "applied directly"),
            ("consultant shift capacity", "1/1/1", "applied directly"),
        ],
        columns=["constraint", "published_value", "application_status"],
    )


def comparison_template() -> pd.DataFrame:
    """Create an auditable paper-value versus reproduced-value template."""
    rows = []
    for row in published_targets().itertuples(index=False):
        rows.append(
            {
                "scenario": row.scenario,
                "metric": row.target,
                "paper_value": row.expected,
                "paper_lower": row.lower,
                "paper_upper": row.upper,
                "reproduced_value": np.nan,
                "absolute_difference": np.nan,
                "tolerance_pct": 10.0,
                "passed": pd.NA,
                "status": "awaiting reproduced metric",
            }
        )
    for scenario in PUBLISHED_SCENARIO_INTENT:
        if scenario != "scenario-11":
            rows.append(
                {
                    "scenario": scenario,
                    "metric": "not numerically disclosed",
                    "paper_value": np.nan,
                    "paper_lower": np.nan,
                    "paper_upper": np.nan,
                    "reproduced_value": np.nan,
                    "absolute_difference": np.nan,
                    "tolerance_pct": np.nan,
                    "passed": pd.NA,
                    "status": "comparison unavailable without a published numerical target",
                }
            )
    return pd.DataFrame(rows)


def compare_reproduced_results(
    reproduced: pd.DataFrame, tolerance_pct: float = 10.0
) -> pd.DataFrame:
    """Compare supplied reproduced metrics with every available paper target."""
    required = {"scenario", "metric", "reproduced_value"}
    missing = required - set(reproduced.columns)
    if missing:
        raise ValueError(f"Missing reproduced columns: {', '.join(sorted(missing))}")
    targets = published_targets().rename(
        columns={"target": "metric", "expected": "paper_value"}
    )
    merged = targets.merge(reproduced, on=["scenario", "metric"], how="left")
    merged["absolute_difference"] = (
        merged["reproduced_value"] - merged["paper_value"]
    ).abs()
    denominator = merged["paper_value"].abs().replace(0, 1)
    merged["error_pct"] = merged["absolute_difference"] / denominator * 100
    merged["tolerance_pct"] = tolerance_pct
    merged["passed"] = merged["reproduced_value"].notna() & (
        merged["error_pct"] <= tolerance_pct
    )
    return merged


def reproduction_manifest() -> dict[str, Any]:
    return {
        "citation": {
            "doi": PAPER_DOI,
            "url": PAPER_URL,
            "title": "Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation",
            "year": 2020,
        },
        "claim": REPRODUCTION_CLAIM,
        "published_specification": asdict(PUBLISHED_SPEC),
        "derived_values": {
            "warmup_days": PUBLISHED_SPEC.warmup_days,
            "simulated_accuracy_low_pct": PUBLISHED_SPEC.simulated_accuracy_low_pct,
            "simulated_accuracy_high_pct": PUBLISHED_SPEC.simulated_accuracy_high_pct,
        },
        "scenario_intent": PUBLISHED_SCENARIO_INTENT,
        "supported_baseline_config": asdict(paper_base_config()),
        "distribution_fidelity": {
            "patient_interarrival": (
                "Pearson V family disclosed; shape/scale unavailable in current evidence, "
                "so not fabricated"
            ),
            "preparation": "triangular(4,5,6) implemented exactly in paper-specific sampler",
            "report_interpretation": "uniform(6,12) implemented exactly in paper-specific sampler",
            "mri_service": "normal(26.46,8.0) implemented in paper-specific sampler",
            "reception": "exponential mean 8 implemented exactly in paper-specific sampler",
        },
        "limitations": [
            "Original Simul8 model, event calendar and random streams are unavailable",
            "Scenario-level numerical targets are only compared where published evidence is available",
            "Hard queue capacities and generic 90% availability are retained as explicit evidence until supported natively",
        ],
    }


def validate_reproduction_manifest(manifest: dict[str, Any] | None = None) -> None:
    selected = reproduction_manifest() if manifest is None else manifest
    required = {
        "citation",
        "claim",
        "published_specification",
        "derived_values",
        "scenario_intent",
        "supported_baseline_config",
        "distribution_fidelity",
        "limitations",
    }
    missing = required - set(selected)
    if missing:
        raise ValueError(f"Missing reproduction manifest sections: {', '.join(sorted(missing))}")
    if len(selected["scenario_intent"]) != 11:
        raise ValueError("The reproduction manifest must contain all eleven paper scenarios")
    if PUBLISHED_SPEC.replications != 46 or PUBLISHED_SPEC.random_seed != 17:
        raise ValueError("Published run-control assumptions were altered")
    if (
        abs(
            PUBLISHED_SPEC.outpatient_share
            + PUBLISHED_SPEC.inpatient_share
            + PUBLISHED_SPEC.emergency_share
            - 1.0
        )
        > 1e-9
    ):
        raise ValueError("Published patient shares must sum to one")


__all__ = [
    "PAPER_DOI",
    "PAPER_URL",
    "PUBLISHED_SCENARIO_INTENT",
    "PUBLISHED_SPEC",
    "REPRODUCTION_CLAIM",
    "PublishedPaperSpecification",
    "compare_reproduced_results",
    "comparison_template",
    "operational_constraint_status",
    "paper_base_config",
    "paper_table_figure_index",
    "published_targets",
    "reproduction_manifest",
    "sample_published_service_times",
    "scenario_results_catalog",
    "validate_reproduction_manifest",
]
