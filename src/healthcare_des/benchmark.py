"""Reproducible multi-scenario benchmarking for healthcare capacity models."""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Mapping

import pandas as pd

from .model import ScenarioConfig, run_replications, summarise


DEFAULT_SCENARIOS: dict[str, dict[str, float | int]] = {
    "baseline": {},
    "low-demand": {"daily_demand_multiplier": 0.8},
    "high-demand": {"daily_demand_multiplier": 1.2},
    "high-no-show": {"no_show_rate": 0.15},
    "extra-mri": {"mri_machines_delta": 1},
    "extra-radiographer": {"radiographers_delta": 1},
    "extra-radiologist": {"radiologists_delta": 1},
    "reduced-capacity": {
        "mri_machines_delta": -1,
        "radiographers_delta": -1,
    },
}


def _build_scenario(
    base: ScenarioConfig,
    name: str,
    changes: Mapping[str, float | int],
) -> ScenarioConfig:
    supported = {
        "daily_demand_multiplier",
        "no_show_rate",
        "mri_machines_delta",
        "radiographers_delta",
        "radiologists_delta",
    }
    unknown = sorted(set(changes) - supported)
    if unknown:
        raise ValueError(f"Unsupported benchmark changes: {', '.join(unknown)}")

    multiplier = float(changes.get("daily_demand_multiplier", 1.0))
    if multiplier <= 0:
        raise ValueError("daily_demand_multiplier must be positive")

    config = replace(
        base,
        name=name,
        daily_demand=base.daily_demand * multiplier,
        no_show_rate=float(changes.get("no_show_rate", base.no_show_rate)),
        mri_machines=base.mri_machines + int(changes.get("mri_machines_delta", 0)),
        radiographers=base.radiographers + int(changes.get("radiographers_delta", 0)),
        radiologists=base.radiologists + int(changes.get("radiologists_delta", 0)),
    )
    config.validate()
    return config


def benchmark_scenarios(
    base: ScenarioConfig,
    scenarios: Mapping[str, Mapping[str, float | int]] | None = None,
    replications: int = 20,
) -> pd.DataFrame:
    """Run a common set of scenarios and compare each result with baseline.

    The baseline scenario must be present. Percentage deltas are reported for
    mean waiting time, throughput and SLA completion so trade-offs are visible.
    """
    base.validate()
    if replications <= 0:
        raise ValueError("replications must be positive")

    selected = dict(DEFAULT_SCENARIOS if scenarios is None else scenarios)
    if not selected:
        raise ValueError("scenarios must contain at least one scenario")
    if "baseline" not in selected:
        raise ValueError("scenarios must include a baseline entry")

    rows: list[dict[str, float | int | str]] = []
    for name, changes in selected.items():
        config = _build_scenario(base, name, changes)
        summary = summarise(run_replications(config, replications=replications))
        rows.append({**asdict(config), **summary})

    result = pd.DataFrame(rows)
    baseline = result.loc[result["name"] == "baseline"].iloc[0]

    for metric in (
        "mean_wait_minutes",
        "mean_system_minutes",
        "completed_within_120_pct",
        "throughput_per_day",
    ):
        baseline_value = float(baseline[metric])
        delta_column = f"{metric}_vs_baseline_pct"
        if baseline_value == 0:
            result[delta_column] = 0.0
        else:
            result[delta_column] = (
                (result[metric].astype(float) - baseline_value) / baseline_value * 100.0
            )

    return result.sort_values(
        ["mean_wait_minutes", "throughput_per_day"],
        ascending=[True, False],
    ).reset_index(drop=True)
